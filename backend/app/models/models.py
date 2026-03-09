import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Numeric, Boolean, ForeignKey, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class CreditCase(Base):
    __tablename__ = "credit_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(String(20), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    cin = Column(String(21))
    gstin = Column(String(15))
    pan = Column(String(10))
    industry_code = Column(String(10))
    loan_type = Column(String(50))
    requested_amount = Column(Numeric(18, 2))
    requested_tenure_months = Column(Integer)
    purpose = Column(Text)
    status = Column(String(30), default="INTAKE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    assigned_analyst_id = Column(UUID(as_uuid=True))
    priority = Column(String(10), default="NORMAL")

    data_sources = relationship("CaseDataSource", back_populates="case", cascade="all, delete-orphan")
    financial_spreads = relationship("FinancialSpread", back_populates="case", cascade="all, delete-orphan")
    ml_scores = relationship("MLScore", back_populates="case", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="case", cascade="all, delete-orphan")
    cam_documents = relationship("CAMDocument", back_populates="case", cascade="all, delete-orphan")
    early_warnings = relationship("EarlyWarningSignal", back_populates="case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CreditCase {self.case_number}: {self.company_name} [{self.status}]>"


class CaseDataSource(Base):
    __tablename__ = "case_data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("credit_cases.id"), nullable=False)
    source_type = Column(String(50))
    source_identifier = Column(Text)
    raw_data = Column(JSON)
    processed_data = Column(JSON)
    ingestion_status = Column(String(20))
    ingested_at = Column(DateTime(timezone=True))

    case = relationship("CreditCase", back_populates="data_sources")

    def __repr__(self):
        return f"<CaseDataSource {self.source_type} [{self.ingestion_status}]>"


class FinancialSpread(Base):
    __tablename__ = "financial_spreads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("credit_cases.id"), nullable=False)
    fiscal_year = Column(String(10))
    period_type = Column(String(10))
    # P&L
    revenue = Column(Numeric(18, 2))
    gross_profit = Column(Numeric(18, 2))
    ebitda = Column(Numeric(18, 2))
    ebit = Column(Numeric(18, 2))
    pbt = Column(Numeric(18, 2))
    pat = Column(Numeric(18, 2))
    # Balance Sheet
    total_assets = Column(Numeric(18, 2))
    total_debt = Column(Numeric(18, 2))
    equity = Column(Numeric(18, 2))
    current_assets = Column(Numeric(18, 2))
    current_liabilities = Column(Numeric(18, 2))
    cash_equivalents = Column(Numeric(18, 2))
    # Cash Flow
    cfo = Column(Numeric(18, 2))
    cfi = Column(Numeric(18, 2))
    cff = Column(Numeric(18, 2))
    # Ratios
    current_ratio = Column(Numeric(8, 4))
    debt_equity_ratio = Column(Numeric(8, 4))
    dscr = Column(Numeric(8, 4))
    interest_coverage = Column(Numeric(8, 4))
    gross_margin = Column(Numeric(8, 4))
    ebitda_margin = Column(Numeric(8, 4))
    pat_margin = Column(Numeric(8, 4))
    roce = Column(Numeric(8, 4))
    roe = Column(Numeric(8, 4))
    asset_turnover = Column(Numeric(8, 4))
    debtor_days = Column(Integer)
    creditor_days = Column(Integer)
    inventory_days = Column(Integer)

    case = relationship("CreditCase", back_populates="financial_spreads")

    def __repr__(self):
        return f"<FinancialSpread {self.fiscal_year} Rev={self.revenue}>"


class MLScore(Base):
    __tablename__ = "ml_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("credit_cases.id"), nullable=False)
    model_version = Column(String(20))
    pd_score = Column(Numeric(6, 4))
    lgd_score = Column(Numeric(6, 4))
    ead = Column(Numeric(18, 2))
    expected_loss = Column(Numeric(18, 2))
    credit_grade = Column(String(5))
    credit_score = Column(Integer)
    recommended_limit = Column(Numeric(18, 2))
    recommended_rate = Column(Numeric(6, 4))
    risk_premium = Column(Numeric(6, 4))
    decision = Column(String(20))
    confidence = Column(Numeric(4, 3))
    shap_values = Column(JSON)
    feature_importances = Column(JSON)
    scored_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("CreditCase", back_populates="ml_scores")

    def __repr__(self):
        return f"<MLScore Grade={self.credit_grade} PD={self.pd_score} [{self.decision}]>"


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("credit_cases.id"), nullable=False)
    agent_name = Column(String(50))
    step_name = Column(String(100))
    thought = Column(Text)
    action = Column(Text)
    observation = Column(Text)
    duration_ms = Column(Integer)
    status = Column(String(20))
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("CreditCase", back_populates="agent_logs")

    def __repr__(self):
        return f"<AgentLog {self.agent_name}:{self.step_name} [{self.status}]>"


class CAMDocument(Base):
    __tablename__ = "cam_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("credit_cases.id"), nullable=False)
    version = Column(Integer, default=1)
    cam_json = Column(JSON)
    pdf_path = Column(String(500))
    word_count = Column(Integer)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("CreditCase", back_populates="cam_documents")

    def __repr__(self):
        return f"<CAMDocument v{self.version} words={self.word_count}>"


class EarlyWarningSignal(Base):
    __tablename__ = "early_warning_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("credit_cases.id"), nullable=False)
    signal_type = Column(String(50))
    severity = Column(String(10))
    description = Column(Text)
    triggered_by = Column(String(100))
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("CreditCase", back_populates="early_warnings")

    def __repr__(self):
        return f"<EWS [{self.severity}] {self.signal_type}>"
