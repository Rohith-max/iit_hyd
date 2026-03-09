"""CAM Writer Agent — generates full Credit Appraisal Memo section by section using Claude."""
import time
import asyncio
import logging
from typing import Dict

from app.agents.state import CreditAnalysisState
from app.agents.ws_manager import ws_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

CAM_SYSTEM_PROMPT = """You are a Senior Credit Analyst at a top-tier Indian commercial bank with 20 years of experience in corporate credit.
You write precise, professional Credit Appraisal Memos (CAM) following RBI guidelines and internal credit policy.
Your writing is analytical, evidence-based, and uses specific numbers from the data provided.
You flag risks clearly using banking terminology (DSCR, TOL/TNW, FACR, MPBF, etc.).
You never hallucinate numbers — only use figures explicitly provided in the context.
Write in formal British English as used in Indian banking. Be concise but comprehensive.
IMPORTANT: Output plain text only. Do NOT use markdown, headers (#), bold (**), tables (|---|), bullet lists with dashes/asterisks, or any other formatting. Use line breaks and spacing for structure."""

CAM_SECTION_PROMPTS = {
    "executive_summary": """Write the Executive Summary section of a Credit Appraisal Memo.
Decision: {decision}
Company: {company_name}
Loan Request: {loan_type} of ₹{requested_amount_cr:.2f} Crore for {tenure} months
Credit Grade: {credit_grade} | PD: {pd_score:.4f} | DSCR: {dscr:.2f}x | D/E: {de:.2f}x
Recommended Limit: ₹{recommended_limit_cr:.2f} Crore at {rate:.2f}%
Confidence: {confidence:.1%}

Include a concise 200-word summary with the decision upfront, followed by key metrics listed one per line.""",

    "company_background": """Write the Company Background section.
Company: {company_name}
CIN: {cin}
Incorporated: {date_of_incorporation}
Industry: {industry_code}
Years in Operation: {years_in_operation}
Promoter Holding: {promoter_holding_pct:.0f}%
Directors: {directors}
Registered Address: {registered_address}

Cover: business model, history, promoter profile, group structure.""",

    "industry_analysis": """Write the Industry & Market Analysis section.
Industry Code: {industry_code}
Sector Outlook: {sector_outlook}
Industry Growth: {industry_growth_rate:.1%}
Industry NPA Rate: {npl_rate:.1%}
Key Risks: {key_risks}
Growth Drivers: {growth_drivers}
Market Size: {market_size}

Cover: sector overview, competitive positioning, tailwinds/headwinds, brief Porter's 5 forces.""",

    "financial_analysis": """Write the Financial Analysis section.
5-Year Financial Summary:
{financial_table}

Key Ratios:
DSCR: {dscr:.2f}x (3Y Avg: {dscr_3y_avg:.2f}x)
Current Ratio: {current_ratio:.2f}x
D/E: {de:.2f}x
EBITDA Margin: {ebitda_margin:.1%}
ROE: {roe:.1%}
Altman Z: {altman_z:.2f}

Anomalies detected: {anomalies}
Peer comparison: {peer_summary}

Cover: 5-year trends, ratio analysis, cash flow quality, working capital analysis, peer comparison. List ratios one per line.""",

    "banking_conduct": """Write the Banking Conduct section.
CIBIL Score: {cibil_score}
DPD History: 0-DPD: {dpd_0}, 30-DPD: {dpd_30}, 60-DPD: {dpd_60}, 90-DPD: {dpd_90}
Existing Utilization: {utilization:.0%}
Loan Enquiries (6M): {enquiries}
Existing Charges: {charges}

Cover: account conduct, existing facilities, utilization patterns.""",

    "collateral_assessment": """Write the Collateral Assessment section.
Collateral Type: {collateral_type}
LTV Ratio: {ltv:.0%}
Coverage Ratio: {coverage:.2f}x
SARFAESI Applicable: {sarfaesi}
Collateral Value: ₹{collateral_value_cr:.2f} Crore

Cover: collateral details, LTV, enforceability, SARFAESI applicability.""",

    "risk_assessment": """Write the Risk Assessment section.
PD Model Output: {pd_score:.4f} (Grade: {credit_grade})
Altman Z-Score: {altman_z:.2f} ({z_zone})
Piotroski F-Score: {f_score:.0f}/9
Beneish M-Score: {m_score:.2f} ({m_zone})

SHAP Analysis Summary: {shap_summary}

Risk Radar Scores (0-10): Financial: {radar_financial}, Business: {radar_business}, Management: {radar_management}, Industry: {radar_industry}, Bureau: {radar_bureau}, Collateral: {radar_collateral}

EWS Triggers: {ews_summary}

Cover: ML model interpretation, key risk factors with mitigants, EWS analysis.""",

    "credit_decision": """Write the Credit Decision section.
Decision: {decision}
Recommended Limit: ₹{recommended_limit_cr:.2f} Crore
Pricing: MCLR ({mclr:.2f}%) + Risk Premium ({risk_premium:.2f}%) = {total_rate:.2f}%
Expected Loss: ₹{expected_loss_lakh:.2f} Lakh ({el_pct:.2f}% of limit)
Confidence: {confidence:.1%}

Cover: decision rationale, limit working, pricing rationale (RARR breakdown), tenure recommendation.""",

    "covenants": """Write the Covenants & Conditions section.
Credit Grade: {credit_grade}
DSCR: {dscr:.2f}x
D/E: {de:.2f}x
Decision: {decision}

Recommend financial covenants (DSCR > 1.25x, D/E < 3x, etc.), reporting covenants, pre-disbursement conditions, ongoing monitoring requirements.""",

    "appendices": """Generate the Appendices section with:
1. 5-Year Financial Spreads (listed one per line)
2. Key Ratio Trends (listed one per line)
3. Top 10 SHAP Feature Importance
4. Data Sources List

Financial Data:
{financial_table}

SHAP Top Features:
{shap_features}

Data Sources: DuckDB/Databricks, MCA Portal, CIBIL Bureau, News (Tavily), Industry Reports (ChromaDB RAG)""",
}


async def _emit(case_id: str, thought: str, section: str = "", status: str = "running"):
    await ws_manager.broadcast(case_id, {
        "type": "agent_event",
        "agent": "CAMWriter",
        "thought": thought,
        "section": section,
        "status": status,
    })


class CAMWriterAgent:
    """Generates full CAM document section by section using Claude with streaming."""

    async def run(self, state: CreditAnalysisState) -> CreditAnalysisState:
        case_id = state["case_id"]
        start = time.time()
        await _emit(case_id, "Initiating CAM document generation...")

        sections_order = [
            "executive_summary", "company_background", "industry_analysis",
            "financial_analysis", "banking_conduct", "collateral_assessment",
            "risk_assessment", "credit_decision", "covenants", "appendices",
        ]
        section_titles = {
            "executive_summary": "1.0 Executive Summary",
            "company_background": "2.0 Company Background",
            "industry_analysis": "3.0 Industry & Market Analysis",
            "financial_analysis": "4.0 Financial Analysis",
            "banking_conduct": "5.0 Banking Conduct",
            "collateral_assessment": "6.0 Collateral Assessment",
            "risk_assessment": "7.0 Risk Assessment",
            "credit_decision": "8.0 Credit Decision",
            "covenants": "9.0 Covenants & Conditions",
            "appendices": "10.0 Appendices",
        }

        cam_sections = {}
        for section_key in sections_order:
            title = section_titles[section_key]
            await _emit(case_id, f"Writing {title}...", section=section_key, status="writing")

            context = self._build_context(section_key, state)
            content = await self._write_section(case_id, section_key, context)
            cam_sections[section_key] = {"title": title, "content": content}

            word_count = len(content.split())
            await _emit(case_id, f"Completed {title} ({word_count} words)", section=section_key, status="section_done")

            if settings.DEMO_MODE:
                await asyncio.sleep(0.2)

        state["cam_sections"] = cam_sections
        total_words = sum(len(s["content"].split()) for s in cam_sections.values())

        elapsed = int((time.time() - start) * 1000)
        state["agent_logs"].append({
            "agent_name": "CAMWriter",
            "step_name": "full_cam",
            "thought": f"CAM generation complete: {total_words} words across {len(cam_sections)} sections",
            "duration_ms": elapsed,
            "status": "completed",
        })
        await _emit(case_id, f"CAM document complete — {total_words} words ({elapsed}ms)", status="completed")
        state["status"] = "COMPLETED"
        return state

    async def _write_section(self, case_id: str, section_key: str, context: dict) -> str:
        """Write a CAM section using Claude streaming or fallback."""
        prompt_template = CAM_SECTION_PROMPTS.get(section_key, "")
        try:
            prompt = prompt_template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing key {e} in context for {section_key}")
            prompt = prompt_template

        if not settings.DEMO_MODE and settings.ANTHROPIC_API_KEY:
            return await self._stream_claude(case_id, section_key, prompt)
        else:
            return await self._generate_fallback(case_id, section_key, context)

    async def _stream_claude(self, case_id: str, section_key: str, prompt: str) -> str:
        """Stream CAM section from Claude."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            full_text = ""
            async with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=CAM_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                async for text in stream.text_stream:
                    full_text += text
                    await ws_manager.broadcast(case_id, {
                        "type": "cam_stream",
                        "section": section_key,
                        "delta": text,
                    })
            return full_text
        except Exception as e:
            logger.error(f"Claude streaming failed for {section_key}: {e}")
            return await self._generate_fallback(case_id, section_key, {})

    async def _generate_fallback(self, case_id: str, section_key: str, context: dict) -> str:
        """Generate realistic CAM content without LLM."""
        content = FALLBACK_SECTIONS.get(section_key, lambda c: "Section content to be generated.")(context)
        # Simulate streaming
        words = content.split()
        chunk_size = 5
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            await ws_manager.broadcast(case_id, {
                "type": "cam_stream",
                "section": section_key,
                "delta": chunk + " ",
            })
            await asyncio.sleep(0.02)
        return content

    def _build_context(self, section_key: str, state: dict) -> dict:
        """Build context dict for prompt formatting."""
        scores = state.get("ml_scores", {})
        features = state.get("ml_features", {})
        meta = state.get("company_meta", {})
        web = state.get("web_research", {})
        collateral = state.get("collateral_data", {})
        spreads = state.get("financial_spreads", [])

        requested_amount = float(state.get("requested_amount", 0) or 0)
        recommended_limit = float(scores.get("recommended_limit", 0) or 0)

        # Financial table
        fin_lines = []
        for s in spreads:
            fin_lines.append(f"{s.get('fiscal_year','')}: Rev ₹{float(s.get('revenue',0) or 0)/10000000:.1f}Cr, EBITDA ₹{float(s.get('ebitda',0) or 0)/10000000:.1f}Cr, PAT ₹{float(s.get('pat',0) or 0)/10000000:.1f}Cr")
        financial_table = "\n".join(fin_lines) if fin_lines else "N/A"

        # SHAP features
        shap_vals = scores.get("shap_values", [])
        shap_lines = [f"{s.get('display_name','')}: {s.get('value',0):.4f} ({s.get('direction', '')} {abs(s.get('shap_value',0)):.4f})" for s in shap_vals[:10]]

        radar = scores.get("feature_importances", {})
        ews = state.get("early_warnings", [])
        ews_summary = "; ".join([f"[{e['severity']}] {e['description']}" for e in ews]) or "No triggers"
        industry_ctx = web.get("industry_context", {})

        return {
            "company_name": state.get("company_name", ""),
            "cin": state.get("cin", "N/A"),
            "loan_type": state.get("loan_type", "Term Loan"),
            "requested_amount_cr": requested_amount / 10000000,
            "tenure": state.get("requested_tenure_months", 60),
            "decision": scores.get("decision", "PENDING"),
            "credit_grade": scores.get("credit_grade", "N/A"),
            "pd_score": float(scores.get("pd_score", 0) or 0),
            "dscr": float(features.get("dscr", 0) or 0),
            "dscr_3y_avg": float(features.get("dscr_3y_avg", 0) or 0),
            "de": float(features.get("debt_equity_ratio", 0) or 0),
            "current_ratio": float(features.get("current_ratio", 0) or 0),
            "ebitda_margin": float(features.get("ebitda_margin", 0) or 0),
            "roe": float(features.get("roe", 0) or 0),
            "altman_z": float(features.get("altman_z_score", 0) or 0),
            "f_score": float(features.get("piotroski_f_score", 0) or 0),
            "m_score": float(features.get("beneish_m_score", 0) or 0),
            "z_zone": "Safe" if features.get("altman_z_score", 0) > 2.9 else "Grey" if features.get("altman_z_score", 0) > 1.23 else "Distress",
            "m_zone": "Normal" if features.get("beneish_m_score", -3) < -1.78 else "Manipulation Risk",
            "recommended_limit_cr": recommended_limit / 10000000,
            "rate": float(scores.get("recommended_rate", 0) or 0) * 100,
            "mclr": 8.50,
            "risk_premium": float(scores.get("risk_premium", 0) or 0) * 100,
            "total_rate": float(scores.get("recommended_rate", 0) or 0) * 100,
            "expected_loss_lakh": float(scores.get("expected_loss", 0) or 0) / 100000,
            "el_pct": (float(scores.get("expected_loss", 0) or 0) / max(recommended_limit, 1)) * 100,
            "confidence": float(scores.get("confidence", 0) or 0),
            "date_of_incorporation": meta.get("date_of_incorporation", "N/A"),
            "industry_code": state.get("industry_code", "N/A"),
            "years_in_operation": meta.get("years_in_operation", "N/A"),
            "promoter_holding_pct": float(meta.get("promoter_holding_pct", 0) or 0),
            "directors": str(meta.get("directors", [])),
            "registered_address": meta.get("registered_address", "N/A"),
            "charges": str(meta.get("charges", [])),
            "sector_outlook": industry_ctx.get("sector_outlook", "N/A"),
            "industry_growth_rate": float(features.get("industry_growth_rate", 0.07) or 0),
            "npl_rate": float(features.get("industry_npl_rate", 0.05) or 0),
            "key_risks": str(industry_ctx.get("key_risks", [])),
            "growth_drivers": str(industry_ctx.get("growth_drivers", [])),
            "market_size": industry_ctx.get("market_size", "N/A"),
            "financial_table": financial_table,
            "anomalies": str(state.get("processed_financials", {}).get("anomalies", [])),
            "peer_summary": str(state.get("processed_financials", {}).get("peer_comparison", {}).get("above_median_count", 0)) + " of 8 metrics above industry median",
            "cibil_score": float(features.get("cibil_score", 0) or 0),
            "dpd_0": int(features.get("dpd_0_count", 0)),
            "dpd_30": int(features.get("dpd_30_count", 0)),
            "dpd_60": int(features.get("dpd_60_count", 0)),
            "dpd_90": int(features.get("dpd_90_count", 0)),
            "utilization": float(features.get("existing_loan_utilization", 0) or 0),
            "enquiries": int(features.get("loan_enquiries_6m", 0)),
            "collateral_type": collateral.get("collateral_type", "N/A"),
            "ltv": float(collateral.get("ltv_ratio", 0) or 0),
            "coverage": float(collateral.get("collateral_coverage_ratio", 0) or 0),
            "sarfaesi": "Yes" if collateral.get("sarfaesi_applicable", 0) else "No",
            "collateral_value_cr": float(collateral.get("collateral_value_to_loan", 1) or 1) * requested_amount / 10000000,
            "shap_summary": scores.get("shap_summary", ""),
            "shap_features": "\n".join(shap_lines),
            "radar_financial": radar.get("financial", 0),
            "radar_business": radar.get("business", 0),
            "radar_management": radar.get("management", 0),
            "radar_industry": radar.get("industry", 0),
            "radar_bureau": radar.get("bureau", 0),
            "radar_collateral": radar.get("collateral", 0),
            "ews_summary": ews_summary,
        }


def _fallback_exec_summary(ctx):
    decision = ctx.get("decision", "PENDING")
    company = ctx.get("company_name", "Company")
    grade = ctx.get("credit_grade", "N/A")
    limit = ctx.get("recommended_limit_cr", 0)
    rate = ctx.get("rate", 0)
    strength = 'strong' if decision == 'APPROVE' else 'moderate' if decision == 'CONDITIONAL' else 'weak'
    servicing = 'adequate' if ctx.get('dscr', 0) > 1.5 else 'marginal'
    return (
        f"Executive Summary\n\n"
        f"Decision: {decision}\n\n"
        f"This Credit Appraisal Memo pertains to the credit proposal of {company} "
        f"seeking a {ctx.get('loan_type', 'Term Loan')} facility of Rs {ctx.get('requested_amount_cr', 0):.2f} Crore "
        f"for a tenure of {ctx.get('tenure', 60)} months.\n\n"
        f"Based on comprehensive analysis encompassing financial performance, business quality assessment, "
        f"credit bureau data, industry outlook, and machine learning-based credit scoring, "
        f"the recommended decision is {decision}.\n\n"
        f"Key Metrics:\n"
        f"  Credit Grade: {grade}\n"
        f"  PD Score: {ctx.get('pd_score', 0):.4f}\n"
        f"  DSCR: {ctx.get('dscr', 0):.2f}x\n"
        f"  D/E Ratio: {ctx.get('de', 0):.2f}x\n"
        f"  Recommended Limit: Rs {limit:.2f} Cr\n"
        f"  Recommended Rate: {rate:.2f}%\n"
        f"  Confidence: {ctx.get('confidence', 0):.1%}\n\n"
        f"The company demonstrates {strength} financial fundamentals with {servicing} debt-servicing capability."
    )


def _fallback_company_bg(ctx):
    return (
        f"Company Background\n\n"
        f"{ctx.get('company_name', 'Company')} (CIN: {ctx.get('cin', 'N/A')}) was incorporated on "
        f"{ctx.get('date_of_incorporation', 'N/A')} and has been in operation for approximately "
        f"{ctx.get('years_in_operation', 'N/A')} years.\n\n"
        f"The company is registered at {ctx.get('registered_address', 'N/A')} and operates in the "
        f"{ctx.get('industry_code', 'N/A')} sector. Promoter holding stands at {ctx.get('promoter_holding_pct', 0):.0f}%.\n\n"
        f"Board of Directors:\n"
        f"The company's governance structure includes experienced professionals across finance, "
        f"operations, and industry domains.\n\n"
        f"Group Structure:\n"
        f"The company operates as part of a structured group with established business relationships "
        f"and operational synergies."
    )


def _fallback_industry(ctx):
    npl = ctx.get('npl_rate', 0.05)
    npl_note = 'within acceptable range' if npl < 0.08 else 'elevated levels warrant caution'
    return (
        f"Industry and Market Analysis\n\n"
        f"Sector Overview: The company operates in a sector with an estimated market size of "
        f"{ctx.get('market_size', 'N/A')}, growing at {ctx.get('industry_growth_rate', 0.07):.1%} annually.\n\n"
        f"Outlook: {ctx.get('sector_outlook', 'Moderate growth expected')}\n\n"
        f"Industry NPA Rate: {npl:.1%} ({npl_note})\n\n"
        f"Growth Drivers: {ctx.get('growth_drivers', 'N/A')}\n\n"
        f"Key Risks: {ctx.get('key_risks', 'N/A')}\n\n"
        f"Porter's Five Forces (Brief):\n"
        f"  Supplier Power: Moderate\n"
        f"  Buyer Power: Moderate to High\n"
        f"  Competitive Rivalry: High\n"
        f"  Threat of Substitutes: Low to Moderate\n"
        f"  Barriers to Entry: Moderate"
    )


def _fallback_financial(ctx):
    dscr = ctx.get('dscr', 0)
    cr = ctx.get('current_ratio', 0)
    de = ctx.get('de', 0)
    ebitda = ctx.get('ebitda_margin', 0)
    roe = ctx.get('roe', 0)
    cf_note = 'positive and support debt servicing' if dscr > 1.5 else 'adequate but warrant monitoring'
    return (
        f"Financial Analysis\n\n"
        f"5-Year Financial Summary:\n{ctx.get('financial_table', 'N/A')}\n\n"
        f"Key Ratio Analysis:\n"
        f"  DSCR: {dscr:.2f}x ({'Adequate' if dscr > 1.5 else 'Marginal'})\n"
        f"  Current Ratio: {cr:.2f}x ({'Healthy' if cr > 1.5 else 'Tight'})\n"
        f"  D/E: {de:.2f}x ({'Conservative' if de < 2 else 'Leveraged'})\n"
        f"  EBITDA Margin: {ebitda:.1%} ({'Strong' if ebitda > 0.2 else 'Moderate'})\n"
        f"  ROE: {roe:.1%} ({'Good' if roe > 0.15 else 'Moderate'})\n"
        f"  Altman Z: {ctx.get('altman_z', 0):.2f} ({ctx.get('z_zone', 'N/A')})\n\n"
        f"Peer Comparison: The company performs above industry median on {ctx.get('peer_summary', 'N/A')}.\n\n"
        f"Cash Flow Quality: Operating cash flows are {cf_note}."
    )


def _fallback_banking(ctx):
    cibil = ctx.get('cibil_score', 0)
    cibil_note = 'Satisfactory' if cibil > 700 else 'Below threshold'
    return (
        f"Banking Conduct\n\n"
        f"CIBIL Score: {cibil:.0f} ({cibil_note})\n\n"
        f"DPD History (Last 12 Months):\n"
        f"  0 DPD: {ctx.get('dpd_0', 0)} months\n"
        f"  30+ DPD: {ctx.get('dpd_30', 0)} instances\n"
        f"  60+ DPD: {ctx.get('dpd_60', 0)} instances\n"
        f"  90+ DPD: {ctx.get('dpd_90', 0)} instances\n\n"
        f"Existing Facility Utilization: {ctx.get('utilization', 0):.0%}\n"
        f"Loan Enquiries (6 months): {ctx.get('enquiries', 0)}"
    )


def _fallback_collateral(ctx):
    cov = ctx.get('coverage', 0)
    cov_note = 'provides adequate security' if cov > 1.2 else 'coverage is marginal'
    return (
        f"Collateral Assessment\n\n"
        f"Collateral Type: {ctx.get('collateral_type', 'N/A')}\n"
        f"Loan-to-Value (LTV): {ctx.get('ltv', 0):.0%}\n"
        f"Coverage Ratio: {cov:.2f}x\n"
        f"SARFAESI Applicable: {ctx.get('sarfaesi', 'N/A')}\n"
        f"Estimated Collateral Value: Rs {ctx.get('collateral_value_cr', 0):.2f} Crore\n\n"
        f"The collateral {cov_note} for the proposed facility."
    )


def _fallback_risk(ctx):
    return (
        f"Risk Assessment\n\n"
        f"ML Model Output:\n"
        f"  PD Score: {ctx.get('pd_score', 0):.4f} (Grade: {ctx.get('credit_grade', 'N/A')})\n"
        f"  Altman Z-Score: {ctx.get('altman_z', 0):.2f} ({ctx.get('z_zone', 'N/A')})\n"
        f"  Piotroski F-Score: {ctx.get('f_score', 0):.0f}/9\n"
        f"  Beneish M-Score: {ctx.get('m_score', 0):.2f} ({ctx.get('m_zone', 'N/A')})\n\n"
        f"SHAP Analysis: {ctx.get('shap_summary', 'N/A')}\n\n"
        f"Risk Radar Scores (0-10):\n"
        f"  Financial: {ctx.get('radar_financial', 0)}\n"
        f"  Business: {ctx.get('radar_business', 0)}\n"
        f"  Management: {ctx.get('radar_management', 0)}\n"
        f"  Industry: {ctx.get('radar_industry', 0)}\n"
        f"  Bureau: {ctx.get('radar_bureau', 0)}\n"
        f"  Collateral: {ctx.get('radar_collateral', 0)}\n\n"
        f"Early Warning Signals: {ctx.get('ews_summary', 'None')}"
    )


def _fallback_decision(ctx):
    return (
        f"Credit Decision\n\n"
        f"Recommendation: {ctx.get('decision', 'PENDING')}\n\n"
        f"Recommended Facility:\n"
        f"  Facility Type: {ctx.get('loan_type', 'Term Loan')}\n"
        f"  Recommended Limit: Rs {ctx.get('recommended_limit_cr', 0):.2f} Crore\n"
        f"  Tenor: {ctx.get('tenure', 60)} months\n"
        f"  Rate: MCLR ({ctx.get('mclr', 8.5):.2f}%) + {ctx.get('risk_premium', 0):.2f}% = {ctx.get('total_rate', 0):.2f}% p.a.\n"
        f"  Expected Loss: Rs {ctx.get('expected_loss_lakh', 0):.2f} Lakh ({ctx.get('el_pct', 0):.2f}% of limit)\n"
        f"  Confidence: {ctx.get('confidence', 0):.1%}"
    )


def _fallback_covenants(ctx):
    return (
        "Covenants and Conditions\n\n"
        "Financial Covenants:\n"
        "  1. DSCR to be maintained at minimum 1.25x at all times\n"
        "  2. Debt-to-Equity ratio not to exceed 3.00x\n"
        "  3. Current Ratio to be maintained at minimum 1.33x\n"
        "  4. Promoter holding not to fall below 51%\n"
        "  5. No dividend distribution if DSCR falls below 1.50x\n\n"
        "Reporting Covenants:\n"
        "  1. Audited annual financials within 180 days of year-end\n"
        "  2. Quarterly provisional financials within 45 days\n"
        "  3. Monthly stock and debtors statements\n"
        "  4. Annual insurance renewal confirmation\n\n"
        "Pre-Disbursement Conditions:\n"
        "  1. Completion of all documentation including hypothecation/mortgage\n"
        "  2. Creation of charge with ROC\n"
        "  3. Submission of last 3 years audited financials\n"
        "  4. Board resolution authorising the borrowing\n\n"
        "Ongoing Monitoring:\n"
        "  1. Annual credit review\n"
        "  2. Quarterly financial covenant compliance check\n"
        "  3. Half-yearly unit visit report\n"
        "  4. Regular CIBIL monitoring"
    )


def _fallback_appendices(ctx):
    return (
        f"Appendices\n\n"
        f"A. Financial Spreads (5-Year)\n{ctx.get('financial_table', 'N/A')}\n\n"
        f"B. SHAP Feature Importance (Top 10)\n{ctx.get('shap_features', 'N/A')}\n\n"
        f"C. Data Sources\n"
        f"  1. Financial Data: DuckDB (Databricks Delta Lake)\n"
        f"  2. Company Information: MCA Portal (Ministry of Corporate Affairs)\n"
        f"  3. Credit Bureau: CIBIL Commercial\n"
        f"  4. News and Web Intelligence: Tavily Search API\n"
        f"  5. Industry Reports: ChromaDB Vector Store (RAG)\n"
        f"  6. Regulatory: SEBI, NCLT, RBI databases\n"
        f"  7. ML Models: XGBoost + LightGBM Ensemble (10,000 sample training set)\n\n"
        f"This Credit Appraisal Memo was generated by NEXUS CREDIT AI Engine v1.0\n"
        f"Document Classification: CONFIDENTIAL"
    )


FALLBACK_SECTIONS = {
    "executive_summary": _fallback_exec_summary,
    "company_background": _fallback_company_bg,
    "industry_analysis": _fallback_industry,
    "financial_analysis": _fallback_financial,
    "banking_conduct": _fallback_banking,
    "collateral_assessment": _fallback_collateral,
    "risk_assessment": _fallback_risk,
    "credit_decision": _fallback_decision,
    "covenants": _fallback_covenants,
    "appendices": _fallback_appendices,
}
