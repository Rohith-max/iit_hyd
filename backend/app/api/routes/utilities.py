"""Utility API routes — company lookup, benchmarks, dashboard stats."""
from fastapi import APIRouter
from app.api.schemas import CompanyLookupRequest, CompanyLookupResponse, DashboardStatsResponse, IndustryBenchmarkResponse

router = APIRouter(prefix="/api/v1", tags=["utilities"])


@router.post("/companies/lookup", response_model=CompanyLookupResponse)
async def company_lookup(req: CompanyLookupRequest):
    """Mock MCA company lookup by CIN."""
    return CompanyLookupResponse(
        company_name="Rajasthan Solar Tech Pvt Ltd",
        cin=req.cin,
        date_of_incorporation="2015-03-15",
        registered_address="Plot 42, RIICO Industrial Area, Jodhpur, Rajasthan 342001",
        authorized_capital=50000000,
        paid_up_capital=25000000,
        company_status="ACTIVE",
        directors=[
            {"name": "Vikram Singh Rathore", "din": "07123456", "designation": "Managing Director", "since": "2015"},
            {"name": "Priya Mehta", "din": "08234567", "designation": "Director - Finance", "since": "2017"},
            {"name": "Dr. Arun Joshi", "din": "09345678", "designation": "Independent Director", "since": "2020"},
        ],
        charges=[
            {"charge_id": "CHG-001", "holder": "State Bank of India", "amount": 150000000, "status": "OPEN", "date": "2022-06-15"},
        ]
    )


@router.get("/industry/{nic_code}/benchmarks", response_model=IndustryBenchmarkResponse)
async def industry_benchmarks(nic_code: str):
    """Industry ratio benchmarks by NIC code."""
    benchmarks = {
        "2610": ("Solar & Renewable Energy", 1.6, 1.3, 1.9, 0.22, 0.14, 0.8, 0.03, "Positive"),
        "1711": ("Textiles", 1.4, 1.8, 1.5, 0.15, 0.10, 1.1, 0.06, "Neutral"),
        "4100": ("Real Estate", 1.2, 2.5, 1.1, 0.25, 0.08, 0.4, 0.09, "Cautious"),
    }
    data = benchmarks.get(nic_code, ("General Industry", 1.5, 1.5, 1.8, 0.18, 0.12, 1.0, 0.05, "Neutral"))
    return IndustryBenchmarkResponse(
        nic_code=nic_code,
        industry_name=data[0],
        median_current_ratio=data[1],
        median_debt_equity=data[2],
        median_dscr=data[3],
        median_ebitda_margin=data[4],
        median_roe=data[5],
        median_asset_turnover=data[6],
        npl_rate=data[7],
        sector_outlook=data[8],
    )


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def dashboard_stats():
    """Platform-level statistics."""
    return DashboardStatsResponse(
        active_cases=12,
        approved_this_month=847,
        avg_processing_time_seconds=163,
        avg_credit_score=742,
        total_processed=847,
        model_accuracy_auc=0.942,
        capital_saved="₹2.3Cr/year",
    )


@router.get("/demo/metrics")
async def demo_metrics():
    """Demo metrics endpoint."""
    return {
        "total_cases_today": 847,
        "avg_decisioning_time": "2m 43s",
        "model_accuracy_auc": 0.942,
        "capital_saved": "₹2.3Cr/year",
        "traditional_process": {"time": "3-6 weeks", "analysts": 8, "cost": "₹85,000"},
        "nexus_credit": {"time": "3 minutes", "analysts": 0, "cost": "₹12"},
    }
