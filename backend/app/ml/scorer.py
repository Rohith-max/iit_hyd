"""Credit scoring engine with PD/LGD/EAD, credit grading, and RARR."""
import numpy as np
import pickle
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent.parent / "models"


@dataclass
class MLScoreResult:
    pd_score: float
    lgd_score: float
    ead: float
    expected_loss: float
    credit_grade: str
    credit_score: int
    recommended_limit: float
    recommended_rate: float
    risk_premium: float
    decision: str
    confidence: float

    def to_dict(self):
        return asdict(self)


class CreditScorer:
    """Ensemble credit scoring with XGBoost + LightGBM stacking."""

    def __init__(self):
        self.xgb_pd = None
        self.xgb_calibrator = None
        self.lgbm_pd = None
        self.meta_learner = None
        self.limit_model = None
        self.feature_names = None
        self._load_models()

    def _load_models(self):
        try:
            for name in ["xgb_pd", "xgb_calibrator", "lgbm_pd", "meta_learner", "limit_model", "feature_names"]:
                path = MODELS_DIR / f"{name}.pkl"
                if path.exists():
                    with open(path, "rb") as f:
                        setattr(self, name, pickle.load(f))
            if self.xgb_pd is not None:
                logger.info("ML models loaded successfully")
            else:
                logger.warning("ML models not found — run train_model first")
        except Exception as e:
            logger.error(f"Error loading models: {e}")

    def ensure_models(self):
        if self.xgb_pd is None:
            from app.ml.train_model import ModelTrainer
            trainer = ModelTrainer()
            trainer.train()
            self._load_models()

    def score(self, features: dict, requested_amount: float = 0) -> MLScoreResult:
        """Score a credit application and return full decision."""
        self.ensure_models()

        # Prepare feature vector
        X = np.array([[features.get(f, 0.0) for f in self.feature_names]])

        # Ensemble PD prediction
        xgb_raw = self.xgb_pd.predict_proba(X)[:, 1][0]
        xgb_prob = float(self.xgb_calibrator.predict([xgb_raw])[0]) if self.xgb_calibrator else xgb_raw
        lgbm_prob = self.lgbm_pd.predict_proba(X)[:, 1][0]
        meta_features = np.array([[xgb_prob, lgbm_prob]])
        pd_score = float(self.meta_learner.predict_proba(meta_features)[:, 1][0])

        # LGD estimation (simplified Basel II approach)
        collateral_score = features.get("collateral_type_score", 0)
        coverage = features.get("collateral_coverage_ratio", 1.0)
        lgd_score = self._estimate_lgd(collateral_score, coverage)

        # EAD
        ead = requested_amount if requested_amount > 0 else features.get("revenue_latest", 100) * 0.3

        # Expected Loss
        expected_loss = pd_score * lgd_score * ead

        # Credit grade & score
        credit_grade = self.assign_credit_grade(pd_score)
        credit_score = self._pd_to_score(pd_score)

        # RARR
        risk_premium = self.compute_rarr(pd_score, lgd_score, ead)
        recommended_rate = 0.085 + risk_premium  # MCLR 8.5% + premium

        # Credit limit optimization
        cash_flows = features.get("ebitda_latest", 0) * 0.7  # Approximate annual FCF
        collateral_value = ead * coverage
        recommended_limit = self.optimize_credit_limit(cash_flows, collateral_value, requested_amount)

        # Decision
        confidence = 1.0 - pd_score
        if pd_score < 0.05:
            decision = "APPROVE"
        elif pd_score < 0.15:
            decision = "CONDITIONAL"
        else:
            decision = "DECLINE"

        return MLScoreResult(
            pd_score=round(pd_score, 4),
            lgd_score=round(lgd_score, 4),
            ead=round(ead, 2),
            expected_loss=round(expected_loss, 2),
            credit_grade=credit_grade,
            credit_score=credit_score,
            recommended_limit=round(recommended_limit, 2),
            recommended_rate=round(recommended_rate, 4),
            risk_premium=round(risk_premium, 4),
            decision=decision,
            confidence=round(confidence, 3),
        )

    def compute_rarr(self, pd: float, lgd: float, ead: float) -> float:
        """Risk-Adjusted Rate of Return premium."""
        el = pd * lgd * ead
        capital_charge = 0.08
        operational_cost = 0.015
        risk_premium = (el / max(ead * (1 - lgd), 1)) + capital_charge + operational_cost
        return min(risk_premium, 0.15)  # Cap at 15%

    def optimize_credit_limit(
        self, annual_cash_flows: float, collateral_value: float, requested_amount: float
    ) -> float:
        """Optimize credit limit based on cash flows, collateral, and request."""
        cf_based_limit = annual_cash_flows * 4  # 4x annual cash flow
        collateral_based_limit = collateral_value * 0.75
        optimal = min(
            requested_amount if requested_amount > 0 else float("inf"),
            max(cf_based_limit, 0),
            max(collateral_based_limit, 0) if collateral_value > 0 else float("inf"),
        )
        if optimal == float("inf"):
            optimal = requested_amount if requested_amount > 0 else annual_cash_flows * 3
        return max(optimal, 0)

    @staticmethod
    def assign_credit_grade(pd: float) -> str:
        """Map PD to credit grade per Basel II standards."""
        if pd < 0.001: return "AAA"
        if pd < 0.003: return "AA"
        if pd < 0.007: return "A"
        if pd < 0.02: return "BBB"
        if pd < 0.05: return "BB"
        if pd < 0.10: return "B"
        if pd < 0.20: return "CCC"
        return "D"

    @staticmethod
    def _pd_to_score(pd: float) -> int:
        """Convert PD to 300-900 credit score."""
        return max(300, min(900, 900 - int(600 * (pd ** 0.25))))

    @staticmethod
    def _estimate_lgd(collateral_score: float, coverage: float) -> float:
        """Estimate Loss Given Default based on collateral."""
        base_lgd = 0.45  # Basel II unsecured
        if collateral_score >= 5:
            base_lgd = 0.25
        elif collateral_score >= 4:
            base_lgd = 0.30
        elif collateral_score >= 3:
            base_lgd = 0.35
        # Adjust for coverage
        if coverage > 1.5:
            base_lgd *= 0.7
        elif coverage > 1.0:
            base_lgd *= 0.85
        return min(base_lgd, 0.9)
