#!/usr/bin/env python3
"""
NEXUS CREDIT — Demo Runner Script
Runs all 3 demo cases through the ML scoring pipeline and prints a summary.

Usage:
    cd backend
    python -m scripts.run_demo
"""
import sys
import os
import time
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///demo.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ANTHROPIC_API_KEY", "demo")
os.environ.setdefault("DUCKDB_PATH", "./data/nexus_demo.duckdb")
os.environ.setdefault("DEMO_MODE", "true")


def run_demo():
    print("=" * 70)
    print("  NEXUS CREDIT — AI-Powered Credit Decisioning Engine")
    print("  Demo Runner")
    print("=" * 70)
    print()

    # Step 1: Seed DuckDB
    print("[1/4] Seeding DuckDB with demo financials...")
    from app.db.seed import seed_duckdb, DEMO_CASES
    seed_duckdb()
    print("  ✓ 3 companies, 5 years of financials each")
    print("  ✓ Industry benchmarks (8 NIC codes)")
    print("  ✓ Macro indicators (10 entries)")
    print()

    # Step 2: Train ML models
    print("[2/4] Training ML ensemble (XGBoost + LightGBM)...")
    t0 = time.time()
    from app.ml.scorer import CreditScorer
    scorer = CreditScorer()
    scorer.ensure_models()
    print(f"  ✓ Models trained in {time.time() - t0:.1f}s")
    print()

    # Step 3: Feature Engineering + Scoring for each demo case
    print("[3/4] Running credit analysis on demo cases...")
    print()

    from app.ml.feature_engineering import FeatureEngineer
    from app.ml.explainer import SHAPExplainer

    fe = FeatureEngineer()
    explainer = SHAPExplainer()

    import duckdb
    db_path = os.getenv("DUCKDB_PATH", "./data/nexus_demo.duckdb")
    con = duckdb.connect(db_path)

    results = []

    for case in DEMO_CASES:
        company = case["company_name"]
        cin = case["cin"]
        requested = case["requested_amount"]
        loan_type = case["loan_type"]

        print(f"  📋 {company}")
        print(f"     Loan: {loan_type} | Requested: ₹{requested/1e7:.0f} Cr")

        # Fetch financials from DuckDB
        rows = con.execute(
            "SELECT * FROM company_financials WHERE cin = ? ORDER BY fiscal_year",
            [cin]
        ).fetchdf()

        if rows.empty:
            print(f"     ⚠ No financial data found for CIN {cin}")
            results.append({"company": company, "error": "No data"})
            continue

        # Convert to list of dicts
        spreads = rows.to_dict("records")

        # Compute features
        company_meta = {
            "years_in_operation": case.get("years_in_operation", 10),
            "auditor_quality": case.get("auditor_quality", 3),
            "qualified_opinion": case.get("qualified_opinion", False),
            "export_revenue_pct": case.get("export_revenue_pct", 0.1),
            "related_party_ratio": case.get("related_party_ratio", 0.05),
        }

        bureau_data = {
            "cibil_score": case.get("cibil_score", 700),
            "dpd_max": case.get("dpd_max", 0),
            "existing_utilization": case.get("existing_utilization", 0.5),
            "enquiry_count_6m": case.get("enquiry_count_6m", 3),
            "unsecured_ratio": case.get("unsecured_ratio", 0.2),
            "bureau_vintage_years": case.get("bureau_vintage_years", 5),
        }

        web_signals = {
            "news_sentiment_score": case.get("news_sentiment", 0.3),
            "regulatory_action_flag": case.get("regulatory_flags", False),
            "litigation_score": case.get("litigation_score", 2),
            "management_change_velocity": 0,
            "social_media_controversy": 0,
            "gst_compliance_rate": case.get("gst_compliance", 0.9),
            "roc_compliance_score": 0.85,
        }

        features = fe.compute_all_features(spreads, company_meta, bureau_data, web_signals)
        result = scorer.score(features, requested_amount=requested)

        # SHAP explanation
        shap_data = explainer.explain(features)

        results.append({
            "company": company,
            "decision": result.decision,
            "grade": result.credit_grade,
            "score": result.credit_score,
            "pd": result.pd_score,
            "limit": result.recommended_limit,
            "rate": result.recommended_rate,
            "expected_loss": result.expected_loss,
            "confidence": result.confidence,
        })

        decision_icon = {"APPROVE": "✅", "CONDITIONAL": "⚠️", "DECLINE": "❌"}.get(result.decision, "❓")
        print(f"     {decision_icon} Decision: {result.decision} | Grade: {result.credit_grade} | Score: {result.credit_score}")
        print(f"     PD: {result.pd_score:.4f} | Confidence: {result.confidence:.1%}")
        print(f"     Limit: ₹{result.recommended_limit/1e7:.1f} Cr | Rate: {result.recommended_rate:.2%}")
        print(f"     Expected Loss: ₹{result.expected_loss/1e5:.1f}L")
        print()

    con.close()

    # Step 4: Summary table
    print("[4/4] Summary")
    print()
    print("=" * 90)
    print(f"{'Company':<35} {'Decision':<12} {'Grade':<6} {'Score':<6} {'PD':<8} {'Limit (Cr)':<12} {'Rate':<8}")
    print("-" * 90)
    for r in results:
        if "error" in r:
            print(f"{r['company']:<35} {'ERROR':<12}")
            continue
        print(
            f"{r['company']:<35} {r['decision']:<12} {r['grade']:<6} "
            f"{r['score']:<6} {r['pd']:<8.4f} "
            f"₹{r['limit']/1e7:<10.1f} {r['rate']:<8.2%}"
        )
    print("=" * 90)
    print()
    print("NEXUS CREDIT: From Application to Decision in 180 Seconds.")
    print()


if __name__ == "__main__":
    run_demo()
