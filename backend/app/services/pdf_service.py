"""PDF generation service using WeasyPrint + Jinja2."""
import logging
import re
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import markdown

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _format_inr(value) -> str:
    """Format number as Indian currency string."""
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(v) >= 1e7:
        return f"{v / 1e7:,.2f} Cr"
    if abs(v) >= 1e5:
        return f"{v / 1e5:,.2f} L"
    return f"{v:,.0f}"


def _md_to_html(text: str) -> str:
    """Convert markdown text to safe HTML for PDF rendering."""
    if not text:
        return ""
    html = markdown.markdown(
        text,
        extensions=["tables", "fenced_code"],
    )
    return html


CAM_SECTION_TITLES = {
    "executive_summary": ("1.0", "Executive Summary"),
    "company_background": ("2.0", "Company Background"),
    "industry_analysis": ("3.0", "Industry & Market Analysis"),
    "financial_analysis": ("4.0", "Financial Analysis"),
    "banking_conduct": ("5.0", "Banking Conduct"),
    "collateral_assessment": ("6.0", "Collateral Assessment"),
    "risk_assessment": ("7.0", "Risk Assessment"),
    "credit_decision": ("8.0", "Credit Decision"),
    "covenants_conditions": ("9.0", "Covenants & Conditions"),
    "appendices": ("10.0", "Appendices"),
}


def generate_cam_pdf(cam_json: dict, case_data: dict, ml_scores: dict | None = None, ews_list: list | None = None, financial_spreads_raw: list | None = None, shap_data: dict | None = None) -> bytes:
    """
    Render the CAM as a PDF using WeasyPrint.
    Returns PDF bytes.
    """
    from weasyprint import HTML

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("cam_template.html")

    # Build sections list
    sections = []
    cam_sections = cam_json.get("sections", cam_json)
    for key in [
        "executive_summary", "company_background", "industry_analysis",
        "financial_analysis", "banking_conduct", "collateral_assessment",
        "risk_assessment", "credit_decision", "covenants_conditions", "appendices",
    ]:
        content = cam_sections.get(key, "")
        if not content:
            continue
        number, title = CAM_SECTION_TITLES.get(key, ("", key.replace("_", " ").title()))
        sections.append({
            "number": number,
            "title": title,
            "content": _md_to_html(content),
        })

    # ML score extraction
    scores = ml_scores or {}
    pd_score = scores.get("pd_score", 0)
    credit_grade = scores.get("credit_grade", "N/A")
    credit_score = scores.get("credit_score", "N/A")
    recommended_limit = scores.get("recommended_limit", case_data.get("requested_amount", 0))
    recommended_rate = scores.get("recommended_rate", "N/A")
    expected_loss = scores.get("expected_loss", 0)
    decision = scores.get("decision", "PENDING")
    dscr_latest = scores.get("dscr_latest", "N/A")
    de_ratio = scores.get("de_ratio", "N/A")

    # Financial spreads for appendix
    spread_years = []
    financial_spreads = []
    if financial_spreads_raw:
        sorted_spreads = sorted(financial_spreads_raw, key=lambda x: x.get("fiscal_year", ""))
        spread_years = [s.get("fiscal_year", "") for s in sorted_spreads]
        metrics = [
            ("Revenue", "revenue"), ("EBITDA", "ebitda"), ("PAT", "pat"),
            ("Total Assets", "total_assets"), ("Total Debt", "total_debt"),
            ("Equity", "equity"), ("CFO", "cfo"),
            ("Current Ratio", "current_ratio"), ("D/E Ratio", "debt_equity_ratio"),
            ("DSCR", "dscr"), ("EBITDA Margin %", "ebitda_margin"),
            ("ROE %", "roe"), ("ROCE %", "roce"),
        ]
        for label, field in metrics:
            values = []
            for s in sorted_spreads:
                val = s.get(field, "")
                if isinstance(val, (int, float)):
                    values.append(f"{val:,.2f}" if abs(val) < 100 else _format_inr(val))
                else:
                    values.append(str(val) if val else "—")
            financial_spreads.append({"metric": label, "values": values})

    # SHAP features for appendix
    shap_features = []
    if shap_data and shap_data.get("waterfall_data"):
        for item in shap_data["waterfall_data"][:15]:
            shap_features.append({
                "feature": item.get("feature", ""),
                "value": f"{item.get('value', 0):.4f}" if isinstance(item.get("value"), (int, float)) else str(item.get("value", "")),
                "shap_value": f"{item.get('shap_value', 0):+.4f}" if isinstance(item.get("shap_value"), (int, float)) else str(item.get("shap_value", "")),
                "direction": item.get("direction", ""),
            })

    # EWS signals
    ews_signals = []
    if ews_list:
        for e in ews_list:
            ews_signals.append({
                "signal_type": e.get("signal_type", ""),
                "severity": e.get("severity", "GREEN"),
                "description": e.get("description", ""),
                "triggered_by": e.get("triggered_by", ""),
            })

    context = {
        "company_name": case_data.get("company_name", "Unknown"),
        "case_number": case_data.get("case_number", "CAM-0000-000"),
        "appraisal_date": datetime.now().strftime("%d %B %Y"),
        "loan_type": case_data.get("loan_type", "Term Loan"),
        "requested_amount_formatted": _format_inr(case_data.get("requested_amount", 0)),
        "industry": case_data.get("industry", "General"),
        "cin": case_data.get("cin", "N/A"),
        "decision": decision,
        "credit_score": credit_score,
        "pd_score": f"{pd_score * 100:.2f}" if isinstance(pd_score, (int, float)) else str(pd_score),
        "expected_loss_formatted": _format_inr(expected_loss),
        "credit_grade": credit_grade,
        "recommended_limit_formatted": _format_inr(recommended_limit),
        "recommended_rate": f"{recommended_rate:.2f}" if isinstance(recommended_rate, (int, float)) else str(recommended_rate),
        "dscr_latest": dscr_latest,
        "de_ratio": de_ratio,
        "sections": sections,
        "ews_signals": ews_signals,
        "spread_years": spread_years,
        "financial_spreads": financial_spreads,
        "shap_features": shap_features,
    }

    html_content = template.render(**context)
    pdf_bytes = HTML(string=html_content).write_pdf()
    logger.info(f"Generated CAM PDF for {case_data.get('case_number')}: {len(pdf_bytes)} bytes")
    return pdf_bytes
