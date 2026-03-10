import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Zap, Shield, Brain, BarChart3, Clock, FileText,
  TrendingUp, ChevronRight, Database, Globe, AlertTriangle,
  CheckCircle2, Building2, Landmark, CreditCard, Factory,
} from 'lucide-react';

/* ─── Scroll Reveal Hook ─── */
function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  const [vis, setVis] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVis(true); io.unobserve(el); } }, { threshold: 0.12 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return { ref, vis };
}

/* ─── Counter Animation ─── */
function Counter({ target, suffix = '', prefix = '' }: { target: number; suffix?: string; prefix?: string }) {
  const [val, setVal] = useState(0);
  const { ref, vis } = useReveal();
  useEffect(() => {
    if (!vis) return;
    let curr = 0;
    const step = target / 60;
    const t = setInterval(() => {
      curr += step;
      if (curr >= target) { setVal(target); clearInterval(t); } else setVal(Math.floor(curr));
    }, 16);
    return () => clearInterval(t);
  }, [vis, target]);
  return <span ref={ref}>{prefix}{val.toLocaleString()}{suffix}</span>;
}

/* ═══════════════════════════ LANDING PAGE ═══════════════════════════ */
export default function Landing() {
  const navigate = useNavigate();

  // Sticky nav scroll state
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, []);

  const partners = [
    'State Bank of India', 'HDFC Bank', 'ICICI Bank', 'Axis Bank',
    'Kotak Mahindra', 'Bank of Baroda', 'Punjab National Bank',
    'IndusInd Bank', 'Canara Bank', 'Union Bank of India',
  ];

  const solutions = [
    { icon: Landmark, title: 'Corporate Lending', desc: 'End-to-end credit appraisal for term loans, working capital, and project finance up to ₹500 Cr.' },
    { icon: Building2, title: 'MSME Finance', desc: 'Accelerated decisioning for Mudra, CGTMSE, and PSB-backed MSME lending programmes.' },
    { icon: CreditCard, title: 'Trade Finance', desc: 'LC, BG, and buyer credit assessment with cross-border risk intelligence and ECGC integration.' },
    { icon: Factory, title: 'Infrastructure & Project', desc: 'DCF-based project viability, DSCR waterfall modelling, and consortium lending analytics.' },
  ];

  const capabilities = [
    { icon: Brain, title: 'AI Agent Orchestration', desc: 'Five autonomous agents collaborate in sequence — ingesting data, analysing financials, researching markets, scoring risk, and generating CAMs.' },
    { icon: Zap, title: 'Real-Time Decisioning', desc: 'From application to credit decision in under 3 minutes. Replaces manual workflows that typically require 3–6 weeks.' },
    { icon: Shield, title: 'Explainable AI', desc: 'Every decision is supported by feature-level SHAP explanations ensuring full transparency and RBI regulatory compliance.' },
    { icon: BarChart3, title: 'Ensemble ML Scoring', desc: 'XGBoost and LightGBM ensemble with Basel II-calibrated PD, LGD, and EAD models across 80+ engineered features.' },
    { icon: Clock, title: 'Live Streaming Pipeline', desc: 'Watch agents think in real-time via WebSocket. CAM builds section-by-section before your eyes.' },
    { icon: FileText, title: 'Auto-Generated CAM', desc: 'Publication-quality Credit Appraisal Memo with financial spreads, peer benchmarking, and covenant recommendations.' },
    { icon: TrendingUp, title: 'Early Warning System', desc: '15 automated triggers monitoring DSCR, leverage, pledge ratios, audit flags, and market signals continuously.' },
    { icon: AlertTriangle, title: 'Fraud Detection', desc: 'Beneish M-Score, promoter pledge analysis, and anomaly detection across financial statements and bureau data.' },
  ];

  return (
    <div className="bg-black text-white overflow-hidden">

      {/* ═══ STICKY NAVBAR ═══ */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-black/80 backdrop-blur-xl border-b border-white/5' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-nexus-cyan/10 border border-nexus-cyan/20">
              <span className="text-nexus-cyan font-bold text-sm font-mono">N</span>
            </div>
            <span className="text-sm font-semibold tracking-tight">
              NEXUS <span className="text-nexus-cyan">CREDIT</span>
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-white/50">
            <a href="#solutions" className="hover:text-white transition-colors">Solutions</a>
            <a href="#platform" className="hover:text-white transition-colors">Platform</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
            <a href="#integrate" className="hover:text-white transition-colors">Integrate</a>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="hidden sm:flex items-center gap-2 rounded-full bg-nexus-cyan/10 border border-nexus-cyan/20 text-nexus-cyan px-5 py-2 text-sm font-medium transition-all hover:bg-nexus-cyan/20"
            >
              Open Platform
            </button>
            <button
              onClick={() => navigate('/intake')}
              className="flex items-center gap-2 rounded-full bg-white text-black px-5 py-2 text-sm font-semibold transition-all hover:bg-white/90"
            >
              Get Started
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </nav>

      {/* ═══ HERO ═══ */}
      <section className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden">
        {/* Background gradient orbs */}
        <div className="absolute inset-0 z-0">
          <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] rounded-full bg-nexus-cyan/5 blur-[120px]" />
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] rounded-full bg-blue-600/5 blur-[100px]" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_20%,black_70%)]" />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center py-20">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 mb-8 backdrop-blur-sm">
            <span className="h-2 w-2 rounded-full bg-nexus-green animate-pulse" />
            <span className="text-xs text-white/60 tracking-wide">Platform Active</span>
            <span className="text-xs text-white/30">|</span>
            <span className="text-xs text-white/60">Autonomous Credit Intelligence</span>
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.05] tracking-tight mb-6">
            <span className="gradient-text">Transform Credit Appraisal</span>
            <br />
            <span className="gradient-text">with Autonomous</span>{' '}
            <span className="gradient-text-cyan">AI Agents</span>
          </h1>

          <p className="max-w-2xl mx-auto text-lg text-white/40 mb-10 leading-relaxed">
            NEXUS CREDIT deploys an AI agent swarm to ingest financial data, score risk using ML ensembles, and generate publication-quality Credit Appraisal Memos — all in under 3 minutes.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate('/intake')}
              className="group flex items-center gap-2 rounded-full bg-white text-black px-8 py-3.5 text-sm font-semibold transition-all hover:bg-white/90 hover:shadow-[0_0_30px_rgba(255,255,255,0.15)]"
            >
              Start Credit Analysis
              <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 rounded-full border border-white/15 px-8 py-3.5 text-sm font-medium text-white/70 transition-all hover:border-white/30 hover:text-white hover:bg-white/5"
            >
              View Dashboard
            </button>
          </div>
        </div>
      </section>

      {/* ═══ PARTNER TICKER ═══ */}
      <section className="border-y border-white/5 py-5 overflow-hidden">
        <div className="flex animate-ticker whitespace-nowrap">
          {[...partners, ...partners].map((name, i) => (
            <span key={i} className="mx-12 text-sm text-white/15 font-medium tracking-wide uppercase flex-shrink-0">
              {name}
            </span>
          ))}
        </div>
      </section>

      {/* ═══ SOLUTIONS FOR EVERY SEGMENT ═══ */}
      <section id="solutions" className="py-28 px-6">
        <div className="max-w-7xl mx-auto">
          <RevealBlock>
            <div className="max-w-2xl mb-16">
              <span className="text-xs text-nexus-cyan tracking-widest uppercase font-medium">Solutions</span>
              <h2 className="text-4xl sm:text-5xl font-bold mt-4 gradient-text leading-tight">
                Credit Intelligence for Every Lending Vertical
              </h2>
              <p className="text-white/40 mt-4 leading-relaxed">
                Purpose-built credit decisioning workflows for corporate lending, MSME finance, trade finance, and infrastructure projects — all powered by the same AI engine.
              </p>
            </div>
          </RevealBlock>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {solutions.map((s, i) => (
              <RevealBlock key={i} delay={i * 100}>
                <div className="group glass rounded-2xl p-6 h-full transition-all duration-300 hover:bg-white/[0.04] hover:border-white/10 cursor-pointer">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-nexus-cyan/5 border border-nexus-cyan/10 mb-5 group-hover:bg-nexus-cyan/10 group-hover:border-nexus-cyan/20 transition-all">
                    <s.icon size={22} className="text-nexus-cyan/70 group-hover:text-nexus-cyan transition-colors" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{s.title}</h3>
                  <p className="text-sm text-white/35 leading-relaxed">{s.desc}</p>
                  <div className="mt-5 flex items-center gap-1 text-xs text-nexus-cyan/60 group-hover:text-nexus-cyan transition-colors">
                    <span>Learn more</span>
                    <ChevronRight size={12} />
                  </div>
                </div>
              </RevealBlock>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ METRICS BAR ═══ */}
      <section className="py-16 border-y border-white/5 bg-white/[0.01]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
            {[
              { value: 94, suffix: '%', label: 'Model Accuracy (AUC-ROC)' },
              { value: 180, suffix: 's', label: 'Average Decision Time' },
              { value: 80, suffix: '+', label: 'Engineered Features' },
              { value: 10, suffix: '', label: 'CAM Sections Generated' },
              { value: 15, suffix: '', label: 'EWS Trigger Signals' },
            ].map((m, i) => (
              <RevealBlock key={i} delay={i * 80}>
                <div className="text-center">
                  <div className="text-3xl sm:text-4xl font-bold font-mono tracking-tight text-white">
                    <Counter target={m.value} suffix={m.suffix} />
                  </div>
                  <div className="text-xs text-white/30 mt-2 uppercase tracking-wider leading-tight">{m.label}</div>
                </div>
              </RevealBlock>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ PLATFORM CAPABILITIES ═══ */}
      <section id="platform" className="py-28 px-6">
        <div className="max-w-7xl mx-auto">
          <RevealBlock>
            <div className="text-center mb-16">
              <span className="text-xs text-nexus-cyan tracking-widest uppercase font-medium">Platform</span>
              <h2 className="text-4xl sm:text-5xl font-bold mt-4 gradient-text">
                End-to-End Credit Intelligence
              </h2>
              <p className="text-white/40 mt-4 max-w-2xl mx-auto">
                Every component engineered for speed, accuracy, and regulatory compliance across the entire credit lifecycle.
              </p>
            </div>
          </RevealBlock>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {capabilities.map((f, i) => (
              <RevealBlock key={i} delay={i * 60}>
                <div className="group glass glass-hover rounded-2xl p-6 h-full transition-all duration-300">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 border border-white/10 mb-4 group-hover:border-nexus-cyan/30 transition-colors">
                    <f.icon size={20} className="text-white/50 group-hover:text-nexus-cyan transition-colors" />
                  </div>
                  <h3 className="text-base font-semibold mb-2">{f.title}</h3>
                  <p className="text-sm text-white/35 leading-relaxed">{f.desc}</p>
                </div>
              </RevealBlock>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ HOW IT WORKS — SPLIT LAYOUT ═══ */}
      <section id="how-it-works" className="py-28 px-6 border-y border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            {/* Left — Text + Steps */}
            <RevealBlock>
              <div>
                <span className="text-xs text-nexus-cyan tracking-widest uppercase font-medium">How It Works</span>
                <h2 className="text-4xl sm:text-5xl font-bold mt-4 gradient-text leading-tight">
                  From Data to Decision in Five Steps
                </h2>
                <p className="text-white/40 mt-4 leading-relaxed mb-10">
                  Our autonomous pipeline processes applications end-to-end. No manual intervention required — each agent hands off to the next seamlessly.
                </p>
                <div className="space-y-5">
                  {[
                    { step: '01', title: 'Data Ingestion', desc: 'Financial statements, bureau data, and MCA records auto-extracted via DuckDB and API connectors.', color: 'text-blue-400' },
                    { step: '02', title: 'Financial Analysis', desc: 'Altman Z-Score, Piotroski F-Score, Beneish M-Score computed. 80+ features engineered.', color: 'text-purple-400' },
                    { step: '03', title: 'Market Intelligence', desc: 'Real-time news sentiment, regulatory flags, and industry benchmarking via web research.', color: 'text-cyan-400' },
                    { step: '04', title: 'Risk Scoring', desc: 'XGBoost + LightGBM ensemble produces calibrated PD, Expected Loss, and credit grade.', color: 'text-green-400' },
                    { step: '05', title: 'CAM Generation', desc: '10-section Credit Appraisal Memo generated with complete analysis and recommendations.', color: 'text-amber-400' },
                  ].map((s, i) => (
                    <div key={i} className="flex gap-4 items-start group">
                      <div className="flex-shrink-0 w-10 text-right">
                        <span className={`text-xs font-mono font-bold ${s.color} opacity-60`}>{s.step}</span>
                      </div>
                      <div className="flex-1 pb-5 border-b border-white/5 last:border-0">
                        <h4 className="font-semibold text-sm text-white/90">{s.title}</h4>
                        <p className="text-xs text-white/35 mt-1 leading-relaxed">{s.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </RevealBlock>

            {/* Right — Code Block */}
            <RevealBlock delay={200}>
              <div className="glass rounded-2xl overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-white/[0.02]">
                  <div className="h-3 w-3 rounded-full bg-nexus-red/50" />
                  <div className="h-3 w-3 rounded-full bg-nexus-amber/50" />
                  <div className="h-3 w-3 rounded-full bg-nexus-green/50" />
                  <span className="ml-3 text-xs text-white/25 font-mono">orchestrator.py</span>
                </div>
                <pre className="p-6 text-[13px] font-mono leading-relaxed overflow-x-auto text-white/60">
                  <code>{`pipeline = CreditAnalysisPipeline(case_id)

# Five autonomous agents execute in sequence
await pipeline.run([
  DataIngestorAgent(),      # DuckDB + MCA + Bureau
  FinancialAnalystAgent(),  # Ratios + DCF + 80 features
  WebResearchAgent(),       # Tavily + News Sentiment
  RiskAssessmentAgent(),    # PD / LGD / EAD + SHAP
  CAMWriterAgent(),         # Streaming CAM generation
])

# Output
# ├─ Credit Grade:  AA-
# ├─ Approved Limit: ₹25.00 Cr
# ├─ Interest Rate:  11.25% p.a.
# ├─ Expected Loss:  ₹1.87 Lakh
# └─ CAM:            10 sections generated`}</code>
                </pre>
              </div>
            </RevealBlock>
          </div>
        </div>
      </section>

      {/* ═══ COMPARISON — BEFORE / AFTER ═══ */}
      <section className="py-28 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            {/* Left — Comparison Cards */}
            <RevealBlock>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div className="glass rounded-2xl p-7">
                  <div className="text-nexus-red/70 text-xs uppercase tracking-wider font-semibold mb-6">Traditional Process</div>
                  <div className="space-y-5">
                    <div><span className="text-3xl font-bold font-mono">3–6</span><span className="text-white/35 ml-2 text-sm">Weeks</span></div>
                    <div><span className="text-3xl font-bold font-mono">8–12</span><span className="text-white/35 ml-2 text-sm">Analysts</span></div>
                    <div><span className="text-3xl font-bold font-mono">₹85K</span><span className="text-white/35 ml-2 text-sm">Per Appraisal</span></div>
                    <div><span className="text-3xl font-bold font-mono">23%</span><span className="text-white/35 ml-2 text-sm">Drop-off Rate</span></div>
                  </div>
                </div>
                <div className="glass rounded-2xl p-7 glow-border">
                  <div className="text-nexus-cyan text-xs uppercase tracking-wider font-semibold mb-6">With NEXUS CREDIT</div>
                  <div className="space-y-5">
                    <div><span className="text-3xl font-bold font-mono text-nexus-cyan">3</span><span className="text-white/35 ml-2 text-sm">Minutes</span></div>
                    <div><span className="text-3xl font-bold font-mono text-nexus-cyan">0</span><span className="text-white/35 ml-2 text-sm">Manual Steps</span></div>
                    <div><span className="text-3xl font-bold font-mono text-nexus-cyan">₹12</span><span className="text-white/35 ml-2 text-sm">Per Appraisal</span></div>
                    <div><span className="text-3xl font-bold font-mono text-nexus-cyan">&lt;1%</span><span className="text-white/35 ml-2 text-sm">Drop-off Rate</span></div>
                  </div>
                </div>
              </div>
            </RevealBlock>

            {/* Right — Text */}
            <RevealBlock delay={150}>
              <div>
                <span className="text-xs text-nexus-cyan tracking-widest uppercase font-medium">Why NEXUS CREDIT</span>
                <h2 className="text-4xl sm:text-5xl font-bold mt-4 gradient-text leading-tight">
                  Reduce Credit Turnaround from Weeks to Minutes
                </h2>
                <p className="text-white/40 mt-6 leading-relaxed">
                  Traditional credit appraisal involves teams of analysts manually spreading financials, pulling bureau reports, writing memos, and routing approvals over weeks. NEXUS CREDIT compresses this entire workflow into a single autonomous pipeline.
                </p>
                <div className="mt-8 space-y-3">
                  {[
                    'RBI-compliant AI decisioning with full audit trail',
                    'Basel II-calibrated probability of default modelling',
                    'SHAP-based explainability for every credit decision',
                    'Auto-generated CAM accepted by credit committees',
                  ].map((item, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <CheckCircle2 size={16} className="text-nexus-green/60 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-white/50">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </RevealBlock>
          </div>
        </div>
      </section>

      {/* ═══ DEVELOPER / API INTEGRATION ═══ */}
      <section id="integrate" className="py-28 px-6 border-y border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            {/* Left — Text */}
            <RevealBlock>
              <div>
                <span className="text-xs text-nexus-cyan tracking-widest uppercase font-medium">Integration</span>
                <h2 className="text-4xl sm:text-5xl font-bold mt-4 gradient-text leading-tight">
                  Built for Developers. Ready for Production.
                </h2>
                <p className="text-white/40 mt-4 leading-relaxed mb-8">
                  Integrate credit decisioning into your loan origination system with a single API call. RESTful endpoints for case creation, analysis triggering, and CAM retrieval.
                </p>
                <div className="flex flex-wrap gap-3">
                  {[
                    { icon: Database, label: 'DuckDB' },
                    { icon: Globe, label: 'REST API' },
                    { icon: Zap, label: 'WebSocket' },
                    { icon: FileText, label: 'PDF Export' },
                    { icon: Shield, label: 'SHAP' },
                    { icon: Brain, label: 'Claude AI' },
                  ].map((t, i) => (
                    <div key={i} className="flex items-center gap-2 rounded-full bg-white/5 border border-white/8 px-4 py-2">
                      <t.icon size={14} className="text-white/40" />
                      <span className="text-xs text-white/50 font-medium">{t.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </RevealBlock>

            {/* Right — API Code */}
            <RevealBlock delay={200}>
              <div className="glass rounded-2xl overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-white/[0.02]">
                  <span className="text-xs text-white/25 font-mono">API Integration</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-nexus-green/60 font-mono">200 OK</span>
                    <div className="h-2 w-2 rounded-full bg-nexus-green/40" />
                  </div>
                </div>
                <pre className="p-6 text-[13px] font-mono leading-relaxed overflow-x-auto text-white/60">
                  <code>{`# Create a credit analysis case
POST /api/v1/cases
{
  "company_name": "Tata Steel Ltd",
  "cin": "L27100MH1907PLC000260",
  "loan_type": "TERM_LOAN",
  "requested_amount": 250000000,
  "tenure_months": 60
}

# Trigger autonomous analysis
POST /api/v1/cases/{case_id}/analyze

# Retrieve credit decision
GET /api/v1/cases/{case_id}/decision
→ {
    "verdict": "APPROVE",
    "credit_grade": "AA-",
    "pd_score": 0.0023,
    "recommended_limit_cr": 25.00,
    "rate": 11.25
  }

# Download generated CAM
GET /api/v1/cases/{case_id}/cam/pdf`}</code>
                </pre>
              </div>
            </RevealBlock>
          </div>
        </div>
      </section>

      {/* ═══ DATA ECOSYSTEM TICKER ═══ */}
      <section className="py-16 px-6">
        <div className="max-w-7xl mx-auto">
          <RevealBlock>
            <div className="text-center mb-10">
              <span className="text-xs text-white/25 tracking-widest uppercase font-medium">Data Ecosystem</span>
            </div>
          </RevealBlock>
          <div className="flex flex-wrap justify-center gap-x-12 gap-y-4">
            {['DuckDB', 'Databricks', 'CIBIL Bureau', 'MCA Portal', 'Tavily Search', 'SEBI', 'RBI', 'NCLT', 'BSE/NSE'].map((src, i) => (
              <RevealBlock key={i} delay={i * 50}>
                <span className="text-sm text-white/15 font-medium tracking-wide uppercase whitespace-nowrap">{src}</span>
              </RevealBlock>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ BOTTOM CTA ═══ */}
      <section className="py-32 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <RevealBlock>
            <h2 className="text-4xl sm:text-5xl font-bold gradient-text leading-tight mb-6">
              Ready to Modernise Your Credit Appraisal?
            </h2>
            <p className="text-white/35 text-lg mb-10 max-w-xl mx-auto leading-relaxed">
              Deploy autonomous credit intelligence in your lending workflow. Start analysing cases in minutes, not weeks.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => navigate('/intake')}
                className="group inline-flex items-center gap-3 rounded-full bg-white text-black px-10 py-4 text-sm font-semibold transition-all hover:bg-white/90 hover:shadow-[0_0_40px_rgba(255,255,255,0.15)]"
              >
                Start Credit Analysis
                <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center gap-3 rounded-full border border-white/15 px-10 py-4 text-sm font-medium text-white/60 transition-all hover:border-white/30 hover:text-white"
              >
                View Dashboard
                <ChevronRight size={16} />
              </button>
            </div>
          </RevealBlock>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="border-t border-white/5 pt-16 pb-10 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-10 mb-16">
            {/* Brand */}
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-nexus-cyan/10 border border-nexus-cyan/20">
                  <span className="text-nexus-cyan font-bold text-sm font-mono">N</span>
                </div>
                <span className="text-sm font-semibold tracking-tight">
                  NEXUS <span className="text-nexus-cyan">CREDIT</span>
                </span>
              </div>
              <p className="text-xs text-white/25 leading-relaxed">
                AI-powered autonomous credit decisioning engine for Indian commercial banking.
              </p>
            </div>

            {/* Platform */}
            <div>
              <h4 className="text-xs text-white/50 uppercase tracking-wider font-semibold mb-4">Platform</h4>
              <ul className="space-y-2.5">
                <li><button onClick={() => navigate('/dashboard')} className="text-xs text-white/30 hover:text-white/60 transition-colors">Dashboard</button></li>
                <li><button onClick={() => navigate('/intake')} className="text-xs text-white/30 hover:text-white/60 transition-colors">New Analysis</button></li>
                <li><span className="text-xs text-white/30">Credit Decision</span></li>
                <li><span className="text-xs text-white/30">CAM Viewer</span></li>
              </ul>
            </div>

            {/* Capabilities */}
            <div>
              <h4 className="text-xs text-white/50 uppercase tracking-wider font-semibold mb-4">Capabilities</h4>
              <ul className="space-y-2.5">
                <li><span className="text-xs text-white/30">AI Agent Swarm</span></li>
                <li><span className="text-xs text-white/30">ML Ensemble Scoring</span></li>
                <li><span className="text-xs text-white/30">SHAP Explainability</span></li>
                <li><span className="text-xs text-white/30">Early Warning System</span></li>
              </ul>
            </div>

            {/* Technology */}
            <div>
              <h4 className="text-xs text-white/50 uppercase tracking-wider font-semibold mb-4">Technology</h4>
              <ul className="space-y-2.5">
                <li><span className="text-xs text-white/30">FastAPI Backend</span></li>
                <li><span className="text-xs text-white/30">React Frontend</span></li>
                <li><span className="text-xs text-white/30">XGBoost + LightGBM</span></li>
                <li><span className="text-xs text-white/30">Claude AI (Anthropic)</span></li>
              </ul>
            </div>

            {/* Compliance */}
            <div>
              <h4 className="text-xs text-white/50 uppercase tracking-wider font-semibold mb-4">Compliance</h4>
              <ul className="space-y-2.5">
                <li><span className="text-xs text-white/30">RBI Guidelines</span></li>
                <li><span className="text-xs text-white/30">Basel II Framework</span></li>
                <li><span className="text-xs text-white/30">IND AS Standards</span></li>
                <li><span className="text-xs text-white/30">SEBI Regulations</span></li>
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="border-t border-white/5 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-xs text-white/20">
              &copy; 2026 NEXUS CREDIT. Autonomous Credit Intelligence Platform.
            </div>
            <div className="flex items-center gap-6 text-xs text-white/20">
              <span>Privacy Policy</span>
              <span>Terms of Service</span>
              <span>API Documentation</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

/* ─── Reveal Block Wrapper ─── */
function RevealBlock({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const { ref, vis } = useReveal();
  return (
    <div
      ref={ref}
      className="transition-all duration-700"
      style={{
        opacity: vis ? 1 : 0,
        transform: vis ? 'translateY(0)' : 'translateY(30px)',
        transitionDelay: `${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}
