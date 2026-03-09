"""Synthetic data generation and model training pipeline."""
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import pickle
import logging

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, brier_score_loss
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier
from imblearn.over_sampling import SMOTE

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
DATA_DIR = Path(__file__).parent.parent.parent / "data"

FEATURE_NAMES = [
    "revenue_latest", "ebitda_latest", "pat_latest",
    "revenue_cagr_5y", "ebitda_cagr_5y", "pat_cagr_5y",
    "revenue_yoy", "ebitda_yoy", "pat_yoy",
    "revenue_trend_slope", "ebitda_trend_slope",
    "current_ratio", "debt_equity_ratio", "dscr", "interest_coverage",
    "gross_margin", "ebitda_margin", "pat_margin",
    "roce", "roe", "asset_turnover",
    "dscr_3y_avg", "debtor_days", "creditor_days", "inventory_days",
    "cash_conversion_cycle", "net_debt_to_ebitda",
    "altman_z_score", "piotroski_f_score", "beneish_m_score",
    "fixed_charge_coverage",
    "industry_risk_score", "years_in_operation", "management_quality_score",
    "customer_concentration_hhi", "geographic_diversification",
    "export_revenue_pct", "related_party_txn_ratio",
    "auditor_quality_score", "qualified_audit_flag",
    "promoter_holding_pct", "promoter_pledge_pct",
    "board_independence_ratio", "company_age_log", "is_listed", "group_strength_score",
    "cibil_score", "cibil_score_normalized",
    "existing_loan_utilization", "dpd_0_count", "dpd_30_count",
    "dpd_60_count", "dpd_90_count", "loan_enquiries_6m",
    "unsecured_debt_ratio", "bureau_vintage_years",
    "ltv_ratio", "collateral_type_score", "collateral_coverage_ratio",
    "guarantor_nw_ratio", "sarfaesi_applicable",
    "collateral_value_to_loan", "number_of_collaterals", "collateral_age_years",
    "industry_npl_rate", "gdp_growth_rate", "sector_credit_growth",
    "input_cost_inflation", "industry_leverage_median", "commodity_exposure_score",
    "regulatory_environment_score", "industry_growth_rate",
    "interest_rate_sensitivity", "fx_exposure_score",
    "news_sentiment_score", "regulatory_action_flag", "litigation_score",
    "mgmt_change_velocity", "social_controversy_score",
    "gst_compliance_rate", "roc_compliance_score",
]


class ModelTrainer:
    """Generates synthetic training data and trains ensemble models."""

    def __init__(self):
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def generate_synthetic_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """Generate synthetic credit data with ~8% default rate using Basel II statistics."""
        np.random.seed(42)
        data = {}

        # Financial health features (good companies have high values for positive metrics)
        is_default = np.random.binomial(1, 0.08, n_samples)  # ~8% default rate

        # Features correlated with default risk
        noise = lambda: np.random.normal(0, 0.1, n_samples)

        data["revenue_latest"] = np.abs(stats.lognorm.rvs(s=1.2, scale=np.exp(4), size=n_samples))
        data["ebitda_latest"] = data["revenue_latest"] * np.clip(np.random.normal(0.18, 0.08, n_samples), 0.01, 0.5)
        data["pat_latest"] = data["ebitda_latest"] * np.clip(np.random.normal(0.55, 0.2, n_samples), -0.5, 0.9)

        data["revenue_cagr_5y"] = np.clip(np.random.normal(0.12 - 0.15 * is_default, 0.08), -0.3, 0.5)
        data["ebitda_cagr_5y"] = np.clip(np.random.normal(0.10 - 0.12 * is_default, 0.10), -0.4, 0.6)
        data["pat_cagr_5y"] = np.clip(np.random.normal(0.08 - 0.10 * is_default, 0.12), -0.5, 0.6)

        data["revenue_yoy"] = np.clip(np.random.normal(0.10 - 0.15 * is_default, 0.12), -0.5, 0.8)
        data["ebitda_yoy"] = np.clip(np.random.normal(0.08 - 0.12 * is_default, 0.15), -0.6, 0.8)
        data["pat_yoy"] = np.clip(np.random.normal(0.06 - 0.10 * is_default, 0.18), -0.8, 1.0)

        data["revenue_trend_slope"] = np.random.normal(500 - 800 * is_default, 300)
        data["ebitda_trend_slope"] = np.random.normal(100 - 200 * is_default, 80)

        data["current_ratio"] = np.clip(np.random.normal(1.8 - 0.8 * is_default, 0.5), 0.2, 5.0)
        data["debt_equity_ratio"] = np.clip(np.random.normal(1.2 + 2.0 * is_default, 0.8), 0.01, 8.0)
        data["dscr"] = np.clip(np.random.normal(2.0 - 1.2 * is_default, 0.6), 0.3, 5.0)
        data["interest_coverage"] = np.clip(np.random.normal(4.0 - 3.0 * is_default, 1.5), 0.1, 15.0)
        data["gross_margin"] = np.clip(np.random.normal(0.35 - 0.10 * is_default, 0.12), 0.01, 0.80)
        data["ebitda_margin"] = np.clip(np.random.normal(0.18 - 0.08 * is_default, 0.08), -0.1, 0.5)
        data["pat_margin"] = np.clip(np.random.normal(0.08 - 0.06 * is_default, 0.06), -0.3, 0.3)
        data["roce"] = np.clip(np.random.normal(0.15 - 0.10 * is_default, 0.08), -0.2, 0.5)
        data["roe"] = np.clip(np.random.normal(0.14 - 0.12 * is_default, 0.10), -0.4, 0.6)
        data["asset_turnover"] = np.clip(np.random.normal(1.2 - 0.3 * is_default, 0.4), 0.1, 4.0)
        data["dscr_3y_avg"] = np.clip(data["dscr"] + np.random.normal(0, 0.2, n_samples), 0.3, 5.0)
        data["debtor_days"] = np.clip(np.random.normal(60 + 30 * is_default, 20), 10, 180)
        data["creditor_days"] = np.clip(np.random.normal(45 + 10 * is_default, 15), 10, 120)
        data["inventory_days"] = np.clip(np.random.normal(45 + 20 * is_default, 20), 0, 180)
        data["cash_conversion_cycle"] = data["debtor_days"] + data["inventory_days"] - data["creditor_days"]
        data["net_debt_to_ebitda"] = np.clip(np.random.normal(2.5 + 3.0 * is_default, 1.5), -1, 15)
        data["altman_z_score"] = np.clip(np.random.normal(3.0 - 2.0 * is_default, 1.0), -1, 8)
        data["piotroski_f_score"] = np.clip(np.random.normal(6.0 - 3.0 * is_default, 1.5), 0, 9)
        data["beneish_m_score"] = np.random.normal(-2.5 + 1.5 * is_default, 0.8)
        data["fixed_charge_coverage"] = np.clip(np.random.normal(3.0 - 2.0 * is_default, 1.0), 0.1, 10)

        # Business quality
        data["industry_risk_score"] = np.clip(np.random.normal(5 - 1.5 * is_default, 1.5), 1, 10)
        data["years_in_operation"] = np.clip(np.random.exponential(15, n_samples), 1, 80)
        data["management_quality_score"] = np.clip(np.random.normal(6 - 2 * is_default, 1.5), 1, 10)
        data["customer_concentration_hhi"] = np.clip(np.random.beta(2, 5, n_samples) + 0.1 * is_default, 0, 1)
        data["geographic_diversification"] = np.clip(np.random.normal(5 - 1 * is_default, 2), 1, 10)
        data["export_revenue_pct"] = np.clip(np.random.beta(2, 5, n_samples), 0, 1)
        data["related_party_txn_ratio"] = np.clip(np.random.beta(1.5, 8, n_samples) + 0.05 * is_default, 0, 0.5)
        data["auditor_quality_score"] = np.random.choice([1, 3, 5], n_samples, p=[0.3, 0.4, 0.3])
        data["qualified_audit_flag"] = np.random.binomial(1, 0.05 + 0.15 * is_default)
        data["promoter_holding_pct"] = np.clip(np.random.normal(60, 15, n_samples), 10, 100)
        data["promoter_pledge_pct"] = np.clip(np.random.exponential(10, n_samples) + 20 * is_default, 0, 100)
        data["board_independence_ratio"] = np.clip(np.random.normal(0.35, 0.1, n_samples), 0, 0.75)
        data["company_age_log"] = np.log1p(data["years_in_operation"])
        data["is_listed"] = np.random.binomial(1, 0.3, n_samples).astype(float)
        data["group_strength_score"] = np.clip(np.random.normal(5 - 1 * is_default, 2), 1, 10)

        # Credit bureau
        data["cibil_score"] = np.clip(np.random.normal(750 - 150 * is_default, 50), 300, 900)
        data["cibil_score_normalized"] = (data["cibil_score"] - 300) / 600
        data["existing_loan_utilization"] = np.clip(np.random.beta(3, 4, n_samples) + 0.2 * is_default, 0, 1)
        data["dpd_0_count"] = np.clip(12 - np.random.poisson(2 * is_default, n_samples), 0, 12).astype(float)
        data["dpd_30_count"] = np.clip(np.random.poisson(0.5 + 2 * is_default, n_samples), 0, 12).astype(float)
        data["dpd_60_count"] = np.clip(np.random.poisson(0.1 + 1 * is_default, n_samples), 0, 12).astype(float)
        data["dpd_90_count"] = np.clip(np.random.poisson(0.05 + 0.8 * is_default, n_samples), 0, 12).astype(float)
        data["loan_enquiries_6m"] = np.clip(np.random.poisson(2 + 3 * is_default, n_samples), 0, 20).astype(float)
        data["unsecured_debt_ratio"] = np.clip(np.random.beta(2, 5, n_samples) + 0.1 * is_default, 0, 1)
        data["bureau_vintage_years"] = np.clip(np.random.exponential(8, n_samples), 0, 30)

        # Collateral
        data["ltv_ratio"] = np.clip(np.random.normal(0.6 + 0.15 * is_default, 0.15), 0.1, 1.0)
        data["collateral_type_score"] = np.random.choice([0, 3, 4, 5], n_samples, p=[0.1, 0.2, 0.3, 0.4]).astype(float)
        data["collateral_coverage_ratio"] = np.clip(np.random.normal(1.5 - 0.5 * is_default, 0.4), 0.3, 3.0)
        data["guarantor_nw_ratio"] = np.clip(np.random.exponential(0.5, n_samples), 0, 3)
        data["sarfaesi_applicable"] = np.random.binomial(1, 0.7, n_samples).astype(float)
        data["collateral_value_to_loan"] = np.clip(np.random.normal(1.4 - 0.4 * is_default, 0.3), 0.3, 3.0)
        data["number_of_collaterals"] = np.random.randint(1, 5, n_samples).astype(float)
        data["collateral_age_years"] = np.clip(np.random.exponential(5, n_samples), 0, 30)

        # Macro
        data["industry_npl_rate"] = np.clip(np.random.beta(2, 20, n_samples), 0.01, 0.3)
        data["gdp_growth_rate"] = np.random.normal(0.065, 0.01, n_samples)
        data["sector_credit_growth"] = np.random.normal(0.08, 0.03, n_samples)
        data["input_cost_inflation"] = np.random.normal(0.05, 0.02, n_samples)
        data["industry_leverage_median"] = np.clip(np.random.normal(1.5, 0.5, n_samples), 0.3, 5)
        data["commodity_exposure_score"] = np.clip(np.random.normal(4, 2, n_samples), 1, 10)
        data["regulatory_environment_score"] = np.clip(np.random.normal(5, 1.5, n_samples), 1, 10)
        data["industry_growth_rate"] = np.random.normal(0.07, 0.03, n_samples)
        data["interest_rate_sensitivity"] = np.clip(np.random.normal(5, 2, n_samples), 1, 10)
        data["fx_exposure_score"] = np.clip(np.random.normal(3, 2, n_samples), 1, 10)

        # Web intelligence
        data["news_sentiment_score"] = np.clip(np.random.normal(0.2 - 0.5 * is_default, 0.3), -1, 1)
        data["regulatory_action_flag"] = np.random.binomial(1, 0.02 + 0.15 * is_default).astype(float)
        data["litigation_score"] = np.clip(np.random.exponential(1, n_samples) + 3 * is_default, 0, 10)
        data["mgmt_change_velocity"] = np.clip(np.random.poisson(0.5 + 1.5 * is_default, n_samples), 0, 8).astype(float)
        data["social_controversy_score"] = np.clip(np.random.exponential(0.5, n_samples) + 2 * is_default, 0, 10)
        data["gst_compliance_rate"] = np.clip(np.random.normal(0.95 - 0.15 * is_default, 0.05), 0.5, 1.0)
        data["roc_compliance_score"] = np.clip(np.random.normal(7 - 3 * is_default, 1.5), 1, 10)

        df = pd.DataFrame(data)
        df["default"] = is_default
        return df

    def train(self) -> dict:
        """Train ensemble models and save to disk."""
        logger.info("Generating synthetic training data...")
        df = self.generate_synthetic_data(10000)

        # Save training data
        parquet_path = DATA_DIR / "training_data.parquet"
        df.to_parquet(parquet_path, index=False)
        logger.info(f"Training data saved to {parquet_path}")

        X = df[FEATURE_NAMES].values
        y = df["default"].values

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # SMOTE oversampling
        smote = SMOTE(random_state=42)
        X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
        logger.info(f"After SMOTE: {sum(y_train_sm==1)}/{len(y_train_sm)} defaults")

        # 1. XGBoost PD model with isotonic calibration
        logger.info("Training XGBoost PD model...")
        xgb_model = XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            scale_pos_weight=12, eval_metric="logloss",
            random_state=42,
        )
        xgb_model.fit(X_train_sm, y_train_sm)

        # Isotonic calibration on original (non-SMOTE) training data
        xgb_raw_probs = xgb_model.predict_proba(X_train)[:, 1]
        xgb_calibrator = IsotonicRegression(out_of_bounds="clip")
        xgb_calibrator.fit(xgb_raw_probs, y_train)

        # 2. LightGBM PD model
        logger.info("Training LightGBM PD model...")
        lgbm_model = LGBMClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            scale_pos_weight=12, random_state=42, verbose=-1
        )
        lgbm_model.fit(X_train_sm, y_train_sm)

        # 3. Stacking meta-learner
        logger.info("Training meta-learner...")
        xgb_probs = xgb_calibrator.predict(xgb_model.predict_proba(X_train)[:, 1]).reshape(-1, 1)
        lgbm_probs = lgbm_model.predict_proba(X_train)[:, 1].reshape(-1, 1)
        meta_features = np.hstack([xgb_probs, lgbm_probs])
        meta_model = LogisticRegression(random_state=42)
        meta_model.fit(meta_features, y_train)

        # 4. Credit Limit regressor
        logger.info("Training credit limit model...")
        # Synthetic limit targets based on features
        limit_targets = np.clip(
            df["revenue_latest"].values * 0.3 * (1 - df["default"].values * 0.8)
            * df["collateral_coverage_ratio"].values,
            0, None
        )
        X_limit_train, X_limit_test, y_limit_train, y_limit_test = train_test_split(
            X, limit_targets, test_size=0.2, random_state=42
        )
        limit_model = XGBRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42
        )
        limit_model.fit(X_limit_train, y_limit_train)

        # Evaluation
        xgb_test_probs = xgb_calibrator.predict(xgb_model.predict_proba(X_test)[:, 1])
        lgbm_test_probs = lgbm_model.predict_proba(X_test)[:, 1]
        meta_test_features = np.hstack([xgb_test_probs.reshape(-1,1), lgbm_test_probs.reshape(-1,1)])
        meta_probs = meta_model.predict_proba(meta_test_features)[:, 1]
        meta_preds = (meta_probs > 0.3).astype(int)  # F-beta threshold

        auc = roc_auc_score(y_test, meta_probs)
        brier = brier_score_loss(y_test, meta_probs)
        report = classification_report(y_test, meta_preds)

        logger.info(f"\n=== Model Performance ===")
        logger.info(f"ROC-AUC: {auc:.4f}")
        logger.info(f"Brier Score: {brier:.4f}")
        logger.info(f"\n{report}")

        # Save models
        models = {
            "xgb_pd": xgb_model,
            "xgb_calibrator": xgb_calibrator,
            "lgbm_pd": lgbm_model,
            "meta_learner": meta_model,
            "limit_model": limit_model,
            "feature_names": FEATURE_NAMES,
        }
        for name, model in models.items():
            path = MODELS_DIR / f"{name}.pkl"
            with open(path, "wb") as f:
                pickle.dump(model, f)
            logger.info(f"Saved {name} to {path}")

        return {"auc": auc, "brier": brier, "report": report}
