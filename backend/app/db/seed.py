"""Seed DuckDB with demo financial data and create demo credit cases."""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def seed_duckdb(db_path: str | None = None):
    """Seed DuckDB with demo company financials and industry benchmarks."""
    import duckdb

    if db_path is None:
        db_path = os.getenv("DUCKDB_PATH", "./data/nexus_demo.duckdb")

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db_path)

    # Company financials table
    con.execute("""
        CREATE TABLE IF NOT EXISTS company_financials (
            company_name VARCHAR, cin VARCHAR, fiscal_year VARCHAR,
            revenue DOUBLE, cost_of_goods DOUBLE, gross_profit DOUBLE,
            ebitda DOUBLE, depreciation DOUBLE, ebit DOUBLE,
            interest_expense DOUBLE, pbt DOUBLE, tax DOUBLE, pat DOUBLE,
            total_assets DOUBLE, total_debt DOUBLE, equity DOUBLE,
            current_assets DOUBLE, current_liabilities DOUBLE,
            cash_equivalents DOUBLE, inventory DOUBLE,
            trade_receivables DOUBLE, trade_payables DOUBLE,
            cfo DOUBLE, cfi DOUBLE, cff DOUBLE,
            retained_earnings DOUBLE
        )
    """)

    # Industry benchmarks table
    con.execute("""
        CREATE TABLE IF NOT EXISTS industry_benchmarks (
            nic_code VARCHAR, industry_name VARCHAR,
            median_current_ratio DOUBLE, median_de_ratio DOUBLE,
            median_ebitda_margin DOUBLE, median_roe DOUBLE,
            median_dscr DOUBLE, median_asset_turnover DOUBLE,
            sector_npl_rate DOUBLE, sector_growth_rate DOUBLE
        )
    """)

    # Macro indicators table
    con.execute("""
        CREATE TABLE IF NOT EXISTS macro_indicators (
            indicator VARCHAR, year INTEGER, value DOUBLE
        )
    """)

    # Check if data already exists
    count = con.execute("SELECT COUNT(*) FROM company_financials").fetchone()[0]
    if count > 0:
        logger.info("DuckDB already seeded, skipping")
        con.close()
        return

    # ===== DEMO CASE 1: Rajasthan Solar Tech Pvt Ltd (APPROVE) =====
    solar_data = [
        ("Rajasthan Solar Tech Pvt Ltd", "U40106RJ2015PTC048123", "FY2020",
         45_00_00_000, 31_50_00_000, 13_50_00_000, 9_90_00_000, 2_25_00_000, 7_65_00_000,
         1_80_00_000, 5_85_00_000, 1_46_25_000, 4_38_75_000,
         72_00_00_000, 27_00_00_000, 32_00_00_000,
         22_50_00_000, 13_50_00_000, 4_50_00_000, 6_75_00_000,
         9_00_00_000, 5_40_00_000,
         8_10_00_000, -12_00_00_000, 5_40_00_000, 18_00_00_000),
        ("Rajasthan Solar Tech Pvt Ltd", "U40106RJ2015PTC048123", "FY2021",
         52_00_00_000, 36_40_00_000, 15_60_00_000, 11_96_00_000, 2_60_00_000, 9_36_00_000,
         1_95_00_000, 7_41_00_000, 1_85_25_000, 5_55_75_000,
         82_00_00_000, 28_00_00_000, 37_50_00_000,
         26_00_00_000, 15_60_00_000, 5_20_00_000, 7_80_00_000,
         10_40_00_000, 6_24_00_000,
         9_88_00_000, -10_00_00_000, 2_00_00_000, 23_50_00_000),
        ("Rajasthan Solar Tech Pvt Ltd", "U40106RJ2015PTC048123", "FY2022",
         63_00_00_000, 43_00_00_000, 20_00_00_000, 15_12_00_000, 3_15_00_000, 11_97_00_000,
         2_10_00_000, 9_87_00_000, 2_46_75_000, 7_40_25_000,
         95_00_00_000, 30_00_00_000, 44_00_00_000,
         31_50_00_000, 18_90_00_000, 6_30_00_000, 9_45_00_000,
         12_60_00_000, 7_56_00_000,
         12_60_00_000, -15_00_00_000, 4_00_00_000, 30_80_00_000),
        ("Rajasthan Solar Tech Pvt Ltd", "U40106RJ2015PTC048123", "FY2023",
         76_00_00_000, 51_68_00_000, 24_32_00_000, 19_00_00_000, 3_80_00_000, 15_20_00_000,
         2_28_00_000, 12_92_00_000, 3_23_00_000, 9_69_00_000,
         110_00_00_000, 32_00_00_000, 53_00_00_000,
         38_00_00_000, 22_00_00_000, 7_60_00_000, 11_40_00_000,
         15_20_00_000, 9_12_00_000,
         15_96_00_000, -18_00_00_000, 3_00_00_000, 40_40_00_000),
        ("Rajasthan Solar Tech Pvt Ltd", "U40106RJ2015PTC048123", "FY2024",
         89_00_00_000, 59_63_00_000, 29_37_00_000, 23_14_00_000, 4_45_00_000, 18_69_00_000,
         2_40_00_000, 16_29_00_000, 4_07_25_000, 12_21_75_000,
         128_00_00_000, 33_00_00_000, 64_00_00_000,
         44_80_00_000, 25_60_00_000, 8_96_00_000, 13_44_00_000,
         17_80_00_000, 10_68_00_000,
         19_58_00_000, -20_00_00_000, 2_00_00_000, 52_50_00_000),
    ]

    # ===== DEMO CASE 2: Mumbai Textiles Ltd (CONDITIONAL) =====
    textile_data = [
        ("Mumbai Textiles Ltd", "L17110MH2008PLC182456", "FY2020",
         32_00_00_000, 24_00_00_000, 8_00_00_000, 4_80_00_000, 1_60_00_000, 3_20_00_000,
         2_24_00_000, 96_00_000, 24_00_000, 72_00_000,
         58_00_00_000, 38_00_00_000, 14_00_00_000,
         20_30_00_000, 17_40_00_000, 1_74_00_000, 8_12_00_000,
         8_96_00_000, 6_96_00_000,
         3_20_00_000, -4_00_00_000, 1_60_00_000, 5_60_00_000),
        ("Mumbai Textiles Ltd", "L17110MH2008PLC182456", "FY2021",
         28_00_00_000, 21_56_00_000, 6_44_00_000, 3_64_00_000, 1_54_00_000, 2_10_00_000,
         2_10_00_000, 0, 0, 0,
         56_00_00_000, 37_00_00_000, 13_00_00_000,
         19_60_00_000, 16_80_00_000, 1_40_00_000, 8_40_00_000,
         8_40_00_000, 6_72_00_000,
         2_24_00_000, -2_00_00_000, 56_00_000, 5_60_00_000),
        ("Mumbai Textiles Ltd", "L17110MH2008PLC182456", "FY2022",
         33_00_00_000, 24_75_00_000, 8_25_00_000, 5_28_00_000, 1_65_00_000, 3_63_00_000,
         2_31_00_000, 1_32_00_000, 33_00_000, 99_00_000,
         60_00_00_000, 39_00_00_000, 14_50_00_000,
         21_00_00_000, 18_00_00_000, 1_80_00_000, 8_70_00_000,
         9_00_00_000, 7_20_00_000,
         3_96_00_000, -5_00_00_000, 2_00_00_000, 6_50_00_000),
        ("Mumbai Textiles Ltd", "L17110MH2008PLC182456", "FY2023",
         34_00_00_000, 25_16_00_000, 8_84_00_000, 5_78_00_000, 1_70_00_000, 4_08_00_000,
         2_38_00_000, 1_70_00_000, 42_50_000, 1_27_50_000,
         62_00_00_000, 40_00_00_000, 15_20_00_000,
         21_70_00_000, 18_60_00_000, 1_86_00_000, 9_00_00_000,
         9_30_00_000, 7_44_00_000,
         4_42_00_000, -3_00_00_000, 0, 7_70_00_000),
        ("Mumbai Textiles Ltd", "L17110MH2008PLC182456", "FY2024",
         35_00_00_000, 25_55_00_000, 9_45_00_000, 6_30_00_000, 1_75_00_000, 4_55_00_000,
         2_45_00_000, 2_10_00_000, 52_50_000, 1_57_50_000,
         64_00_00_000, 41_00_00_000, 16_00_00_000,
         22_40_00_000, 19_20_00_000, 1_92_00_000, 9_28_00_000,
         9_60_00_000, 7_68_00_000,
         4_90_00_000, -4_00_00_000, 1_00_00_000, 9_20_00_000),
    ]

    # ===== DEMO CASE 3: Delhi Real Estate Developers (DECLINE) =====
    realty_data = [
        ("Delhi Real Estate Developers Pvt Ltd", "U45201DL2012PTC234567", "FY2020",
         120_00_00_000, 84_00_00_000, 36_00_00_000, 21_60_00_000, 6_00_00_000, 15_60_00_000,
         10_80_00_000, 4_80_00_000, 1_20_00_000, 3_60_00_000,
         350_00_00_000, 245_00_00_000, 70_00_00_000,
         105_00_00_000, 87_50_00_000, 10_50_00_000, 52_50_00_000,
         42_00_00_000, 35_00_00_000,
         9_60_00_000, -30_00_00_000, 22_00_00_000, 28_00_00_000),
        ("Delhi Real Estate Developers Pvt Ltd", "U45201DL2012PTC234567", "FY2021",
         95_00_00_000, 71_25_00_000, 23_75_00_000, 12_35_00_000, 5_70_00_000, 6_65_00_000,
         10_45_00_000, -3_80_00_000, 0, -3_80_00_000,
         340_00_00_000, 255_00_00_000, 60_00_00_000,
         102_00_00_000, 91_80_00_000, 6_80_00_000, 54_40_00_000,
         40_80_00_000, 37_40_00_000,
         -2_85_00_000, -10_00_00_000, 15_00_00_000, 24_00_00_000),
        ("Delhi Real Estate Developers Pvt Ltd", "U45201DL2012PTC234567", "FY2022",
         85_00_00_000, 65_45_00_000, 19_55_00_000, 8_50_00_000, 5_10_00_000, 3_40_00_000,
         10_20_00_000, -6_80_00_000, 0, -6_80_00_000,
         330_00_00_000, 260_00_00_000, 48_00_00_000,
         99_00_00_000, 95_70_00_000, 4_95_00_000, 56_10_00_000,
         39_60_00_000, 39_60_00_000,
         -8_50_00_000, -5_00_00_000, 16_00_00_000, 17_00_00_000),
        ("Delhi Real Estate Developers Pvt Ltd", "U45201DL2012PTC234567", "FY2023",
         78_00_00_000, 62_40_00_000, 15_60_00_000, 5_46_00_000, 4_68_00_000, 78_00_000,
         9_36_00_000, -8_58_00_000, 0, -8_58_00_000,
         320_00_00_000, 265_00_00_000, 35_00_00_000,
         96_00_00_000, 99_20_00_000, 3_20_00_000, 57_60_00_000,
         38_40_00_000, 41_60_00_000,
         -12_48_00_000, -3_00_00_000, 18_00_00_000, 8_00_00_000),
        ("Delhi Real Estate Developers Pvt Ltd", "U45201DL2012PTC234567", "FY2024",
         70_00_00_000, 58_10_00_000, 11_90_00_000, 2_80_00_000, 4_20_00_000, -1_40_00_000,
         8_40_00_000, -9_80_00_000, 0, -9_80_00_000,
         310_00_00_000, 270_00_00_000, 22_00_00_000,
         93_00_00_000, 102_30_00_000, 2_17_00_000, 58_90_00_000,
         37_20_00_000, 43_40_00_000,
         -15_40_00_000, -2_00_00_000, 20_00_00_000, -2_00_00_000),
    ]

    cols = (
        "company_name, cin, fiscal_year, revenue, cost_of_goods, gross_profit, "
        "ebitda, depreciation, ebit, interest_expense, pbt, tax, pat, "
        "total_assets, total_debt, equity, current_assets, current_liabilities, "
        "cash_equivalents, inventory, trade_receivables, trade_payables, "
        "cfo, cfi, cff, retained_earnings"
    )
    placeholders = ", ".join(["?"] * 26)

    for rows in [solar_data, textile_data, realty_data]:
        for row in rows:
            con.execute(f"INSERT INTO company_financials ({cols}) VALUES ({placeholders})", row)

    # Industry benchmarks
    benchmarks = [
        ("26", "Solar Energy & Equipment", 1.8, 1.5, 22.0, 18.0, 2.0, 0.9, 2.5, 12.0),
        ("17", "Textiles & Apparel", 1.3, 2.5, 15.0, 12.0, 1.4, 1.1, 8.5, 4.0),
        ("45", "Real Estate & Construction", 1.1, 3.0, 18.0, 10.0, 1.1, 0.4, 12.0, -2.0),
        ("10", "Food Processing", 1.5, 1.8, 12.0, 15.0, 1.6, 1.3, 5.0, 8.0),
        ("29", "Automobiles", 1.4, 1.6, 14.0, 16.0, 1.8, 1.2, 4.0, 6.0),
        ("21", "Pharmaceuticals", 1.9, 0.8, 20.0, 20.0, 2.2, 0.8, 3.0, 10.0),
        ("62", "IT & Software Services", 2.5, 0.3, 25.0, 28.0, 3.0, 1.5, 1.5, 14.0),
        ("24", "Chemicals", 1.6, 1.4, 16.0, 14.0, 1.5, 1.0, 6.0, 7.0),
    ]
    for b in benchmarks:
        con.execute(
            "INSERT INTO industry_benchmarks VALUES (?,?,?,?,?,?,?,?,?,?)", b
        )

    # Macro indicators
    macros = [
        ("gdp_growth_rate", 2024, 6.8),
        ("gdp_growth_rate", 2023, 7.2),
        ("gdp_growth_rate", 2022, 7.0),
        ("repo_rate", 2024, 6.50),
        ("repo_rate", 2023, 6.50),
        ("cpi_inflation", 2024, 4.8),
        ("cpi_inflation", 2023, 5.4),
        ("iip_growth", 2024, 5.7),
        ("credit_growth", 2024, 16.3),
        ("mclr_1yr", 2024, 8.50),
    ]
    for m in macros:
        con.execute("INSERT INTO macro_indicators VALUES (?,?,?)", m)

    con.close()
    logger.info(f"DuckDB seeded at {db_path} with 3 demo companies + benchmarks + macros")


DEMO_CASES = [
    {
        "company_name": "Rajasthan Solar Tech Pvt Ltd",
        "cin": "U40106RJ2015PTC048123",
        "gstin": "08AABCU9603R1ZM",
        "pan": "AABCU9603R",
        "industry_code": "26",
        "loan_type": "TERM_LOAN",
        "requested_amount": 25_00_00_000,
        "requested_tenure_months": 84,
        "purpose": "Capex for 50MW solar module manufacturing expansion in Jodhpur SEZ",
        "priority": "HIGH",
    },
    {
        "company_name": "Mumbai Textiles Ltd",
        "cin": "L17110MH2008PLC182456",
        "gstin": "27AADCM5678Q1ZK",
        "pan": "AADCM5678Q",
        "industry_code": "17",
        "loan_type": "WCDL",
        "requested_amount": 15_00_00_000,
        "requested_tenure_months": 12,
        "purpose": "Working capital requirement for export order fulfilment and raw material procurement",
        "priority": "NORMAL",
    },
    {
        "company_name": "Delhi Real Estate Developers Pvt Ltd",
        "cin": "U45201DL2012PTC234567",
        "gstin": "07AABCD1234M1ZP",
        "pan": "AABCD1234M",
        "industry_code": "45",
        "loan_type": "LAP",
        "requested_amount": 50_00_00_000,
        "requested_tenure_months": 120,
        "purpose": "Loan against property for project completion funding — Dwarka Phase 2 residential township",
        "priority": "NORMAL",
    },
]
