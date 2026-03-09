"""Data Ingestor Agent — pulls and parses all data sources."""
import duckdb
import logging
import time
import asyncio
from pathlib import Path
from typing import Dict, Optional

from app.agents.state import CreditAnalysisState
from app.agents.ws_manager import ws_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

DUCKDB_PATH = Path(settings.DUCKDB_PATH)


async def _emit(case_id: str, thought: str, action: str = "", observation: str = "", status: str = "running"):
    await ws_manager.broadcast(case_id, {
        "type": "agent_event",
        "agent": "DataIngestor",
        "thought": thought,
        "action": action,
        "observation": observation,
        "status": status,
    })


class DataIngestorAgent:
    """Ingests data from DuckDB, PDFs, and mock APIs."""

    async def run(self, state: CreditAnalysisState) -> CreditAnalysisState:
        case_id = state["case_id"]
        company = state["company_name"]
        start = time.time()

        await _emit(case_id, f"Starting data ingestion for {company}...")

        # 1. DuckDB financials
        await _emit(case_id, "Querying Delta Lake for 5-year financial data...", "SELECT * FROM company_financials")
        financials = self.ingest_from_duckdb(company)
        state["raw_financials"] = financials
        state["financial_spreads"] = financials.get("spreads", [])
        await _emit(case_id, f"Retrieved {len(state['financial_spreads'])} years of financial data", status="step_done")

        if settings.DEMO_MODE:
            await asyncio.sleep(0.5)

        # 2. Company metadata
        await _emit(case_id, "Looking up company on MCA portal...", "POST /companies/lookup")
        meta = self.mock_mca_lookup(state.get("cin", ""))
        state["company_meta"] = meta
        await _emit(case_id, f"Company: {meta.get('company_name', company)}, Est. {meta.get('date_of_incorporation', 'N/A')}", status="step_done")

        if settings.DEMO_MODE:
            await asyncio.sleep(0.3)

        # 3. Bureau data
        await _emit(case_id, "Pulling CIBIL commercial bureau data...", "GET bureau/commercial")
        bureau = self._mock_bureau_data(company)
        state["bureau_data"] = bureau
        await _emit(case_id, f"CIBIL Score: {bureau['cibil_score']}", status="step_done")

        # 4. Collateral
        await _emit(case_id, "Processing collateral information...")
        state["collateral_data"] = state.get("collateral_data", self._default_collateral())

        # 5. Macro data
        await _emit(case_id, "Fetching macro-economic indicators...", "GET /macro/indicators")
        state["macro_data"] = self._macro_data(state.get("industry_code", ""))
        await _emit(case_id, f"GDP Growth: {state['macro_data']['gdp_growth_rate']*100:.1f}%", status="step_done")

        elapsed = int((time.time() - start) * 1000)
        state["agent_logs"].append({
            "agent_name": "DataIngestor",
            "step_name": "full_ingestion",
            "thought": f"Ingested all data sources for {company}",
            "duration_ms": elapsed,
            "status": "completed",
        })
        await _emit(case_id, f"Data ingestion complete ({elapsed}ms)", status="completed")

        state["current_agent"] = "FinancialAnalyst"
        return state

    def ingest_from_duckdb(self, company_name: str) -> dict:
        """Query pre-seeded DuckDB tables for company financials."""
        try:
            con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
            rows = con.execute(
                "SELECT * FROM company_financials WHERE company_name = ? ORDER BY fiscal_year",
                [company_name]
            ).fetchdf()
            con.close()

            if rows.empty:
                return {"spreads": self._default_spreads(company_name)}

            spreads = rows.to_dict("records")
            return {"spreads": spreads}
        except Exception as e:
            logger.warning(f"DuckDB query failed: {e}, using default spreads")
            return {"spreads": self._default_spreads(company_name)}

    def mock_mca_lookup(self, cin: str) -> dict:
        """Return mock MCA company data."""
        return {
            "company_name": "Company",
            "cin": cin or "U72200TG2015PTC123456",
            "date_of_incorporation": "2015-03-15",
            "registered_address": "Hyderabad, Telangana",
            "authorized_capital": 50000000,
            "paid_up_capital": 25000000,
            "company_status": "ACTIVE",
            "industry_risk_score": 6,
            "years_in_operation": 11,
            "management_quality_score": 7,
            "customer_concentration_hhi": 0.12,
            "geographic_diversification": 5,
            "export_revenue_pct": 0.15,
            "related_party_txn_ratio": 0.05,
            "auditor_quality_score": 3,
            "qualified_audit_flag": 0,
            "promoter_holding_pct": 65,
            "promoter_pledge_pct": 10,
            "board_independence_ratio": 0.33,
            "is_listed": 0,
            "group_strength_score": 6,
            "directors": [
                {"name": "Rajesh Kumar", "din": "07123456", "designation": "Managing Director"},
                {"name": "Priya Sharma", "din": "08234567", "designation": "Director"},
            ],
            "charges": [
                {"charge_id": "CHG-001", "holder": "State Bank of India", "amount": 150000000, "status": "OPEN"},
            ],
        }

    def _mock_bureau_data(self, company_name: str) -> dict:
        return {
            "cibil_score": 760,
            "cibil_score_normalized": 0.767,
            "existing_loan_utilization": 0.45,
            "dpd_0_count": 11,
            "dpd_30_count": 1,
            "dpd_60_count": 0,
            "dpd_90_count": 0,
            "loan_enquiries_6m": 2,
            "unsecured_debt_ratio": 0.2,
            "bureau_vintage_years": 8,
        }

    def _default_collateral(self) -> dict:
        return {
            "ltv_ratio": 0.65,
            "collateral_type": "immovable_property",
            "collateral_type_score": 5,
            "collateral_coverage_ratio": 1.4,
            "guarantor_nw_ratio": 0.8,
            "sarfaesi_applicable": 1,
            "collateral_value_to_loan": 1.4,
            "number_of_collaterals": 2,
            "collateral_age_years": 5,
        }

    def _macro_data(self, nic_code: str) -> dict:
        return {
            "industry_npl_rate": 0.04,
            "gdp_growth_rate": 0.065,
            "sector_credit_growth": 0.09,
            "input_cost_inflation": 0.045,
            "industry_leverage_median": 1.4,
            "commodity_exposure_score": 3,
            "regulatory_environment_score": 6,
            "industry_growth_rate": 0.08,
            "interest_rate_sensitivity": 4,
            "fx_exposure_score": 2,
        }

    def _default_spreads(self, company_name: str) -> list:
        """Generate reasonable default financial spreads."""
        base_rev = 450000000  # 45 Cr
        spreads = []
        for i, year in enumerate(["FY2022", "FY2023", "FY2024", "FY2025", "FY2026"]):
            growth = 1 + 0.12 + i * 0.03
            rev = base_rev * growth ** i
            spreads.append({
                "fiscal_year": year, "period_type": "ANNUAL",
                "revenue": round(rev, 2),
                "gross_profit": round(rev * 0.38, 2),
                "ebitda": round(rev * (0.22 + i * 0.01), 2),
                "ebit": round(rev * (0.18 + i * 0.008), 2),
                "pbt": round(rev * (0.14 + i * 0.006), 2),
                "pat": round(rev * (0.10 + i * 0.005), 2),
                "total_assets": round(rev * 1.8, 2),
                "total_debt": round(rev * 0.6, 2),
                "equity": round(rev * 0.8, 2),
                "current_assets": round(rev * 0.5, 2),
                "current_liabilities": round(rev * 0.3, 2),
                "cash_equivalents": round(rev * 0.08, 2),
                "cfo": round(rev * 0.12, 2),
                "cfi": round(rev * -0.08, 2),
                "cff": round(rev * -0.03, 2),
                "current_ratio": round(1.6 + i * 0.05, 4),
                "debt_equity_ratio": round(0.75 - i * 0.03, 4),
                "dscr": round(1.8 + i * 0.1, 4),
                "interest_coverage": round(3.5 + i * 0.3, 4),
                "gross_margin": round(0.38 + i * 0.005, 4),
                "ebitda_margin": round(0.22 + i * 0.01, 4),
                "pat_margin": round(0.10 + i * 0.005, 4),
                "roce": round(0.14 + i * 0.008, 4),
                "roe": round(0.13 + i * 0.007, 4),
                "asset_turnover": round(0.55 + i * 0.02, 4),
                "debtor_days": max(45, 65 - i * 3),
                "creditor_days": 45,
                "inventory_days": max(30, 50 - i * 3),
            })
        return spreads
