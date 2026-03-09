import { useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Database, LineChart, Globe, ShieldCheck, FileText, CheckCircle2, Loader2, ArrowRight, Sparkles } from 'lucide-react';
import { fetchCase, triggerAnalysis } from '../lib/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAgentStore } from '../store';
import clsx from 'clsx';

const AGENTS = [
  { key: 'DataIngestor', label: 'Data Ingestion', icon: Database, color: 'from-blue-500/20 to-blue-500/5', text: 'text-blue-400' },
  { key: 'FinancialAnalyst', label: 'Financial Analysis', icon: LineChart, color: 'from-purple-500/20 to-purple-500/5', text: 'text-purple-400' },
  { key: 'WebResearch', label: 'Web Intelligence', icon: Globe, color: 'from-cyan-500/20 to-cyan-500/5', text: 'text-cyan-400' },
  { key: 'RiskAssessment', label: 'Risk Assessment', icon: ShieldCheck, color: 'from-green-500/20 to-green-500/5', text: 'text-green-400' },
  { key: 'CAMWriter', label: 'CAM Generation', icon: FileText, color: 'from-amber-500/20 to-amber-500/5', text: 'text-amber-400' },
];

const CAM_SECTIONS = [
  'executive_summary', 'company_background', 'industry_analysis',
  'financial_analysis', 'banking_conduct', 'collateral_assessment',
  'risk_assessment', 'credit_decision', 'covenants_conditions', 'appendices',
];

function sectionLabel(key: string) {
  return key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

export default function LiveAnalysis() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const { events, camSections, currentAgent, isComplete } = useAgentStore();
  useWebSocket(caseId);

  const { data: caseData } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => fetchCase(caseId!),
    enabled: !!caseId,
  });

  // Auto-trigger analysis if case is in INTAKE status
  useEffect(() => {
    if (caseData?.status === 'INTAKE' && caseId) {
      triggerAnalysis(caseId).catch(() => {});
    }
  }, [caseData?.status, caseId]);

  const feedRef = useRef<HTMLDivElement>(null);
  const camRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' });
  }, [events]);
  useEffect(() => {
    camRef.current?.scrollTo({ top: camRef.current.scrollHeight, behavior: 'smooth' });
  }, [camSections]);

  const completedAgents = new Set<string>();
  events.forEach(e => {
    if (e.type === 'agent_complete' && e.agent) completedAgents.add(e.agent);
  });

  // Extract metrics from events
  const metrics: { label: string; value: string }[] = [];
  events.forEach(e => {
    if (e.type === 'metric' && e.data) {
      const d = e.data as { label?: string; value?: string };
      if (d.label && d.value) metrics.push({ label: d.label, value: d.value });
    }
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-3">
            <Sparkles size={20} className="text-nexus-cyan" />
            Live Analysis
          </h1>
          <p className="text-sm text-white/40 mt-1">
            {caseData?.company_name ?? 'Loading...'} — {caseData?.case_number ?? ''}
          </p>
        </div>
        {isComplete && (
          <button
            onClick={() => navigate(`/cases/${caseId}/decision`)}
            className="flex items-center gap-2 rounded-xl bg-nexus-green text-black px-6 py-2.5 text-sm font-bold transition-all hover:bg-nexus-green/90 animate-fade-in"
          >
            View Decision <ArrowRight size={14} />
          </button>
        )}
      </div>

      {/* Agent Progress Bar */}
      <div className="flex items-center gap-2">
        {AGENTS.map((a) => {
          const done = completedAgents.has(a.key);
          const active = currentAgent === a.key;
          return (
            <div
              key={a.key}
              className={clsx(
                'flex-1 flex items-center gap-2 rounded-xl border p-3 transition-all',
                done ? 'border-nexus-green/30 bg-nexus-green/5' :
                active ? 'border-nexus-cyan/30 bg-nexus-cyan/5' :
                'border-white/5 bg-white/[0.02]',
              )}
            >
              {done ? (
                <CheckCircle2 size={16} className="text-nexus-green flex-shrink-0" />
              ) : active ? (
                <Loader2 size={16} className="text-nexus-cyan animate-spin flex-shrink-0" />
              ) : (
                <a.icon size={16} className="text-white/20 flex-shrink-0" />
              )}
              <span className={clsx('text-xs font-medium truncate', done ? 'text-nexus-green' : active ? 'text-nexus-cyan' : 'text-white/30')}>
                {a.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Split Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4" style={{ height: 'calc(100vh - 280px)' }}>

        {/* LEFT: Agent Feed */}
        <div className="lg:col-span-2 rounded-xl border border-nexus-dark-border bg-nexus-dark-card flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-nexus-dark-border flex items-center justify-between">
            <span className="text-xs font-medium text-white/50">Agent Activity</span>
            <span className="text-xs text-white/20 font-mono">{events.length} events</span>
          </div>
          <div ref={feedRef} className="flex-1 overflow-y-auto p-4 space-y-3">
            {events.filter(e => e.type !== 'cam_stream' && e.type !== 'pong').map((e, i) => (
              <AgentEventCard key={i} event={e} />
            ))}
            {events.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-white/20">
                <Loader2 size={24} className="animate-spin mb-3" />
                <p className="text-sm">Waiting for agents to start...</p>
              </div>
            )}
          </div>

          {/* Mini Metrics */}
          {metrics.length > 0 && (
            <div className="border-t border-nexus-dark-border p-3 flex flex-wrap gap-2">
              {metrics.slice(-6).map((m, i) => (
                <span key={i} className="inline-flex items-center gap-1 rounded-full bg-nexus-green/10 text-nexus-green px-3 py-1 text-xs font-mono">
                  {m.label}: {m.value} ✓
                </span>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT: Live CAM Preview */}
        <div className="lg:col-span-3 rounded-xl border border-nexus-dark-border bg-nexus-dark-card flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-nexus-dark-border flex items-center justify-between">
            <span className="text-xs font-medium text-white/50">CAM Preview</span>
            <span className="text-xs text-white/20">{Object.keys(camSections).length}/{CAM_SECTIONS.length} sections</span>
          </div>
          <div ref={camRef} className="flex-1 overflow-y-auto p-6">
            {Object.keys(camSections).length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-white/20">
                <FileText size={32} className="mb-3 opacity-30" />
                <p className="text-sm">CAM will appear here as it's generated...</p>
              </div>
            ) : (
              <div className="space-y-6">
                {CAM_SECTIONS.map(key => {
                  const content = camSections[key];
                  if (!content) return null;
                  return (
                    <div key={key} className="animate-fade-in">
                      <div className="flex items-center gap-2 mb-3">
                        <CheckCircle2 size={14} className="text-nexus-green" />
                        <h3 className="text-sm font-semibold text-white/70">{sectionLabel(key)}</h3>
                      </div>
                      <div className="rounded-lg bg-white/[0.02] border border-white/5 p-4 text-sm text-white/60 leading-relaxed whitespace-pre-wrap font-serif">
                        {content}
                        <span className="inline-block w-px h-4 bg-nexus-cyan animate-pulse ml-0.5" />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function AgentEventCard({ event }: { event: import('../types').AgentEvent }) {
  const agentInfo = AGENTS.find(a => a.key === event.agent);
  const Icon = agentInfo?.icon ?? Database;

  if (event.type === 'pipeline_start') {
    return (
      <div className="flex items-center gap-2 text-nexus-cyan text-xs p-2 rounded-lg bg-nexus-cyan/5 border border-nexus-cyan/10">
        <Sparkles size={14} /> Pipeline started
      </div>
    );
  }
  if (event.type === 'pipeline_complete') {
    return (
      <div className="flex items-center gap-2 text-nexus-green text-xs p-2 rounded-lg bg-nexus-green/5 border border-nexus-green/10">
        <CheckCircle2 size={14} /> Analysis complete!
      </div>
    );
  }

  return (
    <div className="flex gap-3 p-2">
      <div className={clsx('flex-shrink-0 h-8 w-8 rounded-lg bg-gradient-to-br flex items-center justify-center border border-white/5', agentInfo?.color ?? 'from-white/10 to-white/5')}>
        <Icon size={14} className="text-white/50" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={clsx('text-xs font-medium', agentInfo?.text ?? 'text-white/50')}>{agentInfo?.label ?? event.agent ?? ''}</span>
          {event.status && <span className="text-[10px] text-white/20">{event.status}</span>}
        </div>
        {event.thought && <p className="text-xs text-white/40 mt-0.5 leading-relaxed">{event.thought}</p>}
        {event.action && <p className="text-xs text-white/30 mt-0.5 font-mono">{event.action}</p>}
      </div>
    </div>
  );
}
