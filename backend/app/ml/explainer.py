"""SHAP explainability for credit scoring models."""
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent.parent / "models"

FEATURE_DISPLAY_NAMES = {
    "dscr": "Debt Service Coverage Ratio",
    "altman_z_score": "Altman Z-Score",
    "cibil_score": "CIBIL Score",
    "debt_equity_ratio": "Debt-to-Equity Ratio",
    "current_ratio": "Current Ratio",
    "ebitda_margin": "EBITDA Margin",
    "pat_margin": "PAT Margin",
    "interest_coverage": "Interest Coverage",
    "revenue_cagr_5y": "5-Year Revenue CAGR",
    "net_debt_to_ebitda": "Net Debt / EBITDA",
    "promoter_pledge_pct": "Promoter Pledge %",
    "news_sentiment_score": "News Sentiment",
    "regulatory_action_flag": "Regulatory Action Flag",
    "piotroski_f_score": "Piotroski F-Score",
    "beneish_m_score": "Beneish M-Score",
    "ltv_ratio": "Loan-to-Value Ratio",
    "dpd_90_count": "90+ DPD Count",
    "collateral_coverage_ratio": "Collateral Coverage",
    "cash_conversion_cycle": "Cash Conversion Cycle",
    "roce": "Return on Capital Employed",
}


class SHAPExplainer:
    """SHAP-based model explainability for credit decisions."""

    def __init__(self):
        self.xgb_model = None
        self.feature_names = None
        self._load()

    def _load(self):
        try:
            xgb_path = MODELS_DIR / "xgb_pd.pkl"
            fn_path = MODELS_DIR / "feature_names.pkl"
            if xgb_path.exists():
                with open(xgb_path, "rb") as f:
                    self.xgb_model = pickle.load(f)
            if fn_path.exists():
                with open(fn_path, "rb") as f:
                    self.feature_names = pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading models for SHAP: {e}")

    def explain(self, features: dict) -> dict:
        """Generate SHAP explanation for a single prediction."""
        try:
            import shap
        except ImportError:
            return self._fallback_explain(features)

        if self.xgb_model is None or self.feature_names is None:
            return self._fallback_explain(features)

        X = np.array([[features.get(f, 0.0) for f in self.feature_names]])

        try:
            # Try TreeExplainer on the base estimator if calibrated
            base_model = self.xgb_model
            if hasattr(base_model, "estimator"):
                base_model = base_model.estimator
            if hasattr(base_model, "calibrated_classifiers_"):
                base_model = base_model.calibrated_classifiers_[0].estimator

            explainer = shap.TreeExplainer(base_model)
            shap_values = explainer.shap_values(X)

            if isinstance(shap_values, list):
                shap_vals = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            else:
                shap_vals = shap_values[0]

            waterfall_data = self._build_waterfall(shap_vals, features)
            nl_summary = self.generate_nl_summary(waterfall_data[:5])
            radar_scores = self.get_risk_radar_scores(features)

            return {
                "waterfall_data": waterfall_data,
                "natural_language_summary": nl_summary,
                "risk_radar": radar_scores,
                "base_value": float(explainer.expected_value[1]) if isinstance(explainer.expected_value, np.ndarray) else float(explainer.expected_value),
            }
        except Exception as e:
            logger.warning(f"SHAP TreeExplainer failed, using fallback: {e}")
            return self._fallback_explain(features)

    def _fallback_explain(self, features: dict) -> dict:
        """Heuristic-based explanation when SHAP isn't available."""
        important_features = [
            ("dscr", 0.15, True), ("altman_z_score", 0.12, True),
            ("cibil_score", 0.10, True), ("debt_equity_ratio", -0.10, False),
            ("current_ratio", 0.08, True), ("ebitda_margin", 0.08, True),
            ("interest_coverage", 0.07, True), ("net_debt_to_ebitda", -0.07, False),
            ("promoter_pledge_pct", -0.06, False), ("news_sentiment_score", 0.06, True),
            ("regulatory_action_flag", -0.05, False), ("piotroski_f_score", 0.05, True),
            ("ltv_ratio", -0.04, False), ("dpd_90_count", -0.04, False),
            ("collateral_coverage_ratio", 0.04, True),
        ]

        waterfall_data = []
        for feat_name, base_impact, positive_is_good in important_features:
            val = features.get(feat_name, 0)
            # Estimate impact direction based on feature value
            if positive_is_good:
                impact = base_impact * (1 if val > 0 else -1) * min(abs(val) / 5, 2)
            else:
                impact = base_impact * (-1 if val > 0 else 1) * min(abs(val) / 5, 2)

            waterfall_data.append({
                "feature": feat_name,
                "display_name": FEATURE_DISPLAY_NAMES.get(feat_name, feat_name),
                "value": round(float(val), 4),
                "shap_value": round(float(impact), 4),
                "direction": "positive" if impact > 0 else "negative",
            })

        waterfall_data.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        nl_summary = self.generate_nl_summary(waterfall_data[:5])
        radar_scores = self.get_risk_radar_scores(features)

        return {
            "waterfall_data": waterfall_data[:15],
            "natural_language_summary": nl_summary,
            "risk_radar": radar_scores,
            "base_value": 0.08,
        }

    def _build_waterfall(self, shap_vals: np.ndarray, features: dict) -> list:
        """Build waterfall chart data from SHAP values."""
        items = []
        for i, fname in enumerate(self.feature_names):
            items.append({
                "feature": fname,
                "display_name": FEATURE_DISPLAY_NAMES.get(fname, fname),
                "value": round(float(features.get(fname, 0)), 4),
                "shap_value": round(float(shap_vals[i]), 4),
                "direction": "positive" if shap_vals[i] > 0 else "negative",
            })
        items.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return items[:15]

    @staticmethod
    def generate_nl_summary(top_features: list) -> str:
        """Generate natural language summary from top SHAP features."""
        positive = [f for f in top_features if f["direction"] == "positive"]
        negative = [f for f in top_features if f["direction"] == "negative"]

        parts = []
        if positive:
            strengths = ", ".join(
                f"{f['display_name']} of {f['value']:.2f} (+{abs(f['shap_value']):.2f} impact)"
                for f in positive[:3]
            )
            parts.append(f"Key strengths: {strengths}.")

        if negative:
            weaknesses = ", ".join(
                f"{f['display_name']} of {f['value']:.2f} (-{abs(f['shap_value']):.2f} impact)"
                for f in negative[:3]
            )
            parts.append(f"Risk factors: {weaknesses}.")

        return " ".join(parts) if parts else "Analysis complete. No significant risk factors identified."

    @staticmethod
    def get_risk_radar_scores(features: dict) -> dict:
        """Compute 6-axis risk radar scores (0-10 scale, higher=better)."""
        # Financial Risk
        dscr = features.get("dscr", 1.5)
        cr = features.get("current_ratio", 1.5)
        de = features.get("debt_equity_ratio", 1.5)
        financial = min(10, max(0, (dscr / 0.3) + (cr / 0.5) - (de / 1.0)))

        # Business Risk
        yrs = features.get("years_in_operation", 10)
        ind_risk = features.get("industry_risk_score", 5)
        business = min(10, max(0, (yrs / 5) + ind_risk / 2))

        # Management Risk
        mgmt = features.get("management_quality_score", 5)
        pledge = features.get("promoter_pledge_pct", 0)
        management = min(10, max(0, mgmt - pledge / 20))

        # Industry Risk
        npl = features.get("industry_npl_rate", 0.05)
        growth = features.get("industry_growth_rate", 0.07)
        industry = min(10, max(0, 8 - npl * 40 + growth * 20))

        # Credit Bureau
        cibil = features.get("cibil_score", 700)
        dpd90 = features.get("dpd_90_count", 0)
        bureau = min(10, max(0, (cibil - 300) / 60 - dpd90))

        # Collateral
        cov = features.get("collateral_coverage_ratio", 1.0)
        col_type = features.get("collateral_type_score", 3)
        collateral = min(10, max(0, cov * 3 + col_type))

        return {
            "financial": round(financial, 1),
            "business": round(business, 1),
            "management": round(management, 1),
            "industry": round(industry, 1),
            "bureau": round(bureau, 1),
            "collateral": round(collateral, 1),
        }
