"""Risk Assessment Agent — ML scoring, EWS generation, final risk synthesis."""
import time
import asyncio
import logging
from typing import Dict, List

from app.agents.state import CreditAnalysisState
from app.agents.ws_manager import ws_manager
from app.ml.scorer import CreditScorer
from app.ml.explainer import SHAPExplainer
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _emit(case_id: str, thought: str, action: str = "", observation: str = "", status: str = "running"):
    await ws_manager.broadcast(case_id, {
        "type": "agent_event",
        "agent": "RiskAssessment",
        "thought": thought,
        "action": action,
        "observation": observation,
        "status": status,
    })


class RiskAssessmentAgent:
    """Runs ML scoring, generates EWS, produces final risk assessment."""

    def __init__(self):
        self.scorer = CreditScorer()
        self.explainer = SHAPExplainer()

    async def run(self, state: CreditAnalysisState) -> CreditAnalysisState:
        case_id = state["case_id"]
        start = time.time()

        await _emit(case_id, "Initiating ML credit scoring engine...")

        features = state.get("ml_features", {})
        # Merge web research features
        web = state.get("web_research", {})
        for key in ["news_sentiment_score", "regulatory_action_flag", "litigation_score",
                     "mgmt_change_velocity", "social_controversy_score", "gst_compliance_rate", "roc_compliance_score"]:
            if key in web:
                features[key] = web[key]

        requested_amount = state.get("requested_amount", 0)

        # Run ML scoring
        await _emit(case_id, "Running XGBoost + LightGBM ensemble with meta-learner...", action="scorer.score()")
        score_result = self.scorer.score(features, requested_amount)
        state["ml_scores"] = score_result.to_dict()

        if settings.DEMO_MODE:
            await asyncio.sleep(0.3)

        await _emit(case_id, f"PD Score: {score_result.pd_score:.4f}", status="metric")
        await _emit(case_id, f"Credit Grade: {score_result.credit_grade}", status="metric")
        await _emit(case_id, f"Credit Score: {score_result.credit_score}/900", status="metric")
        await _emit(case_id, f"Decision: {score_result.decision}", status="metric")

        if settings.DEMO_MODE:
            await asyncio.sleep(0.3)

        # SHAP explainability
        await _emit(case_id, "Generating SHAP explainability analysis...", action="shap.explain()")
        shap_result = self.explainer.explain(features)
        state["ml_scores"]["shap_values"] = shap_result.get("waterfall_data", [])
        state["ml_scores"]["feature_importances"] = shap_result.get("risk_radar", {})
        state["ml_scores"]["shap_summary"] = shap_result.get("natural_language_summary", "")
        await _emit(case_id, shap_result.get("natural_language_summary", ""), status="step_done")

        if settings.DEMO_MODE:
            await asyncio.sleep(0.3)

        # RARR breakdown
        await _emit(case_id, "Computing Risk-Adjusted Rate of Return (RARR)...")
        rate = score_result.recommended_rate
        premium = score_result.risk_premium
        await _emit(case_id, f"RARR: MCLR 8.50% + Risk Premium {premium*100:.2f}% = {rate*100:.2f}%", status="metric")

        # Recommended limit
        limit_cr = score_result.recommended_limit / 10000000
        await _emit(case_id, f"Recommended Limit: ₹{limit_cr:.2f} Cr", status="metric")

        # EWS
        await _emit(case_id, "Checking 15 Early Warning Signal triggers...")
        ews = self.generate_ews(features, state.get("financial_spreads", []))
        state["early_warnings"] = ews

        for signal in ews:
            color = "🔴" if signal["severity"] == "RED" else ("🟡" if signal["severity"] == "AMBER" else "🟢")
            await _emit(case_id, f"{color} EWS: {signal['description']}", status="warning")

        elapsed = int((time.time() - start) * 1000)
        state["agent_logs"].append({
            "agent_name": "RiskAssessment",
            "step_name": "full_assessment",
            "thought": f"Risk assessment complete: {score_result.decision}",
            "duration_ms": elapsed,
            "status": "completed",
        })
        await _emit(case_id, f"Risk assessment complete ({elapsed}ms) — {score_result.decision}", status="completed")
        state["current_agent"] = "CAMWriter"
        return state

    def generate_ews(self, features: dict, spreads: list) -> List[dict]:
        """Check 15 Early Warning Signal trigger conditions."""
        signals = []

        checks = [
            ("DSCR below threshold", features.get("dscr", 2) < 1.2, "RED",
             f"DSCR at {features.get('dscr', 0):.2f}x — below minimum 1.2x covenant", "DSCR"),
            ("High leverage", features.get("debt_equity_ratio", 1) > 3.0, "RED",
             f"D/E ratio at {features.get('debt_equity_ratio', 0):.2f}x — exceeds 3.0x threshold", "Leverage"),
            ("Promoter pledge high", features.get("promoter_pledge_pct", 0) > 50, "RED",
             f"Promoter pledging at {features.get('promoter_pledge_pct', 0):.0f}% — exceeds 50% threshold", "Governance"),
            ("Net loss year", features.get("pat_latest", 1) < 0, "RED",
             "Company reported net loss in latest fiscal year", "Profitability"),
            ("Qualified audit", features.get("qualified_audit_flag", 0) > 0, "AMBER",
             "Qualified audit opinion flagged by statutory auditor", "Governance"),
            ("Low interest coverage", features.get("interest_coverage", 5) < 2.0, "AMBER",
             f"Interest coverage at {features.get('interest_coverage', 0):.2f}x — below 2.0x", "Debt Servicing"),
            ("Deteriorating margins", features.get("ebitda_yoy", 0) < -0.15, "AMBER",
             f"EBITDA margin declined by {abs(features.get('ebitda_yoy', 0))*100:.1f}% YoY", "Profitability"),
            ("High CCC", features.get("cash_conversion_cycle", 0) > 120, "AMBER",
             f"Cash conversion cycle at {features.get('cash_conversion_cycle', 0):.0f} days", "Working Capital"),
            ("Low CIBIL", features.get("cibil_score", 750) < 650, "AMBER",
             f"CIBIL score at {features.get('cibil_score', 0):.0f} — below 650 threshold", "Bureau"),
            ("High DPD", features.get("dpd_90_count", 0) > 0, "RED",
             f"90+ DPD instances: {features.get('dpd_90_count', 0):.0f}", "Bureau"),
            ("Revenue decline", features.get("revenue_yoy", 0) < -0.10, "AMBER",
             f"Revenue declined by {abs(features.get('revenue_yoy', 0))*100:.1f}% YoY", "Revenue"),
            ("Altman distress", features.get("altman_z_score", 3) < 1.23, "RED",
             f"Altman Z-Score at {features.get('altman_z_score', 0):.2f} — Distress Zone", "Solvency"),
            ("Beneish manipulation", features.get("beneish_m_score", -3) > -1.78, "AMBER",
             f"Beneish M-Score at {features.get('beneish_m_score', 0):.2f} — possible manipulation", "Earnings Quality"),
            ("Regulatory action", features.get("regulatory_action_flag", 0) > 0, "RED",
             "Active regulatory action detected", "Compliance"),
            ("High related party", features.get("related_party_txn_ratio", 0) > 0.15, "AMBER",
             f"Related party transactions at {features.get('related_party_txn_ratio', 0)*100:.1f}% of revenue", "Governance"),
        ]

        for name, triggered, severity, description, triggered_by in checks:
            if triggered:
                signals.append({
                    "signal_type": name,
                    "severity": severity,
                    "description": description,
                    "triggered_by": triggered_by,
                })

        # Add GREEN signals for passing checks
        if not any(s["signal_type"] == "DSCR below threshold" for s in signals):
            signals.append({
                "signal_type": "DSCR adequate",
                "severity": "GREEN",
                "description": f"DSCR at {features.get('dscr', 0):.2f}x — above 1.2x minimum",
                "triggered_by": "DSCR",
            })

        return signals
