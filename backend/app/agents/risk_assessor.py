"""Risk Assessment Agent — ML scoring, EWS generation, LLM-powered analysis, final risk synthesis."""
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

        # LLM-powered AI Analysis
        await _emit(case_id, "Generating AI-powered credit analysis and suggestions...")
        ai_analysis = await self._generate_ai_analysis(features, score_result, shap_result, ews, state)
        state["ml_scores"]["ai_analysis"] = ai_analysis
        await _emit(case_id, "AI analysis complete", status="step_done")

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

    async def _generate_ai_analysis(self, features: dict, score_result, shap_result: dict, ews: list, state: dict) -> dict:
        """Call LLM to produce a comprehensive AI credit analysis with actionable suggestions."""
        shap_top = shap_result.get("waterfall_data", [])[:8]
        radar = shap_result.get("feature_importances", {})
        ews_red = [e for e in ews if e["severity"] == "RED"]
        ews_amber = [e for e in ews if e["severity"] == "AMBER"]
        spreads = state.get("financial_spreads", [])

        # Build financial trend mini-table
        fin_trend = ""
        for s in spreads[-3:]:
            rev = float(s.get("revenue", 0) or 0) / 1e7
            ebitda = float(s.get("ebitda", 0) or 0) / 1e7
            pat = float(s.get("pat", 0) or 0) / 1e7
            fin_trend += f"  {s.get('fiscal_year', 'N/A')}: Revenue ₹{rev:.1f}Cr, EBITDA ₹{ebitda:.1f}Cr, PAT ₹{pat:.1f}Cr\n"

        shap_desc = "\n".join(
            f"  - {f.get('display_name', f.get('feature',''))}: value={f.get('value',0):.3f}, "
            f"SHAP impact={f.get('shap_value',0):+.4f} ({f.get('direction','')})"
            for f in shap_top
        )

        ews_desc = "\n".join(f"  [{e['severity']}] {e['description']}" for e in ews_red + ews_amber)
        if not ews_desc:
            ews_desc = "  No RED or AMBER warnings triggered."

        radar_desc = ", ".join(f"{k}: {v:.1f}/10" for k, v in radar.items()) if radar else "N/A"

        prompt = f"""You are a Senior Credit Analyst at a leading Indian bank. Based on the following ML-computed credit analysis data, provide a comprehensive AI Risk Analysis with actionable suggestions.

COMPANY: {state.get('company_name', 'N/A')}
LOAN: {state.get('loan_type', 'Term Loan')} of ₹{float(state.get('requested_amount', 0) or 0)/1e7:.2f} Crore

ML DECISION: {score_result.decision}
CREDIT GRADE: {score_result.credit_grade} | PD: {score_result.pd_score:.4f} | Credit Score: {score_result.credit_score}/900
RECOMMENDED LIMIT: ₹{score_result.recommended_limit/1e7:.2f} Crore at {score_result.recommended_rate*100:.2f}%
CONFIDENCE: {score_result.confidence:.1%} | Expected Loss: ₹{score_result.expected_loss/1e5:.2f} Lakh

KEY FINANCIAL RATIOS:
  DSCR: {features.get('dscr', 0):.2f}x | D/E: {features.get('debt_equity_ratio', 0):.2f}x | Current Ratio: {features.get('current_ratio', 0):.2f}x
  EBITDA Margin: {features.get('ebitda_margin', 0):.1%} | ROE: {features.get('roe', 0):.1%}
  Altman Z: {features.get('altman_z_score', 0):.2f} | Piotroski F: {features.get('piotroski_f_score', 0):.0f}/9
  Beneish M: {features.get('beneish_m_score', 0):.2f} | CIBIL: {features.get('cibil_score', 0):.0f}

FINANCIAL TREND (Last 3 Years):
{fin_trend if fin_trend else '  N/A'}
SHAP TOP FEATURES (driving the ML model):
{shap_desc}

RISK RADAR SCORES: {radar_desc}

EARLY WARNING SIGNALS:
{ews_desc}

Provide your analysis in EXACTLY this JSON format (no markdown, no code fences):
{{
  "summary": "A 2-3 sentence executive summary of the credit profile and your key finding.",
  "strengths": ["strength 1 with specific data", "strength 2", "strength 3"],
  "concerns": ["concern 1 with specific data", "concern 2", "concern 3"],
  "suggestions": ["actionable suggestion 1 for the borrower", "suggestion 2", "suggestion 3", "suggestion 4"],
  "risk_verdict": "A single sentence final risk opinion, e.g. MODERATE RISK — Acceptable with conditions.",
  "monitoring_actions": ["specific monitoring action 1", "action 2", "action 3"]
}}

Use specific numbers from the data. Be analytical, not generic. Each suggestion must be actionable and specific to THIS borrower's situation."""

        if settings.GROQ_API_KEY:
            try:
                return await self._call_groq_analysis(prompt)
            except Exception as e:
                logger.error(f"LLM AI analysis failed: {e}")

        # Fallback: build a structured analysis from the computed data
        return self._build_fallback_analysis(features, score_result, shap_top, ews_red, ews_amber, radar)

    async def _call_groq_analysis(self, prompt: str) -> dict:
        """Call Groq LLM for AI analysis."""
        import json
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You are a Senior Credit Analyst. Respond ONLY with valid JSON. No markdown, no code fences, no extra text."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()
        # Strip code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        return json.loads(raw)

    @staticmethod
    def _build_fallback_analysis(features: dict, score_result, shap_top: list, ews_red: list, ews_amber: list, radar: dict) -> dict:
        """Build structured analysis without LLM from computed data."""
        strengths = []
        concerns = []
        suggestions = []

        dscr = features.get("dscr", 0)
        de = features.get("debt_equity_ratio", 0)
        cr = features.get("current_ratio", 0)
        altman = features.get("altman_z_score", 0)
        cibil = features.get("cibil_score", 0)

        if dscr >= 1.5:
            strengths.append(f"Strong debt servicing capacity with DSCR at {dscr:.2f}x, well above the 1.2x minimum covenant threshold")
        elif dscr < 1.2:
            concerns.append(f"Debt servicing concern — DSCR at {dscr:.2f}x is below the minimum 1.2x threshold")
            suggestions.append(f"Improve DSCR from {dscr:.2f}x to above 1.5x by reducing debt or increasing operating cash flows")

        if de < 2.0:
            strengths.append(f"Conservative leverage with D/E ratio at {de:.2f}x, providing comfortable headroom below the 3.0x threshold")
        elif de > 3.0:
            concerns.append(f"Elevated leverage — D/E ratio at {de:.2f}x exceeds the 3.0x prudential threshold")
            suggestions.append(f"Reduce D/E ratio from {de:.2f}x by retiring high-cost debt or injecting fresh equity of ₹{(de - 2.0) * 10:.0f}Cr")

        if altman > 2.9:
            strengths.append(f"Altman Z-Score of {altman:.2f} places the company in the Safe Zone, indicating low default probability")
        elif altman < 1.23:
            concerns.append(f"Altman Z-Score of {altman:.2f} indicates Distress Zone — elevated insolvency risk")

        if cibil >= 750:
            strengths.append(f"Excellent credit bureau profile with CIBIL score of {cibil:.0f}")
        elif cibil < 650:
            concerns.append(f"Below-average CIBIL score of {cibil:.0f} indicates past repayment irregularities")
            suggestions.append("Improve CIBIL score by ensuring timely repayment of all existing facilities for the next 6-12 months")

        if cr >= 1.5:
            strengths.append(f"Healthy liquidity position with current ratio at {cr:.2f}x")

        for e in ews_red:
            concerns.append(f"{e['description']}")
        for e in ews_amber[:2]:
            concerns.append(f"{e['description']}")

        if not suggestions:
            suggestions.append("Maintain current financial discipline and focus on improving operating margins")
        suggestions.append("Submit quarterly financial statements to enable continuous monitoring")
        suggestions.append("Consider obtaining an external credit rating to improve market credibility and reduce borrowing costs")

        decision = score_result.decision
        pd = score_result.pd_score
        grade = score_result.credit_grade
        risk_level = "LOW" if pd < 0.05 else "MODERATE" if pd < 0.15 else "HIGH"

        return {
            "summary": f"The ML ensemble model assigns a credit grade of {grade} with PD of {pd:.4f} ({pd*100:.2f}%), "
                       f"resulting in a {decision} decision with {score_result.confidence:.0%} confidence. "
                       f"{'The financial profile demonstrates adequate debt servicing capability and manageable leverage.' if decision != 'DECLINE' else 'Multiple risk indicators exceed prudential thresholds, warranting elevated caution.'}",
            "strengths": strengths[:4] if strengths else ["No significant strengths identified relative to risk thresholds"],
            "concerns": concerns[:4] if concerns else ["No material concerns identified — credit profile within acceptable parameters"],
            "suggestions": suggestions[:5],
            "risk_verdict": f"{risk_level} RISK — {'Recommended for approval' if decision == 'APPROVE' else 'Conditional approval subject to covenant compliance' if decision == 'CONDITIONAL' else 'Declined — risk indicators exceed acceptable thresholds'}.",
            "monitoring_actions": [
                "Quarterly DSCR and D/E covenant compliance check",
                "Monthly CIBIL monitoring for new defaults or DPD entries",
                f"Annual review with fresh financial spreads — next due in 12 months",
            ],
        }

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
