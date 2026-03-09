"""Financial Analyst Agent — deep financial analysis and feature engineering."""
import time
import asyncio
import logging
from typing import Dict, List

from app.agents.state import CreditAnalysisState
from app.agents.ws_manager import ws_manager
from app.ml.feature_engineering import FeatureEngineer
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _emit(case_id: str, thought: str, action: str = "", observation: str = "", status: str = "running"):
    await ws_manager.broadcast(case_id, {
        "type": "agent_event",
        "agent": "FinancialAnalyst",
        "thought": thought,
        "action": action,
        "observation": observation,
        "status": status,
    })


class FinancialAnalystAgent:
    """Performs deep financial analysis and feature engineering."""

    def __init__(self):
        self.feature_engineer = FeatureEngineer()

    async def run(self, state: CreditAnalysisState) -> CreditAnalysisState:
        case_id = state["case_id"]
        start = time.time()

        await _emit(case_id, "Starting comprehensive financial analysis...")

        spreads = state.get("financial_spreads", [])
        meta = state.get("company_meta", {})
        bureau = state.get("bureau_data", {})
        web = state.get("web_research", {})
        collateral = state.get("collateral_data", {})
        macro = state.get("macro_data", {})

        # Compute features
        await _emit(case_id, "Computing 80+ credit features across 6 categories...")
        features = self.feature_engineer.compute_all_features(
            spreads, meta, bureau, web, collateral, macro
        )
        state["ml_features"] = features

        if settings.DEMO_MODE:
            await asyncio.sleep(0.3)

        # Key metric emissions
        z_score = features.get("altman_z_score", 0)
        z_zone = "Safe Zone" if z_score > 2.9 else ("Grey Zone" if z_score > 1.23 else "Distress Zone")
        await _emit(case_id, f"Altman Z-Score: {z_score:.2f} ({z_zone})", status="metric")

        f_score = features.get("piotroski_f_score", 0)
        await _emit(case_id, f"Piotroski F-Score: {f_score:.0f}/9", status="metric")

        m_score = features.get("beneish_m_score", -2.5)
        m_zone = "Normal" if m_score < -1.78 else "Manipulation Risk"
        await _emit(case_id, f"Beneish M-Score: {m_score:.2f} ({m_zone})", status="metric")

        dscr = features.get("dscr", 0)
        await _emit(case_id, f"DSCR: {dscr:.2f}x", status="metric")

        ccc = features.get("cash_conversion_cycle", 0)
        await _emit(case_id, f"Cash Conversion Cycle: {ccc:.0f} days", status="metric")

        if settings.DEMO_MODE:
            await asyncio.sleep(0.3)

        # Anomaly detection
        await _emit(case_id, "Running anomaly detection on financial trends...")
        anomalies = self.detect_anomalies(spreads)
        state["processed_financials"] = {
            "features": features,
            "anomalies": anomalies,
        }

        for a in anomalies:
            await _emit(case_id, f"⚠ Anomaly: {a['description']}", status="warning")

        if settings.DEMO_MODE:
            await asyncio.sleep(0.3)

        # Peer comparison
        await _emit(case_id, "Running peer comparison against industry benchmarks...")
        peers = self.peer_comparison(state.get("industry_code", ""), features)
        state["processed_financials"]["peer_comparison"] = peers
        await _emit(case_id, f"Peer analysis complete: company scores above median on {peers.get('above_median_count', 0)} of 8 metrics", status="step_done")

        # DCF
        await _emit(case_id, "Running 3-scenario DCF analysis (base / stress / upside)...")
        dcf = self.run_dcf_scenarios(spreads)
        state["processed_financials"]["dcf_scenarios"] = dcf
        await _emit(case_id, f"DCF Fair Value Range: ₹{dcf['stress']['fair_value']/10000000:.1f}Cr - ₹{dcf['upside']['fair_value']/10000000:.1f}Cr", status="step_done")

        elapsed = int((time.time() - start) * 1000)
        state["agent_logs"].append({
            "agent_name": "FinancialAnalyst",
            "step_name": "full_analysis",
            "thought": f"Completed financial analysis with {len(features)} features",
            "duration_ms": elapsed,
            "status": "completed",
        })
        await _emit(case_id, f"Financial analysis complete ({elapsed}ms)", status="completed")
        state["current_agent"] = "WebResearch"
        return state

    def detect_anomalies(self, spreads: List[dict]) -> List[dict]:
        """Detect financial anomalies in the data."""
        anomalies = []
        if len(spreads) < 2:
            return anomalies

        latest = spreads[-1]
        prev = spreads[-2]

        rev_c = float(latest.get("revenue", 0) or 0)
        rev_p = float(prev.get("revenue", 0) or 0)
        cfo_c = float(latest.get("cfo", 0) or 0)
        pat_c = float(latest.get("pat", 0) or 0)

        # Revenue-to-cash-flow divergence
        if rev_c > rev_p * 1.15 and cfo_c < float(prev.get("cfo", 0) or 0):
            anomalies.append({
                "type": "revenue_cf_divergence",
                "severity": "AMBER",
                "description": "Revenue growing but operating cash flows declining — potential receivables quality issue",
            })

        # Receivables growing faster than revenue
        dd_c = float(latest.get("debtor_days", 0) or 0)
        dd_p = float(prev.get("debtor_days", 0) or 0)
        if dd_c > dd_p * 1.2 and dd_c > 90:
            anomalies.append({
                "type": "receivables_spike",
                "severity": "AMBER",
                "description": f"Debtor days increased from {dd_p:.0f} to {dd_c:.0f} — potential collection issues",
            })

        # Inventory spike
        id_c = float(latest.get("inventory_days", 0) or 0)
        id_p = float(prev.get("inventory_days", 0) or 0)
        if id_c > id_p * 1.3 and id_c > 60:
            anomalies.append({
                "type": "inventory_spike",
                "severity": "AMBER",
                "description": f"Inventory days jumped from {id_p:.0f} to {id_c:.0f} — potential obsolescence or demand issues",
            })

        # Accruals quality
        if pat_c > 0 and cfo_c < pat_c * 0.5:
            anomalies.append({
                "type": "low_accruals_quality",
                "severity": "AMBER",
                "description": "Operating cash flow significantly below PAT — earnings quality concern",
            })

        return anomalies

    def peer_comparison(self, nic_code: str, features: dict) -> dict:
        """Compare against industry median benchmarks."""
        # Industry medians (configurable per NIC code normally from DuckDB)
        medians = {
            "current_ratio": 1.5,
            "debt_equity_ratio": 1.3,
            "dscr": 1.8,
            "ebitda_margin": 0.18,
            "roe": 0.12,
            "asset_turnover": 1.0,
            "interest_coverage": 3.0,
            "pat_margin": 0.08,
        }

        comparison = {}
        above_count = 0
        for metric, median in medians.items():
            val = features.get(metric, 0)
            # For debt_equity, lower is better
            if metric == "debt_equity_ratio":
                is_above = val < median
            else:
                is_above = val > median
            if is_above:
                above_count += 1
            comparison[metric] = {
                "company_value": round(val, 4),
                "industry_median": median,
                "position": "above" if is_above else "below",
            }

        return {"metrics": comparison, "above_median_count": above_count}

    def run_dcf_scenarios(self, spreads: List[dict]) -> dict:
        """Run 3-scenario DCF: base, stress, upside."""
        if not spreads:
            return {"base": {"fair_value": 0}, "stress": {"fair_value": 0}, "upside": {"fair_value": 0}}

        latest_ebitda = float(spreads[-1].get("ebitda", 0) or 0)

        scenarios = {}
        for name, growth_rate, discount_rate in [
            ("base", 0.10, 0.12),
            ("stress", 0.03, 0.15),
            ("upside", 0.18, 0.10),
        ]:
            fcf_base = latest_ebitda * 0.65
            npv = 0
            for year in range(1, 6):
                fcf = fcf_base * (1 + growth_rate) ** year
                npv += fcf / (1 + discount_rate) ** year
            # Terminal value
            terminal = (fcf_base * (1 + growth_rate) ** 5 * (1 + 0.03)) / (discount_rate - 0.03)
            npv += terminal / (1 + discount_rate) ** 5
            scenarios[name] = {
                "fair_value": round(npv, 2),
                "growth_rate": growth_rate,
                "discount_rate": discount_rate,
                "implied_ev_ebitda": round(npv / max(latest_ebitda, 1), 1),
            }

        return scenarios
