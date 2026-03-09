from pydantic import BaseModel, Field
from typing import Any, Optional, List
from datetime import datetime
from decimal import Decimal
import uuid


# --- Case Schemas ---
class CaseCreateRequest(BaseModel):
    company_name: str
    cin: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    industry_code: Optional[str] = None
    loan_type: str
    requested_amount: float
    requested_tenure_months: int
    purpose: Optional[str] = None
    collateral_type: Optional[str] = None
    collateral_value: Optional[float] = None
    collateral_description: Optional[str] = None


class CaseResponse(BaseModel):
    id: str
    case_number: str
    company_name: str
    cin: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    industry_code: Optional[str] = None
    loan_type: Optional[str] = None
    requested_amount: Optional[float] = None
    requested_tenure_months: Optional[int] = None
    purpose: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    priority: str = "NORMAL"

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    cases: List[CaseResponse]
    total: int
    page: int
    page_size: int


# --- Decision Schemas ---
class MLScoreResponse(BaseModel):
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
    shap_values: Optional[Any] = None
    feature_importances: Optional[Any] = None
    scored_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DecisionResponse(BaseModel):
    case_id: str
    company_name: str
    decision: str
    ml_score: MLScoreResponse
    early_warnings: List[dict] = []


# --- EWS Schemas ---
class EWSResponse(BaseModel):
    signal_type: str
    severity: str
    description: str
    triggered_by: str
    detected_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- CAM Schemas ---
class CAMSectionResponse(BaseModel):
    section_name: str
    content: str


class CAMResponse(BaseModel):
    case_id: str
    version: int
    sections: dict
    word_count: int
    generated_at: Optional[datetime] = None


# --- Company Lookup ---
class CompanyLookupRequest(BaseModel):
    cin: str


class CompanyLookupResponse(BaseModel):
    company_name: str
    cin: str
    date_of_incorporation: str
    registered_address: str
    authorized_capital: float
    paid_up_capital: float
    company_status: str
    directors: List[dict]
    charges: List[dict]


# --- Dashboard Stats ---
class DashboardStatsResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    active_cases: int
    approved_this_month: int
    avg_processing_time_seconds: float
    avg_credit_score: float
    total_processed: int
    model_accuracy_auc: float
    capital_saved: str


# --- Industry Benchmarks ---
class IndustryBenchmarkResponse(BaseModel):
    nic_code: str
    industry_name: str
    median_current_ratio: float
    median_debt_equity: float
    median_dscr: float
    median_ebitda_margin: float
    median_roe: float
    median_asset_turnover: float
    npl_rate: float
    sector_outlook: str
