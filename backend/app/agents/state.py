"""Credit Analysis State for LangGraph pipeline."""
from typing import TypedDict, List, Optional


class CreditAnalysisState(TypedDict):
    case_id: str
    company_name: str
    cin: Optional[str]
    industry_code: Optional[str]
    requested_amount: float
    loan_type: str
    raw_financials: dict
    processed_financials: dict
    financial_spreads: list
    web_research: dict
    news_sentiment: dict
    regulatory_flags: list
    company_meta: dict
    bureau_data: dict
    collateral_data: dict
    macro_data: dict
    ml_features: dict
    ml_scores: dict
    early_warnings: list
    cam_sections: dict
    current_agent: str
    agent_logs: list
    errors: list
    status: str
