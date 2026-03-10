"""Data Ingestor Agent — pulls and parses all data sources."""
import duckdb
import hashlib
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


def _company_seed(name: str) -> float:
    """Return a deterministic 0-1 float from company name for consistent risk variation."""
    h = int(hashlib.md5(name.lower().strip().encode()).hexdigest(), 16)
    return (h % 10000) / 10000.0

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
        meta = self.mock_mca_lookup(state.get("cin", ""), company_name=company)
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
        existing = state.get("collateral_data") or {}
        state["collateral_data"] = existing if existing else self._default_collateral(company)

        # 5. Macro data
        await _emit(case_id, "Fetching macro-economic indicators...", "GET /macro/indicators")
        state["macro_data"] = self._macro_data(state.get("industry_code", ""), company_name=company)
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

    def mock_mca_lookup(self, cin: str, company_name: str = "") -> dict:
        """Return mock MCA company data — varies by company name."""
        s = _company_seed(company_name or cin)
        # s < 0.3 = weak company, 0.3-0.7 = average, > 0.7 = strong
        years_op = int(3 + s * 20)  # 3-23 years
        mgmt_quality = max(2, min(9, int(3 + s * 6)))  # 3-9
        promoter_hold = int(30 + s * 45)  # 30-75%
        promoter_pledge = int(max(0, 40 - s * 45))  # 0-40%
        return {
            "company_name": company_name or "Company",
            "cin": cin or "U72200TG2015PTC123456",
            "date_of_incorporation": f"{2024 - years_op}-03-15",
            "registered_address": "Hyderabad, Telangana",
            "authorized_capital": 50000000,
            "paid_up_capital": 25000000,
            "company_status": "ACTIVE",
            "industry_risk_score": max(2, min(9, int(3 + s * 6))),
            "years_in_operation": years_op,
            "management_quality_score": mgmt_quality,
            "customer_concentration_hhi": round(0.30 - s * 0.22, 2),  # 0.08-0.30 (lower is better)
            "geographic_diversification": max(2, min(8, int(2 + s * 6))),
            "export_revenue_pct": round(s * 0.30, 2),
            "related_party_txn_ratio": round(max(0.01, 0.15 - s * 0.12), 2),
            "auditor_quality_score": max(1, min(5, int(1 + s * 4))),
            "qualified_audit_flag": 1 if s < 0.25 else 0,
            "promoter_holding_pct": promoter_hold,
            "promoter_pledge_pct": promoter_pledge,
            "board_independence_ratio": round(0.15 + s * 0.35, 2),
            "is_listed": 1 if s > 0.6 else 0,
            "group_strength_score": max(2, min(9, int(2 + s * 7))),
            "directors": [
                {"name": "Rajesh Kumar", "din": "07123456", "designation": "Managing Director"},
                {"name": "Priya Sharma", "din": "08234567", "designation": "Director"},
            ],
            "charges": [
                {"charge_id": "CHG-001", "holder": "State Bank of India", "amount": 150000000, "status": "OPEN"},
            ],
        }

    def _mock_bureau_data(self, company_name: str) -> dict:
        s = _company_seed(company_name)
        cibil = int(580 + s * 220)  # 580-800
        dpd_90 = max(0, int(4 - s * 6))  # 0-4
        dpd_60 = max(0, int(3 - s * 4))  # 0-3
        dpd_30 = max(0, int(5 - s * 5))  # 0-5
        dpd_0 = 12 - dpd_90 - dpd_60 - dpd_30
        utilization = round(max(0.15, 0.85 - s * 0.55), 2)  # 0.30-0.85
        return {
            "cibil_score": cibil,
            "cibil_score_normalized": round(cibil / 990, 3),
            "existing_loan_utilization": utilization,
            "dpd_0_count": max(0, dpd_0),
            "dpd_30_count": dpd_30,
            "dpd_60_count": dpd_60,
            "dpd_90_count": dpd_90,
            "loan_enquiries_6m": max(0, int(6 - s * 5)),  # 1-6
            "unsecured_debt_ratio": round(max(0.05, 0.45 - s * 0.35), 2),
            "bureau_vintage_years": int(2 + s * 10),
        }

    def _default_collateral(self, company_name: str = "") -> dict:
        s = _company_seed(company_name) if company_name else 0.5
        coverage = round(0.7 + s * 1.0, 2)  # 0.7-1.7
        ltv = round(max(0.40, 0.90 - s * 0.35), 2)  # 0.55-0.90
        ctype_score = max(1, min(5, int(1 + s * 4)))
        return {
            "ltv_ratio": ltv,
            "collateral_type": "immovable_property" if s > 0.4 else "movable_assets",
            "collateral_type_score": ctype_score,
            "collateral_coverage_ratio": coverage,
            "guarantor_nw_ratio": round(0.3 + s * 0.7, 2),
            "sarfaesi_applicable": 1 if s > 0.35 else 0,
            "collateral_value_to_loan": coverage,
            "number_of_collaterals": max(1, int(1 + s * 3)),
            "collateral_age_years": max(1, int(2 + (1 - s) * 12)),
        }

    def _macro_data(self, nic_code: str, company_name: str = "") -> dict:
        s = _company_seed(company_name or nic_code)
        return {
            "industry_npl_rate": round(0.02 + (1 - s) * 0.08, 3),  # 0.02-0.10
            "gdp_growth_rate": round(0.04 + s * 0.04, 3),
            "sector_credit_growth": round(0.04 + s * 0.08, 3),
            "input_cost_inflation": round(0.02 + (1 - s) * 0.06, 3),
            "industry_leverage_median": round(1.0 + (1 - s) * 1.0, 2),
            "commodity_exposure_score": max(1, min(8, int(2 + (1 - s) * 6))),
            "regulatory_environment_score": max(3, min(9, int(3 + s * 6))),
            "industry_growth_rate": round(0.03 + s * 0.10, 3),
            "interest_rate_sensitivity": max(1, min(8, int(2 + (1 - s) * 6))),
            "fx_exposure_score": max(1, min(7, int(1 + (1 - s) * 5))),
        }

    def _default_spreads(self, company_name: str) -> list:
        """Generate financial spreads that vary by company risk profile."""
        s = _company_seed(company_name)
        # s < 0.3 = distressed, 0.3-0.6 = average, > 0.6 = strong
        base_rev = int(100000000 + s * 800000000)  # 10Cr - 90Cr
        spreads = []
        for i, year in enumerate(["FY2022", "FY2023", "FY2024", "FY2025", "FY2026"]):
            # Growth varies: distressed companies may shrink
            if s < 0.3:
                growth_rate = -0.05 + i * 0.01  # negative to slightly positive
            elif s < 0.6:
                growth_rate = 0.05 + i * 0.015
            else:
                growth_rate = 0.10 + i * 0.02
            rev = base_rev * (1 + growth_rate) ** i

            ebitda_pct = max(0.05, 0.08 + s * 0.18 + i * 0.005)  # 8-26% margin
            pat_pct = max(0.01, ebitda_pct * 0.4)
            de_ratio = round(max(0.3, 2.5 - s * 2.2 - i * 0.02), 4)  # 0.3-2.5
            dscr = round(max(0.6, 0.7 + s * 1.8 + i * 0.05), 4)  # 0.7-2.5
            cr = round(max(0.8, 0.9 + s * 1.0 + i * 0.03), 4)  # 0.9-1.9

            spreads.append({
                "fiscal_year": year, "period_type": "ANNUAL",
                "revenue": round(rev, 2),
                "gross_profit": round(rev * (0.15 + s * 0.25), 2),
                "ebitda": round(rev * ebitda_pct, 2),
                "ebit": round(rev * ebitda_pct * 0.85, 2),
                "pbt": round(rev * ebitda_pct * 0.65, 2),
                "pat": round(rev * pat_pct, 2),
                "total_assets": round(rev * (1.2 + (1 - s) * 0.8), 2),
                "total_debt": round(rev * de_ratio * 0.5, 2),
                "equity": round(rev * 0.5, 2),
                "current_assets": round(rev * (0.25 + s * 0.25), 2),
                "current_liabilities": round(rev * (0.25 + (1 - s) * 0.15), 2),
                "cash_equivalents": round(rev * (0.02 + s * 0.08), 2),
                "cfo": round(rev * (0.02 + s * 0.12), 2),
                "cfi": round(rev * -0.08, 2),
                "cff": round(rev * -0.03, 2),
                "current_ratio": cr,
                "debt_equity_ratio": de_ratio,
                "dscr": dscr,
                "interest_coverage": round(max(1.0, 1.5 + s * 3.5 + i * 0.2), 4),
                "gross_margin": round(0.15 + s * 0.25, 4),
                "ebitda_margin": round(ebitda_pct, 4),
                "pat_margin": round(pat_pct, 4),
                "roce": round(0.05 + s * 0.15, 4),
                "roe": round(0.04 + s * 0.14, 4),
                "asset_turnover": round(0.35 + s * 0.35, 4),
                "debtor_days": max(30, int(90 - s * 45)),
                "creditor_days": int(30 + (1 - s) * 30),
                "inventory_days": max(15, int(75 - s * 40)),
            })
        return spreads
