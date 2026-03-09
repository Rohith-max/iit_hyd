# NEXUS CREDIT — AI-Powered Credit Decisioning Engine

> **From Application to Decision in 180 Seconds.**
>
> IIT Hyderabad Hackathon 2025 | Fintech AI Category

---

## What is NEXUS CREDIT?

India's ₹120 lakh crore credit market is strangled by a **4-week decisioning bottleneck** that costs banks ₹8,500 crore annually in analyst hours. NEXUS CREDIT is the world's first **autonomous credit analyst** — an AI agent swarm that ingests multi-source data, runs ML ensemble scoring, performs real-time web research, and auto-generates a **publication-quality 40-page Credit Appraisal Memo (CAM)** in under 3 minutes.

### Key Outputs
- **Lend / Conditional Lend / Decline** decision with confidence score
- **Credit Grade** (AAA → D) with calibrated Probability of Default
- **Recommended Credit Limit** optimized against cash flows and collateral
- **Risk-Adjusted Rate of Return** (MCLR + computed risk premium)
- **Explainable AI** — SHAP waterfall showing every factor's contribution
- **Early Warning Signals** — 15 automated risk triggers with RED/AMBER/GREEN
- **Full CAM PDF** — 30–45 page document with letterhead, tables, and signature block

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NEXUS CREDIT PLATFORM                        │
├──────────────────┬──────────────────────────────────────────────────┤
│   REACT FRONTEND │              FASTAPI BACKEND                     │
│                  │                                                   │
│  ┌────────────┐  │  ┌─────────────────────────────────────────────┐ │
│  │ Landing    │  │  │  Intake API + Validation                   │ │
│  │ Dashboard  │  │  └──────────────┬──────────────────────────────┘ │
│  │ Intake     │  │                 │                                 │
│  │ Live Feed  │  │  ┌──────────────▼──────────────────────────────┐ │
│  │ Decision   │  │  │     AI AGENT SWARM (5 Agents)               │ │
│  │ CAM Viewer │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  └────────────┘  │  │  │ DATA     │  │ RESEARCH │  │ ANALYST  │  │ │
│                  │  │  │ INGESTOR │  │ AGENT    │  │ AGENT    │  │ │
│  WebSocket ◀─────┼──┤  │ DuckDB   │  │ Tavily   │  │ Features │  │ │
│  (live stream)   │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  │ │
│                  │  │  ┌────▼──────────────▼──────────────▼──────┐ │ │
│                  │  │  │    ML ENSEMBLE (XGBoost + LightGBM)     │ │ │
│                  │  │  │    PD / LGD / EAD → Expected Loss       │ │ │
│                  │  │  │    SHAP TreeExplainer → Explainability   │ │ │
│                  │  │  └────────────────┬────────────────────────┘ │ │
│                  │  │  ┌────────────────▼────────────────────────┐ │ │
│                  │  │  │    CAM WRITER (Claude Streaming)         │ │ │
│                  │  │  │    10 Sections → WeasyPrint PDF          │ │ │
│                  │  │  └─────────────────────────────────────────┘ │ │
└──────────────────┴──────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI (async + WebSocket), SQLAlchemy + asyncpg |
| **ML Engine** | XGBoost + LightGBM ensemble, SHAP TreeExplainer, scikit-learn, SMOTE |
| **AI/LLM** | Anthropic Claude claude-sonnet-4-20250514 (streaming CAM generation) |
| **Web Research** | Tavily Search API, ChromaDB (RAG), Playwright |
| **Data Lake** | DuckDB (Databricks Delta Lake mock) with pre-seeded financials |
| **PDF** | WeasyPrint + Jinja2 (A4 template, letterhead, CONFIDENTIAL watermark) |
| **Database** | PostgreSQL 16 + Redis 7 |
| **Frontend** | React 18 + TypeScript + Vite 6, Tailwind CSS 3.4 |
| **State** | Zustand 5 + React Query 5 (TanStack) |
| **Charts** | Recharts 2 (SHAP waterfall, risk radar, financial trends) |
| **Animation** | Framer Motion 11, CSS scroll-reveal, IntersectionObserver |
| **Real-time** | Socket.io client (live agent thought streaming) |
| **Infrastructure** | Docker Compose (4 services), nginx reverse proxy |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- API keys: `ANTHROPIC_API_KEY`, `TAVILY_API_KEY` (optional)

### 1. Clone & Configure

```bash
git clone https://github.com/your-team/nexus-credit.git
cd nexus-credit
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY at minimum
```

### 2. Launch (One Command)

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL 16** on port 5432
- **Redis 7** on port 6379
- **FastAPI Backend** on port 8000 (auto-seeds DuckDB, trains ML models)
- **React Frontend** on port 5173

### 3. Open

Navigate to **http://localhost:5173**

---

## Demo Walkthrough

NEXUS CREDIT ships with **3 pre-seeded demo cases** spanning the full decision spectrum:

| # | Company | Profile | Expected Decision |
|---|---------|---------|-------------------|
| 1 | Rajasthan Solar Tech Pvt Ltd | Strong growth, clean bureau, DSCR 2.1x | **APPROVE** — Grade AA, ₹25Cr, 11.25% |
| 2 | Mumbai Textiles Ltd | Flat revenue, high leverage D/E 2.8x | **CONDITIONAL** — Grade BBB, covenants |
| 3 | Delhi Real Estate Developers | Declining, DSCR 0.9x, regulatory flags | **DECLINE** — Grade CCC |

### Running the Demo

1. Click **"Run Demo Analysis"** on the landing page, or navigate to **Dashboard → New Analysis**
2. In the Intake wizard, enter company details (or use CIN auto-lookup)
3. Upload financials (or proceed with demo data)
4. Click **"Initiate AI Analysis"** — watch the live agent feed:
   - **Data Ingestor** → pulls DuckDB financials, parses uploads
   - **Financial Analyst** → 80+ features, Altman Z-Score, Piotroski F-Score
   - **Web Researcher** → Tavily search, news sentiment, regulatory checks
   - **Risk Assessor** → ML scoring, EWS triggers, RARR calculation
   - **CAM Writer** → Claude streams each section live
5. View the **Decision Dashboard** with SHAP waterfall, risk radar, EWS traffic lights
6. Download the **40-page CAM PDF** with full letterhead and professional formatting

---

## API Endpoints

```
POST   /api/v1/cases                           Create new case
GET    /api/v1/cases                           List cases (paginated)
GET    /api/v1/cases/{case_id}                 Case detail
POST   /api/v1/cases/{case_id}/analyze         Trigger AI analysis pipeline
GET    /api/v1/cases/{case_id}/decision        ML decision + scores
GET    /api/v1/cases/{case_id}/cam             Full CAM JSON
GET    /api/v1/cases/{case_id}/cam/pdf         Download CAM PDF
GET    /api/v1/cases/{case_id}/ews             Early Warning Signals
GET    /api/v1/cases/{case_id}/shap            SHAP explanation data

WS     /ws/cases/{case_id}                    Live agent stream

POST   /api/v1/companies/lookup               MCA lookup by CIN
GET    /api/v1/industry/{nic_code}/benchmarks  Industry benchmarks
GET    /api/v1/dashboard/stats                 Platform statistics
GET    /health                                 Health check
```

---

## ML Model Details

### Ensemble Architecture
- **XGBoost Classifier** — PD model with isotonic calibration
- **LightGBM Classifier** — Alternative PD model
- **Meta-learner** — Stacked LogisticRegression on ensemble outputs
- **XGBoost Regressor** — Optimal credit limit model

### Feature Engineering (80+ Features)
- **Financial Health (30):** CAGR, DSCR, Altman Z-Score, Piotroski F-Score, Beneish M-Score, working capital cycle
- **Business Quality (15):** Industry risk, management quality, customer concentration, audit quality
- **Credit Behaviour (10):** CIBIL score, DPD history, utilization ratio
- **Collateral (8):** LTV ratio, coverage, enforceability
- **Macro & Industry (10):** NPL rates, GDP growth, sector credit growth
- **Web Intelligence (7):** News sentiment, regulatory flags, litigation score

### Credit Grade Mapping
| PD Range | Grade | Risk Level |
|----------|-------|------------|
| < 0.1% | AAA | Minimal |
| 0.1% – 0.3% | AA | Very Low |
| 0.3% – 0.7% | A | Low |
| 0.7% – 2.0% | BBB | Moderate |
| 2.0% – 5.0% | BB | Elevated |
| 5.0% – 10% | B | High |
| 10% – 20% | CCC | Very High |
| > 20% | D | Default |

### RARR Formula
```
Risk Premium = EL/(1-LGD) + Capital Cost (8%) + Operational Cost (1.5%)
RARR = MCLR (8.5%) + Risk Premium
where EL = PD × LGD × EAD
```

---

## Project Structure

```
nexus-credit/
├── backend/
│   ├── app/
│   │   ├── agents/           # AI agent swarm (5 agents + orchestrator)
│   │   │   ├── data_ingestor.py
│   │   │   ├── financial_analyst.py
│   │   │   ├── web_research.py
│   │   │   ├── risk_assessor.py
│   │   │   ├── cam_writer.py
│   │   │   ├── orchestrator.py
│   │   │   ├── state.py
│   │   │   └── ws_manager.py
│   │   ├── api/routes/       # FastAPI endpoints
│   │   ├── ml/               # ML pipeline
│   │   │   ├── feature_engineering.py   # 80+ features
│   │   │   ├── train_model.py           # XGBoost + LightGBM
│   │   │   ├── scorer.py               # Credit scoring
│   │   │   └── explainer.py            # SHAP explainability
│   │   ├── models/           # SQLAlchemy ORM
│   │   ├── services/         # PDF generation
│   │   ├── templates/        # WeasyPrint HTML templates
│   │   ├── core/             # Config & database
│   │   ├── db/               # DuckDB seed data
│   │   └── main.py           # FastAPI entry point
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # 6 pages (Landing → CAMViewer)
│   │   ├── components/       # Layout, UI components
│   │   ├── hooks/            # WebSocket, scroll-reveal
│   │   ├── store/            # Zustand state management
│   │   ├── lib/              # API client (Axios)
│   │   └── types/            # TypeScript interfaces
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Why NEXUS CREDIT Wins

| Dimension | Traditional Process | NEXUS CREDIT |
|-----------|-------------------|--------------|
| **Time** | 3–6 weeks | **3 minutes** |
| **Analysts** | 8–12 people | **1 AI system** |
| **Cost per case** | ₹85,000 | **₹12** (API costs) |
| **Consistency** | Varies by analyst | **100% standardized** |
| **Explainability** | Subjective notes | **SHAP + quantified factors** |
| **Risk Coverage** | ~30 factors checked | **80+ ML features** |
| **Output** | 10-page Word doc | **40-page CAM PDF** |
| **Real-time** | Email updates | **Live WebSocket streaming** |

### Technical Differentiators
1. **AI Agent Swarm** — 5 specialized agents working in parallel, not a single monolithic prompt
2. **Calibrated ML Ensemble** — XGBoost + LightGBM with isotonic calibration for true probability estimates
3. **Explainable AI** — SHAP TreeExplainer waterfall, not a black box
4. **Live Streaming UX** — Watch the AI think in real-time via WebSocket thought streaming
5. **Publication-Quality CAM** — WeasyPrint PDF with proper banking format, not a template fill
6. **Basel II Compliant Scoring** — PD/LGD/EAD framework with proper credit grade mapping

---

## Team

Built for the **IIT Hyderabad Hackathon 2025** | Fintech AI Category

---

## License

MIT License — Built for demonstration and educational purposes.
