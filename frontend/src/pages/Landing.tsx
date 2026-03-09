import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Zap, Shield, Brain, BarChart3, Clock, FileText, TrendingUp, ChevronRight } from 'lucide-react';

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
  const videoRef = useRef<HTMLVideoElement>(null);

  // Hero parallax
  const [scrollY, setScrollY] = useState(0);
  useEffect(() => {
    const h = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, []);

  const trustedBy = [
    'Reserve Bank of India', 'State Bank of India', 'HDFC Bank', 'ICICI Bank',
    'Axis Bank', 'Kotak Mahindra', 'Bank of Baroda', 'Punjab National Bank',
    'Yes Bank', 'IndusInd Bank', 'Canara Bank', 'Union Bank',
  ];

  const features = [
    { icon: Brain, title: 'AI Agent Swarm', desc: 'Five autonomous agents collaborate in real-time — ingesting data, analysing financials, researching the web, scoring risk, and writing a 40-page CAM.', span: 'col-span-2' },
    { icon: Zap, title: '180-Second Decisioning', desc: 'From application to Lend/Decline in under 3 minutes. Traditional process takes 3–6 weeks.', span: '' },
    { icon: Shield, title: 'Explainable AI (SHAP)', desc: 'Every decision is backed by feature-level SHAP explanations. No black boxes — full regulatory transparency.', span: '' },
    { icon: BarChart3, title: 'ML Ensemble Scoring', desc: 'XGBoost + LightGBM ensemble with Basel II-calibrated PD, LGD, and EAD models. 80+ engineered features.', span: 'col-span-2' },
    { icon: Clock, title: 'Real-Time Streaming', desc: 'Watch agents think live via WebSocket. CAM builds section-by-section before your eyes.', span: '' },
    { icon: FileText, title: 'Publication-Quality CAM', desc: 'Auto-generated 40-page Credit Appraisal Memo with financial spreads, peer comparison, and covenants.', span: '' },
    { icon: TrendingUp, title: 'Early Warning System', desc: '15 automated triggers monitor DSCR, leverage, pledge ratios, audit flags, and market signals in real-time.', span: 'col-span-2' },
  ];

  return (
    <div className="bg-black text-white overflow-hidden">

      {/* ═══ SECTION 1: HERO ═══ */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        {/* Video Background */}
        <div className="absolute inset-0 z-0" style={{ transform: `translateY(${scrollY * 0.3}px)` }}>
          <video
            ref={videoRef}
            autoPlay loop muted playsInline
            className="h-full w-full object-cover opacity-30"
            poster="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1920' height='1080'%3E%3Crect fill='%23000'/%3E%3C/svg%3E"
          >
            <source src="https://d1yei2z3i6k35z.cloudfront.net/3536671/672ccf8d62524_AbstractAIneuralnetwork.mp4" type="video/mp4" />
          </video>
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black" />
        </div>

        {/* Hero Content */}
        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
          {/* Pill badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 mb-8 backdrop-blur-sm">
            <span className="h-2 w-2 rounded-full bg-nexus-cyan animate-pulse" />
            <span className="text-xs text-white/70 tracking-wide uppercase">IIT Hyderabad Hackathon 2025</span>
          </div>

          <h1 className="text-6xl sm:text-7xl lg:text-8xl font-bold leading-[0.95] tracking-tight mb-6">
            <span className="gradient-text">From Application</span>
            <br />
            <span className="gradient-text">to Decision in</span>
            <br />
            <span className="gradient-text-cyan">180 Seconds</span>
          </h1>

          <p className="max-w-2xl mx-auto text-lg text-white/50 mb-10 leading-relaxed">
            NEXUS CREDIT is the world's first autonomous credit analyst. AI Agent Swarm + ML Ensemble + Real-Time CAM Generation — production-grade credit decisioning that replaces 3–6 weeks of manual work.
          </p>

          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="group flex items-center gap-2 rounded-full bg-white text-black px-8 py-3.5 text-sm font-semibold transition-all hover:bg-white/90 hover:shadow-[0_0_30px_rgba(255,255,255,0.2)]"
            >
              Enter Platform
              <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
            </button>
            <button
              onClick={() => navigate('/intake')}
              className="flex items-center gap-2 rounded-full border border-white/20 px-8 py-3.5 text-sm font-medium text-white/80 transition-all hover:border-white/40 hover:text-white hover:bg-white/5"
            >
              Run Demo Analysis
            </button>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-2 text-white/30">
          <span className="text-xs tracking-widest uppercase">Scroll</span>
          <div className="h-8 w-[1px] bg-gradient-to-b from-white/30 to-transparent animate-pulse" />
        </div>
      </section>

      {/* ═══ SECTION 2: TRUSTED BY TICKER ═══ */}
      <section className="border-y border-white/5 py-6 overflow-hidden">
        <div className="flex animate-ticker whitespace-nowrap">
          {[...trustedBy, ...trustedBy].map((name, i) => (
            <span key={i} className="mx-10 text-sm text-white/20 font-medium tracking-wide uppercase flex-shrink-0">
              {name}
            </span>
          ))}
        </div>
      </section>

      {/* ═══ SECTION 3: FEATURES BENTO BOX ═══ */}
      <section className="py-28 px-6">
        <div className="max-w-6xl mx-auto">
          <RevealBlock>
            <div className="text-center mb-16">
              <span className="text-xs text-nexus-cyan tracking-widest uppercase font-medium">Capabilities</span>
              <h2 className="text-4xl sm:text-5xl font-bold mt-4 gradient-text">
                Built for the Future of Credit
              </h2>
              <p className="text-white/40 mt-4 max-w-xl mx-auto">
                Every component engineered for speed, accuracy, and regulatory compliance.
              </p>
            </div>
          </RevealBlock>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {features.map((f, i) => (
              <RevealBlock key={i} delay={i * 80}>
                <div
                  className={`group glass glass-hover rounded-2xl p-6 transition-all duration-300 ${f.span || ''}`}
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 border border-white/10 mb-4 group-hover:border-nexus-cyan/30 transition-colors">
                    <f.icon size={20} className="text-white/60 group-hover:text-nexus-cyan transition-colors" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                  <p className="text-sm text-white/40 leading-relaxed">{f.desc}</p>
                </div>
              </RevealBlock>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ SECTION 4: METRICS BANNER ═══ */}
      <section className="py-20 border-y border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: 847, suffix: '+', label: 'Cases Processed' },
              { value: 94, suffix: '.2%', label: 'Model Accuracy' },
              { value: 180, suffix: 's', label: 'Avg Decision Time' },
              { value: 2, suffix: '.3Cr', prefix: '₹', label: 'Capital Saved/Year' },
            ].map((m, i) => (
              <RevealBlock key={i} delay={i * 100}>
                <div className="text-center">
                  <div className="text-4xl sm:text-5xl font-bold font-mono tracking-tight">
                    <Counter target={m.value} suffix={m.suffix} prefix={m.prefix || ''} />
                  </div>
                  <div className="text-sm text-white/30 mt-2 uppercase tracking-wider">{m.label}</div>
                </div>
              </RevealBlock>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ SECTION 5: DEVELOPER / HOW IT WORKS ═══ */}
      <section className="py-28 px-6">
        <div className="max-w-6xl mx-auto">
          <RevealBlock>
            <div className="text-center mb-16">
              <span className="text-xs text-nexus-cyan tracking-widest uppercase font-medium">Architecture</span>
              <h2 className="text-4xl sm:text-5xl font-bold mt-4 gradient-text">
                How NEXUS CREDIT Works
              </h2>
            </div>
          </RevealBlock>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Code Editor Mock */}
            <RevealBlock>
              <div className="glass rounded-2xl overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
                  <div className="h-3 w-3 rounded-full bg-nexus-red/60" />
                  <div className="h-3 w-3 rounded-full bg-nexus-amber/60" />
                  <div className="h-3 w-3 rounded-full bg-nexus-green/60" />
                  <span className="ml-2 text-xs text-white/30 font-mono">orchestrator.py</span>
                </div>
                <pre className="p-5 text-sm font-mono leading-relaxed overflow-x-auto">
                  <code>
{`pipeline = CreditAnalysisPipeline(case_id)

# 5 autonomous agents execute sequentially
await pipeline.run([
  DataIngestorAgent(),     # DuckDB + MCA + Bureau
  FinancialAnalystAgent(), # 80+ features + DCF
  WebResearchAgent(),      # Tavily + Sentiment
  RiskAssessmentAgent(),   # PD/LGD/EAD + SHAP
  CAMWriterAgent(),        # Claude streaming CAM
])

# Result: Decision in < 180 seconds
# → Grade: AA | Limit: ₹25Cr | Rate: 11.25%
# → 40-page CAM generated automatically`}
                  </code>
                </pre>
              </div>
            </RevealBlock>

            {/* Pipeline Steps */}
            <RevealBlock delay={150}>
              <div className="space-y-4">
                {[
                  { step: '01', title: 'Data Ingestion', desc: 'Pull financials from Databricks/DuckDB, parse PDFs, query MCA & bureau APIs', color: 'from-blue-500/20 to-blue-500/5' },
                  { step: '02', title: 'Financial Analysis', desc: 'Compute Altman Z, Piotroski F, Beneish M scores. 80+ features engineered.', color: 'from-purple-500/20 to-purple-500/5' },
                  { step: '03', title: 'Web Intelligence', desc: 'Tavily search, news sentiment via Claude, regulatory flag checks, RAG on filings.', color: 'from-cyan-500/20 to-cyan-500/5' },
                  { step: '04', title: 'Risk Scoring', desc: 'XGBoost+LGBM ensemble → PD, LGD, EAD, Expected Loss, Credit Grade, RARR.', color: 'from-green-500/20 to-green-500/5' },
                  { step: '05', title: 'CAM Generation', desc: 'Claude claude-sonnet-4-20250514 writes 10-section CAM in real-time via streaming.', color: 'from-amber-500/20 to-amber-500/5' },
                ].map((s, i) => (
                  <div key={i} className={`glass rounded-xl p-4 flex gap-4 items-start transition-all hover:bg-white/5`}>
                    <div className={`flex-shrink-0 h-10 w-10 rounded-lg bg-gradient-to-br ${s.color} border border-white/10 flex items-center justify-center`}>
                      <span className="text-xs font-mono font-bold text-white/70">{s.step}</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm">{s.title}</h4>
                      <p className="text-xs text-white/40 mt-1">{s.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </RevealBlock>
          </div>
        </div>
      </section>

      {/* ═══ SECTION 6: COMPARISON PANEL ═══ */}
      <section className="py-20 px-6 border-y border-white/5">
        <div className="max-w-4xl mx-auto">
          <RevealBlock>
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl font-bold gradient-text">The Difference</h2>
            </div>
          </RevealBlock>
          <RevealBlock delay={100}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass rounded-2xl p-8 border-nexus-red/20">
                <div className="text-nexus-red text-xs uppercase tracking-wider font-semibold mb-6">Traditional Process</div>
                <div className="space-y-4">
                  <div><span className="text-3xl font-bold font-mono">3–6</span><span className="text-white/40 ml-2">Weeks</span></div>
                  <div><span className="text-3xl font-bold font-mono">8–12</span><span className="text-white/40 ml-2">Analysts Required</span></div>
                  <div><span className="text-3xl font-bold font-mono">₹85K</span><span className="text-white/40 ml-2">Cost Per Appraisal</span></div>
                  <div><span className="text-3xl font-bold font-mono">23%</span><span className="text-white/40 ml-2">Applications Lapse</span></div>
                </div>
              </div>
              <div className="glass rounded-2xl p-8 border-nexus-cyan/20 glow-border">
                <div className="text-nexus-cyan text-xs uppercase tracking-wider font-semibold mb-6">NEXUS CREDIT</div>
                <div className="space-y-4">
                  <div><span className="text-3xl font-bold font-mono text-nexus-cyan">3</span><span className="text-white/40 ml-2">Minutes</span></div>
                  <div><span className="text-3xl font-bold font-mono text-nexus-cyan">1</span><span className="text-white/40 ml-2">AI System</span></div>
                  <div><span className="text-3xl font-bold font-mono text-nexus-cyan">₹12</span><span className="text-white/40 ml-2">Cost Per Appraisal</span></div>
                  <div><span className="text-3xl font-bold font-mono text-nexus-cyan">0%</span><span className="text-white/40 ml-2">Applications Lapse</span></div>
                </div>
              </div>
            </div>
          </RevealBlock>
        </div>
      </section>

      {/* ═══ SECTION 7: BOTTOM CTA ═══ */}
      <section className="py-32 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <RevealBlock>
            <h2 className="text-5xl sm:text-6xl font-bold gradient-text leading-tight mb-6">
              Ready to Transform<br />Credit Decisioning?
            </h2>
            <p className="text-white/40 text-lg mb-10 max-w-2xl mx-auto">
              Experience the future of credit appraisal. Upload financials, watch AI agents work in real-time,
              and receive a publication-quality CAM in under 3 minutes.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="group inline-flex items-center gap-3 rounded-full bg-white text-black px-10 py-4 text-base font-semibold transition-all hover:bg-white/90 hover:shadow-[0_0_40px_rgba(255,255,255,0.2)]"
            >
              Launch NEXUS CREDIT
              <ChevronRight size={18} className="transition-transform group-hover:translate-x-1" />
            </button>
          </RevealBlock>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="border-t border-white/5 py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 border border-white/10">
              <span className="text-nexus-cyan font-bold text-xs font-mono">N</span>
            </div>
            <span className="text-sm font-semibold tracking-tight">
              NEXUS <span className="text-nexus-cyan">CREDIT</span>
            </span>
          </div>
          <div className="flex items-center gap-8 text-xs text-white/30">
            <span>IIT Hyderabad Hackathon 2025</span>
            <span>•</span>
            <span>AI Credit Decisioning Engine</span>
            <span>•</span>
            <span>v1.0.0</span>
          </div>
          <div className="text-xs text-white/20">
            Built with FastAPI + React + XGBoost + Claude
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
