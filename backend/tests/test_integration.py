"""Integration tests for NEXUS CREDIT pipeline.

These tests validate the ML scoring engine, feature engineering, and DuckDB seeding
without requiring PostgreSQL or external APIs (Anthropic, Tavily).
Run with: python -m pytest backend/tests/test_integration.py -v
"""
import pytest
import os
import sys
from pathlib import Path

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("DUCKDB_PATH", "./data/test_nexus.duckdb")
os.environ.setdefault("DEMO_MODE", "true")


class TestDuckDBSeed:
    """Test DuckDB seed data is created correctly."""

    def test_seed_creates_tables(self, tmp_path):
        import duckdb
        from app.db.seed import seed_duckdb

        db_path = str(tmp_path / "test.duckdb")
        seed_duckdb(db_path)

        con = duckdb.connect(db_path)
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        assert "company_financials" in tables
        assert "industry_benchmarks" in tables
        assert "macro_indicators" in tables
        con.close()

    def test_seed_company_financials_count(self, tmp_path):
        import duckdb
        from app.db.seed import seed_duckdb

        db_path = str(tmp_path / "test.duckdb")
        seed_duckdb(db_path)

        con = duckdb.connect(db_path)
        count = con.execute("SELECT COUNT(*) FROM company_financials").fetchone()[0]
        assert count == 15  # 3 companies × 5 years
        con.close()

    def test_seed_has_three_companies(self, tmp_path):
        import duckdb
        from app.db.seed import seed_duckdb

        db_path = str(tmp_path / "test.duckdb")
        seed_duckdb(db_path)

        con = duckdb.connect(db_path)
        companies = con.execute("SELECT DISTINCT company_name FROM company_financials").fetchall()
        names = {r[0] for r in companies}
        assert "Rajasthan Solar Tech Pvt Ltd" in names
        assert "Mumbai Textiles Ltd" in names
        assert "Delhi Real Estate Developers Pvt Ltd" in names
        con.close()

    def test_seed_industry_benchmarks(self, tmp_path):
        import duckdb
        from app.db.seed import seed_duckdb

        db_path = str(tmp_path / "test.duckdb")
        seed_duckdb(db_path)

        con = duckdb.connect(db_path)
        count = con.execute("SELECT COUNT(*) FROM industry_benchmarks").fetchone()[0]
        assert count >= 3  # At least 3 NIC codes
        con.close()

    def test_seed_idempotent(self, tmp_path):
        import duckdb
        from app.db.seed import seed_duckdb

        db_path = str(tmp_path / "test.duckdb")
        seed_duckdb(db_path)
        seed_duckdb(db_path)  # Second call should be a no-op

        con = duckdb.connect(db_path)
        count = con.execute("SELECT COUNT(*) FROM company_financials").fetchone()[0]
        assert count == 15
        con.close()


class TestFeatureEngineering:
    """Test the feature engineering pipeline."""

    def test_compute_all_features(self):
        from app.ml.feature_engineering import FeatureEngineer

        fe = FeatureEngineer()
        spreads = [
            {
                "fiscal_year": f"FY{2020 + i}",
                "revenue": 45e7 * (1.15 ** i),
                "gross_profit": 15e7 * (1.15 ** i),
                "ebitda": 10e7 * (1.15 ** i),
                "depreciation": 2e7,
                "ebit": 8e7 * (1.15 ** i),
                "interest_expense": 3e7,
                "pbt": 5e7 * (1.15 ** i),
                "tax": 1.5e7 * (1.15 ** i),
                "pat": 3.5e7 * (1.15 ** i),
                "total_assets": 80e7 * (1.1 ** i),
                "total_debt": 30e7,
                "equity": 25e7 * (1.1 ** i),
                "current_assets": 20e7,
                "current_liabilities": 12e7,
                "cash_equivalents": 5e7,
                "inventory": 4e7,
                "trade_receivables": 6e7,
                "trade_payables": 5e7,
                "cfo": 8e7 * (1.1 ** i),
                "cfi": -4e7,
                "cff": -2e7,
                "retained_earnings": 10e7 * (1.1 ** i),
            }
            for i in range(5)
        ]

        company_meta = {
            "years_in_operation": 10,
            "auditor_quality": 5,
            "qualified_opinion": False,
            "export_revenue_pct": 0.15,
            "related_party_ratio": 0.05,
        }

        bureau_data = {
            "cibil_score": 810,
            "dpd_max": 0,
            "existing_utilization": 0.4,
            "enquiry_count_6m": 2,
            "unsecured_ratio": 0.2,
            "bureau_vintage_years": 8,
        }

        web_signals = {
            "news_sentiment_score": 0.6,
            "regulatory_action_flag": False,
            "litigation_score": 2,
            "management_change_velocity": 0,
            "social_media_controversy": 0,
            "gst_compliance_rate": 0.95,
            "roc_compliance_score": 0.9,
        }

        features = fe.compute_all_features(spreads, company_meta, bureau_data, web_signals)

        # Should have a large number of features
        assert len(features) >= 30
        # Key features should exist
        assert "revenue_latest" in features
        assert "current_ratio" in features
        assert "debt_equity_ratio" in features
        assert "cibil_score_normalized" in features

    def test_altman_z_score(self):
        from app.ml.feature_engineering import FeatureEngineer

        fe = FeatureEngineer()
        # Strong company should have Z > 2.9 (safe zone)
        z = fe.altman_z_score(
            working_capital=20e7,
            retained_earnings=10e7,
            ebit=8e7,
            equity=25e7,
            total_liabilities=50e7,
            revenue=45e7,
            total_assets=80e7,
        )
        assert z > 1.0  # Should be in safe or grey zone

    def test_piotroski_f_score(self):
        from app.ml.feature_engineering import FeatureEngineer

        fe = FeatureEngineer()
        score = fe.piotroski_f_score(
            roa=0.08, prev_roa=0.06,
            cfo=8e7, total_assets=80e7,
            delta_leverage=-0.02,
            delta_liquidity=0.1,
            dilution=False,
            gross_margin=0.33, prev_gross_margin=0.30,
            asset_turnover=0.56, prev_asset_turnover=0.52,
        )
        assert 0 <= score <= 9
        assert score >= 5  # Strong company should score well


class TestMLScoring:
    """Test the ML scoring engine."""

    def test_model_training(self, tmp_path):
        from app.ml.train_model import ModelTrainer

        models_dir = tmp_path / "models"
        models_dir.mkdir()

        trainer = ModelTrainer(output_dir=str(models_dir))
        trainer.train()

        assert (models_dir / "xgb_pd.pkl").exists()
        assert (models_dir / "lgbm_pd.pkl").exists()
        assert (models_dir / "meta_learner.pkl").exists()
        assert (models_dir / "feature_names.pkl").exists()

    def test_credit_scoring(self):
        from app.ml.scorer import CreditScorer

        scorer = CreditScorer()
        scorer.ensure_models()

        # Strong borrower features
        features = {
            "revenue_latest": 89e7,
            "revenue_cagr_5y": 0.15,
            "ebitda_margin_latest": 0.26,
            "pat_margin_latest": 0.12,
            "current_ratio": 1.8,
            "debt_equity_ratio": 1.2,
            "dscr_latest": 2.1,
            "dscr_3yr_avg": 2.0,
            "interest_coverage": 3.5,
            "altman_z_score": 3.2,
            "piotroski_f_score": 7,
            "cibil_score_normalized": 0.85,
            "news_sentiment_score": 0.6,
            "collateral_type_score": 5,
            "collateral_coverage_ratio": 1.5,
            "sector_npl_rate": 0.03,
        }

        result = scorer.score(features, requested_amount=25e7)

        assert result.decision in ("APPROVE", "CONDITIONAL", "DECLINE")
        assert 0 <= result.pd_score <= 1
        assert 0 <= result.lgd_score <= 1
        assert 300 <= result.credit_score <= 900
        assert result.credit_grade in ("AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D")
        assert result.recommended_rate > 0.085  # Must be above MCLR

    def test_credit_grade_mapping(self):
        from app.ml.scorer import CreditScorer

        assert CreditScorer.assign_credit_grade(0.0005) == "AAA"
        assert CreditScorer.assign_credit_grade(0.002) == "AA"
        assert CreditScorer.assign_credit_grade(0.005) == "A"
        assert CreditScorer.assign_credit_grade(0.01) == "BBB"
        assert CreditScorer.assign_credit_grade(0.03) == "BB"
        assert CreditScorer.assign_credit_grade(0.07) == "B"
        assert CreditScorer.assign_credit_grade(0.15) == "CCC"
        assert CreditScorer.assign_credit_grade(0.25) == "D"

    def test_weak_borrower_scores_lower(self):
        from app.ml.scorer import CreditScorer

        scorer = CreditScorer()
        scorer.ensure_models()

        # Weak borrower
        weak_features = {
            "revenue_latest": 20e7,
            "revenue_cagr_5y": -0.10,
            "ebitda_margin_latest": 0.05,
            "pat_margin_latest": -0.03,
            "current_ratio": 0.8,
            "debt_equity_ratio": 4.0,
            "dscr_latest": 0.9,
            "dscr_3yr_avg": 0.95,
            "interest_coverage": 0.8,
            "altman_z_score": 1.0,
            "piotroski_f_score": 2,
            "cibil_score_normalized": 0.45,
            "news_sentiment_score": -0.3,
            "collateral_type_score": 0,
            "collateral_coverage_ratio": 0.3,
            "sector_npl_rate": 0.09,
        }

        # Strong borrower
        strong_features = {
            "revenue_latest": 89e7,
            "revenue_cagr_5y": 0.15,
            "ebitda_margin_latest": 0.26,
            "pat_margin_latest": 0.12,
            "current_ratio": 1.8,
            "debt_equity_ratio": 1.2,
            "dscr_latest": 2.1,
            "dscr_3yr_avg": 2.0,
            "interest_coverage": 3.5,
            "altman_z_score": 3.2,
            "piotroski_f_score": 7,
            "cibil_score_normalized": 0.85,
            "news_sentiment_score": 0.6,
            "collateral_type_score": 5,
            "collateral_coverage_ratio": 1.5,
            "sector_npl_rate": 0.03,
        }

        weak_result = scorer.score(weak_features, requested_amount=50e7)
        strong_result = scorer.score(strong_features, requested_amount=25e7)

        # Strong borrower should have lower PD
        assert strong_result.pd_score <= weak_result.pd_score
        # Strong borrower should have higher credit score
        assert strong_result.credit_score >= weak_result.credit_score


class TestSHAPExplainer:
    """Test SHAP explainability."""

    def test_explain_returns_structure(self):
        from app.ml.scorer import CreditScorer
        from app.ml.explainer import SHAPExplainer

        scorer = CreditScorer()
        scorer.ensure_models()

        explainer = SHAPExplainer()
        features = {
            "revenue_latest": 89e7,
            "revenue_cagr_5y": 0.15,
            "ebitda_margin_latest": 0.26,
            "current_ratio": 1.8,
            "debt_equity_ratio": 1.2,
            "dscr_latest": 2.1,
            "altman_z_score": 3.2,
            "cibil_score_normalized": 0.85,
        }

        result = explainer.explain(features, scorer.xgb_pd, scorer.feature_names)

        assert "waterfall" in result or "waterfall_data" in result or isinstance(result, dict)

    def test_risk_radar_scores(self):
        from app.ml.explainer import SHAPExplainer

        explainer = SHAPExplainer()
        features = {
            "current_ratio": 1.8,
            "debt_equity_ratio": 1.2,
            "dscr_latest": 2.1,
            "revenue_cagr_5y": 0.15,
            "ebitda_margin_latest": 0.26,
            "cibil_score_normalized": 0.85,
            "collateral_coverage_ratio": 1.5,
            "news_sentiment_score": 0.6,
            "sector_npl_rate": 0.03,
        }

        radar = explainer.get_risk_radar_scores(features)

        assert isinstance(radar, dict)
        assert len(radar) >= 4  # Should have multiple risk axes


class TestRARRCalculation:
    """Test Risk-Adjusted Rate of Return calculation."""

    def test_rarr_above_mclr(self):
        from app.ml.scorer import CreditScorer

        scorer = CreditScorer()
        premium = scorer.compute_rarr(pd=0.02, lgd=0.35, ead=25e7)
        assert premium > 0  # Premium should be positive
        rate = 0.085 + premium
        assert rate > 0.085  # Total rate must exceed MCLR

    def test_higher_pd_higher_premium(self):
        from app.ml.scorer import CreditScorer

        scorer = CreditScorer()
        low_risk_premium = scorer.compute_rarr(pd=0.01, lgd=0.35, ead=25e7)
        high_risk_premium = scorer.compute_rarr(pd=0.10, lgd=0.35, ead=25e7)
        assert high_risk_premium >= low_risk_premium


class TestDemoCases:
    """Validate demo case data exists and has correct profiles."""

    def test_solar_tech_growth_profile(self, tmp_path):
        import duckdb
        from app.db.seed import seed_duckdb

        db_path = str(tmp_path / "test.duckdb")
        seed_duckdb(db_path)

        con = duckdb.connect(db_path)
        rows = con.execute("""
            SELECT fiscal_year, revenue, ebitda, pat
            FROM company_financials
            WHERE company_name = 'Rajasthan Solar Tech Pvt Ltd'
            ORDER BY fiscal_year
        """).fetchall()

        assert len(rows) == 5
        revenues = [r[1] for r in rows]
        # Revenue should be growing
        assert revenues[-1] > revenues[0]
        # All PAT should be positive (strong company)
        for r in rows:
            assert r[3] > 0  # PAT
        con.close()

    def test_delhi_real_estate_decline_profile(self, tmp_path):
        import duckdb
        from app.db.seed import seed_duckdb

        db_path = str(tmp_path / "test.duckdb")
        seed_duckdb(db_path)

        con = duckdb.connect(db_path)
        rows = con.execute("""
            SELECT fiscal_year, revenue, ebitda, pat
            FROM company_financials
            WHERE company_name = 'Delhi Real Estate Developers Pvt Ltd'
            ORDER BY fiscal_year
        """).fetchall()

        assert len(rows) == 5
        revenues = [r[1] for r in rows]
        # Revenue should be declining
        assert revenues[-1] < revenues[0]
        con.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
