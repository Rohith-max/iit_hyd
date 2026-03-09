"""Feature Engineering Pipeline - 80+ features across 6 categories."""
import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass


class FeatureEngineer:
    """Computes 80+ credit features from financial and non-financial data."""

    def compute_all_features(
        self,
        financial_spreads: List[dict],
        company_meta: dict,
        bureau_data: dict,
        web_signals: dict,
        collateral_data: Optional[dict] = None,
        macro_data: Optional[dict] = None,
    ) -> Dict[str, float]:
        features = {}
        features.update(self._financial_health_features(financial_spreads))
        features.update(self._business_quality_features(company_meta))
        features.update(self._credit_behaviour_features(bureau_data))
        features.update(self._collateral_features(collateral_data or {}))
        features.update(self._macro_industry_features(macro_data or {}, company_meta.get("industry_code", "")))
        features.update(self._web_intelligence_features(web_signals))
        # Median imputation for missing
        for k, v in features.items():
            if v is None or (isinstance(v, float) and np.isnan(v)):
                features[k] = 0.0
        return features

    def _financial_health_features(self, spreads: List[dict]) -> Dict[str, float]:
        features = {}
        if not spreads:
            return {f"fin_{i}": 0.0 for i in range(30)}

        spreads = sorted(spreads, key=lambda x: x.get("fiscal_year", ""))
        latest = spreads[-1]
        n = len(spreads)

        # Revenue and growth
        revenues = [float(s.get("revenue", 0) or 0) for s in spreads]
        ebitdas = [float(s.get("ebitda", 0) or 0) for s in spreads]
        pats = [float(s.get("pat", 0) or 0) for s in spreads]

        features["revenue_latest"] = revenues[-1]
        features["ebitda_latest"] = ebitdas[-1]
        features["pat_latest"] = pats[-1]

        # CAGR calculations
        features["revenue_cagr_5y"] = self._cagr(revenues[0], revenues[-1], n) if revenues[0] > 0 else 0.0
        features["ebitda_cagr_5y"] = self._cagr(abs(ebitdas[0]) if ebitdas[0] > 0 else 1, max(ebitdas[-1], 0.01), n)
        features["pat_cagr_5y"] = self._cagr(abs(pats[0]) if pats[0] > 0 else 1, max(pats[-1], 0.01), n)

        # YoY deltas
        if n >= 2:
            features["revenue_yoy"] = (revenues[-1] - revenues[-2]) / max(abs(revenues[-2]), 1) if revenues[-2] else 0
            features["ebitda_yoy"] = (ebitdas[-1] - ebitdas[-2]) / max(abs(ebitdas[-2]), 1) if ebitdas[-2] else 0
            features["pat_yoy"] = (pats[-1] - pats[-2]) / max(abs(pats[-2]), 1) if pats[-2] else 0
        else:
            features["revenue_yoy"] = 0.0
            features["ebitda_yoy"] = 0.0
            features["pat_yoy"] = 0.0

        # Trend slope
        features["revenue_trend_slope"] = self._trend_slope(revenues)
        features["ebitda_trend_slope"] = self._trend_slope(ebitdas)

        # Key ratios from latest
        features["current_ratio"] = float(latest.get("current_ratio", 0) or 0)
        features["debt_equity_ratio"] = float(latest.get("debt_equity_ratio", 0) or 0)
        features["dscr"] = float(latest.get("dscr", 0) or 0)
        features["interest_coverage"] = float(latest.get("interest_coverage", 0) or 0)
        features["gross_margin"] = float(latest.get("gross_margin", 0) or 0)
        features["ebitda_margin"] = float(latest.get("ebitda_margin", 0) or 0)
        features["pat_margin"] = float(latest.get("pat_margin", 0) or 0)
        features["roce"] = float(latest.get("roce", 0) or 0)
        features["roe"] = float(latest.get("roe", 0) or 0)
        features["asset_turnover"] = float(latest.get("asset_turnover", 0) or 0)

        # DSCR 3-year average
        dscrs = [float(s.get("dscr", 0) or 0) for s in spreads[-3:]]
        features["dscr_3y_avg"] = np.mean(dscrs) if dscrs else 0.0

        # Working capital
        features["debtor_days"] = float(latest.get("debtor_days", 0) or 0)
        features["creditor_days"] = float(latest.get("creditor_days", 0) or 0)
        features["inventory_days"] = float(latest.get("inventory_days", 0) or 0)
        features["cash_conversion_cycle"] = self.ccc_calculation(
            features["debtor_days"], features["inventory_days"], features["creditor_days"]
        )

        # Net debt / EBITDA
        total_debt = float(latest.get("total_debt", 0) or 0)
        cash = float(latest.get("cash_equivalents", 0) or 0)
        features["net_debt_to_ebitda"] = (total_debt - cash) / max(ebitdas[-1], 1) if ebitdas[-1] > 0 else 10.0

        # Altman, Piotroski, Beneish
        features["altman_z_score"] = self.altman_z_score(latest)
        features["piotroski_f_score"] = self.piotroski_f_score(spreads)
        features["beneish_m_score"] = self.beneish_m_score(spreads)

        # Fixed charge coverage
        ebit = float(latest.get("ebit", 0) or 0)
        features["fixed_charge_coverage"] = ebit / max(total_debt * 0.1, 1)

        return features

    def _business_quality_features(self, meta: dict) -> Dict[str, float]:
        features = {}
        features["industry_risk_score"] = float(meta.get("industry_risk_score", 5))
        features["years_in_operation"] = float(meta.get("years_in_operation", 10))
        features["management_quality_score"] = float(meta.get("management_quality_score", 5))
        features["customer_concentration_hhi"] = float(meta.get("customer_concentration_hhi", 0.1))
        features["geographic_diversification"] = float(meta.get("geographic_diversification", 3))
        features["export_revenue_pct"] = float(meta.get("export_revenue_pct", 0))
        features["related_party_txn_ratio"] = float(meta.get("related_party_txn_ratio", 0))
        features["auditor_quality_score"] = float(meta.get("auditor_quality_score", 3))
        features["qualified_audit_flag"] = float(meta.get("qualified_audit_flag", 0))
        features["promoter_holding_pct"] = float(meta.get("promoter_holding_pct", 60))
        features["promoter_pledge_pct"] = float(meta.get("promoter_pledge_pct", 0))
        features["board_independence_ratio"] = float(meta.get("board_independence_ratio", 0.33))
        features["company_age_log"] = np.log1p(features["years_in_operation"])
        features["is_listed"] = float(meta.get("is_listed", 0))
        features["group_strength_score"] = float(meta.get("group_strength_score", 5))
        return features

    def _credit_behaviour_features(self, bureau: dict) -> Dict[str, float]:
        features = {}
        features["cibil_score"] = float(bureau.get("cibil_score", 700))
        features["cibil_score_normalized"] = (features["cibil_score"] - 300) / 600
        features["existing_loan_utilization"] = float(bureau.get("existing_loan_utilization", 0.5))
        features["dpd_0_count"] = float(bureau.get("dpd_0_count", 12))
        features["dpd_30_count"] = float(bureau.get("dpd_30_count", 0))
        features["dpd_60_count"] = float(bureau.get("dpd_60_count", 0))
        features["dpd_90_count"] = float(bureau.get("dpd_90_count", 0))
        features["loan_enquiries_6m"] = float(bureau.get("loan_enquiries_6m", 2))
        features["unsecured_debt_ratio"] = float(bureau.get("unsecured_debt_ratio", 0.3))
        features["bureau_vintage_years"] = float(bureau.get("bureau_vintage_years", 5))
        return features

    def _collateral_features(self, collateral: dict) -> Dict[str, float]:
        features = {}
        features["ltv_ratio"] = float(collateral.get("ltv_ratio", 0.7))
        type_map = {"immovable_property": 5, "financial_assets": 4, "movable": 3, "none": 0}
        features["collateral_type_score"] = float(type_map.get(collateral.get("collateral_type", "none"), 0))
        features["collateral_coverage_ratio"] = float(collateral.get("collateral_coverage_ratio", 1.0))
        features["guarantor_nw_ratio"] = float(collateral.get("guarantor_nw_ratio", 0))
        features["sarfaesi_applicable"] = float(collateral.get("sarfaesi_applicable", 1))
        features["collateral_value_to_loan"] = float(collateral.get("collateral_value_to_loan", 1.2))
        features["number_of_collaterals"] = float(collateral.get("number_of_collaterals", 1))
        features["collateral_age_years"] = float(collateral.get("collateral_age_years", 5))
        return features

    def _macro_industry_features(self, macro: dict, nic_code: str) -> Dict[str, float]:
        features = {}
        features["industry_npl_rate"] = float(macro.get("industry_npl_rate", 0.05))
        features["gdp_growth_rate"] = float(macro.get("gdp_growth_rate", 0.065))
        features["sector_credit_growth"] = float(macro.get("sector_credit_growth", 0.08))
        features["input_cost_inflation"] = float(macro.get("input_cost_inflation", 0.05))
        features["industry_leverage_median"] = float(macro.get("industry_leverage_median", 1.5))
        features["commodity_exposure_score"] = float(macro.get("commodity_exposure_score", 3))
        features["regulatory_environment_score"] = float(macro.get("regulatory_environment_score", 5))
        features["industry_growth_rate"] = float(macro.get("industry_growth_rate", 0.07))
        features["interest_rate_sensitivity"] = float(macro.get("interest_rate_sensitivity", 5))
        features["fx_exposure_score"] = float(macro.get("fx_exposure_score", 2))
        return features

    def _web_intelligence_features(self, web: dict) -> Dict[str, float]:
        features = {}
        features["news_sentiment_score"] = float(web.get("news_sentiment_score", 0))
        features["regulatory_action_flag"] = float(web.get("regulatory_action_flag", 0))
        features["litigation_score"] = float(web.get("litigation_score", 0))
        features["mgmt_change_velocity"] = float(web.get("mgmt_change_velocity", 0))
        features["social_controversy_score"] = float(web.get("social_controversy_score", 0))
        features["gst_compliance_rate"] = float(web.get("gst_compliance_rate", 0.95))
        features["roc_compliance_score"] = float(web.get("roc_compliance_score", 8))
        return features

    def altman_z_score(self, financials: dict) -> float:
        """Modified Altman Z'-Score for private companies."""
        ta = float(financials.get("total_assets", 1) or 1)
        ca = float(financials.get("current_assets", 0) or 0)
        cl = float(financials.get("current_liabilities", 0) or 0)
        equity = float(financials.get("equity", 0) or 0)
        ebit = float(financials.get("ebit", 0) or 0)
        revenue = float(financials.get("revenue", 0) or 0)
        total_debt = float(financials.get("total_debt", 0) or 0)
        pat = float(financials.get("pat", 0) or 0)

        wc = ca - cl
        retained_earnings = equity * 0.7  # Approximation
        total_liabilities = ta - equity if equity < ta else max(total_debt, 1)

        x1 = wc / ta
        x2 = retained_earnings / ta
        x3 = ebit / ta
        x4 = equity / max(total_liabilities, 1)
        x5 = revenue / ta

        return 0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5

    def piotroski_f_score(self, spreads: List[dict]) -> float:
        """9-point Piotroski F-Score."""
        if len(spreads) < 2:
            return 5.0

        curr = spreads[-1]
        prev = spreads[-2]
        score = 0

        ta_c = float(curr.get("total_assets", 1) or 1)
        ta_p = float(prev.get("total_assets", 1) or 1)
        pat_c = float(curr.get("pat", 0) or 0)
        pat_p = float(prev.get("pat", 0) or 0)
        cfo_c = float(curr.get("cfo", 0) or 0)
        equity_c = float(curr.get("equity", 1) or 1)
        equity_p = float(prev.get("equity", 1) or 1)
        debt_c = float(curr.get("total_debt", 0) or 0)
        debt_p = float(prev.get("total_debt", 0) or 0)
        ca_c = float(curr.get("current_assets", 0) or 0)
        cl_c = float(curr.get("current_liabilities", 1) or 1)
        ca_p = float(prev.get("current_assets", 0) or 0)
        cl_p = float(prev.get("current_liabilities", 1) or 1)
        rev_c = float(curr.get("revenue", 0) or 0)
        rev_p = float(prev.get("revenue", 0) or 0)
        gm_c = float(curr.get("gross_margin", 0) or 0)
        gm_p = float(prev.get("gross_margin", 0) or 0)

        roa_c = pat_c / ta_c
        roa_p = pat_p / ta_p

        # 1. ROA > 0
        if roa_c > 0: score += 1
        # 2. CFO > 0
        if cfo_c > 0: score += 1
        # 3. Delta ROA > 0
        if roa_c > roa_p: score += 1
        # 4. Accruals: CFO > PAT
        if cfo_c > pat_c: score += 1
        # 5. Delta leverage (D/E decrease)
        de_c = debt_c / max(equity_c, 1)
        de_p = debt_p / max(equity_p, 1)
        if de_c < de_p: score += 1
        # 6. Delta liquidity (current ratio increase)
        cr_c = ca_c / max(cl_c, 1)
        cr_p = ca_p / max(cl_p, 1)
        if cr_c > cr_p: score += 1
        # 7. No dilution (shares not increased) — approximate as equity growth > PAT
        if equity_c >= equity_p: score += 1
        # 8. Delta gross margin > 0
        if gm_c > gm_p: score += 1
        # 9. Delta asset turnover > 0
        at_c = rev_c / ta_c
        at_p = rev_p / ta_p
        if at_c > at_p: score += 1

        return float(score)

    def beneish_m_score(self, spreads: List[dict]) -> float:
        """Beneish M-Score for earnings manipulation detection."""
        if len(spreads) < 2:
            return -2.5  # Normal range

        curr = spreads[-1]
        prev = spreads[-2]

        rev_c = float(curr.get("revenue", 1) or 1)
        rev_p = float(prev.get("revenue", 1) or 1)
        gp_c = float(curr.get("gross_profit", 0) or 0)
        gp_p = float(prev.get("gross_profit", 0) or 0)
        ta_c = float(curr.get("total_assets", 1) or 1)
        ta_p = float(prev.get("total_assets", 1) or 1)
        ca_c = float(curr.get("current_assets", 0) or 0)
        ca_p = float(prev.get("current_assets", 0) or 0)
        pat_c = float(curr.get("pat", 0) or 0)
        cfo_c = float(curr.get("cfo", 0) or 0)
        debt_c = float(curr.get("total_debt", 0) or 0)
        debt_p = float(prev.get("total_debt", 0) or 0)
        ebit_c = float(curr.get("ebit", 0) or 0)

        # DSRI - Days Sales in Receivables Index
        dsri = 1.0  # Simplified
        # GMI - Gross Margin Index
        gm_p_ratio = gp_p / max(rev_p, 1)
        gm_c_ratio = gp_c / max(rev_c, 1)
        gmi = gm_p_ratio / max(gm_c_ratio, 0.01) if gm_c_ratio > 0 else 1.0
        # AQI - Asset Quality Index
        aqi = (1 - ca_c / max(ta_c, 1)) / max(1 - ca_p / max(ta_p, 1), 0.01)
        # SGI - Sales Growth Index
        sgi = rev_c / max(rev_p, 1)
        # DEPI - Depreciation Index
        depi = 1.0  # Simplified
        # SGAI - SGA Index
        sgai = 1.0  # Simplified
        # Accruals / Total Assets
        tata = (pat_c - cfo_c) / max(ta_c, 1)
        # LVGI - Leverage Index
        lev_c = debt_c / max(ta_c, 1)
        lev_p = debt_p / max(ta_p, 1)
        lvgi = lev_c / max(lev_p, 0.01) if lev_p > 0 else 1.0

        m_score = (
            -4.84
            + 0.920 * dsri
            + 0.528 * gmi
            + 0.404 * aqi
            + 0.892 * sgi
            + 0.115 * depi
            - 0.172 * sgai
            + 4.679 * tata
            - 0.327 * lvgi
        )
        return m_score

    def ccc_calculation(self, debtor_days: float, inventory_days: float, creditor_days: float) -> float:
        """Cash Conversion Cycle."""
        return debtor_days + inventory_days - creditor_days

    @staticmethod
    def _cagr(start_val: float, end_val: float, periods: int) -> float:
        if start_val <= 0 or end_val <= 0 or periods <= 1:
            return 0.0
        return (end_val / start_val) ** (1 / (periods - 1)) - 1

    @staticmethod
    def _trend_slope(values: list) -> float:
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        return float(coeffs[0])
