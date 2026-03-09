import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  LineChart, Line, Legend,
} from 'recharts';
import { CheckCircle, XCircle, AlertTriangle, Download, FileText, ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';
import { fetchDecision, fetchSHAP, fetchCase, downloadCAMPDF } from '../lib/api';
import clsx from 'clsx';

function formatINR(v: number) {
  if (v >= 1e7) return `₹${(v / 1e7).toFixed(1)}Cr`;
  if (v >= 1e5) return `₹${(v / 1e5).toFixed(1)}L`;
  return `₹${v.toLocaleString('en-IN')}`;
}

const GRADE_COLORS: Record<string, string> = {
  AAA: 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10',
  'AA+': 'text-yellow-300 border-yellow-300/30 bg-yellow-300/10',
  AA: 'text-gray-300 border-gray-300/30 bg-gray-300/10',
  'A+': 'text-nexus-cyan border-nexus-cyan/30 bg-nexus-cyan/10',
  A: 'text-nexus-cyan border-nexus-cyan/30 bg-nexus-cyan/10',
  BBB: 'text-nexus-green border-nexus-green/30 bg-nexus-green/10',
  BB: 'text-nexus-amber border-nexus-amber/30 bg-nexus-amber/10',
  B: 'text-nexus-amber border-nexus-amber/30 bg-nexus-amber/10',
  CCC: 'text-nexus-red border-nexus-red/30 bg-nexus-red/10',
  D: 'text-nexus-red border-nexus-red/30 bg-nexus-red/10',
};

export default function Decision() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();

  const { data: caseData } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => fetchCase(caseId!),
    enabled: !!caseId,
  });

  const { data: decisionData, isLoading } = useQuery({
    queryKey: ['decision', caseId],
    queryFn: () => fetchDecision(caseId!),
    enabled: !!caseId,
  });

  const { data: shapData } = useQuery({
    queryKey: ['shap', caseId],
    queryFn: () => fetchSHAP(caseId!),
    enabled: !!caseId,
  });

  const scores = decisionData?.scores;
  const ews = decisionData?.ews ?? [];

  const handleDownloadPDF = async () => {
    if (!caseId) return;
    const blob = await downloadCAMPDF(caseId);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CAM-${caseData?.case_number ?? caseId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading || !scores) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center text-white/30">
          <div className="h-12 w-12 rounded-full border-2 border-white/20 border-t-nexus-cyan animate-spin mx-auto mb-4" />
          <p>Loading decision...</p>
        </div>
      </div>
    );
  }

  const decision = scores.decision;
  const isApprove = decision === 'APPROVE';
  const isDecline = decision === 'DECLINE';

  // SHAP waterfall data
  const waterfallData = (shapData?.waterfall_data ?? []).slice(0, 12).map(f => ({
    feature: f.feature.replace(/_/g, ' ').slice(0, 25),
    value: f.shap_value,
    fill: f.direction === 'negative' ? '#00E5FF' : '#FFB800',
  }));

  // Risk radar data
  const radarData = shapData?.risk_radar
    ? Object.entries(shapData.risk_radar).map(([k, v]) => ({
        axis: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        value: v,
      }))
    : [
        { axis: 'Financial', value: 7 },
        { axis: 'Business', value: 6 },
        { axis: 'Management', value: 7 },
        { axis: 'Industry', value: 5 },
        { axis: 'Bureau', value: 8 },
        { axis: 'Collateral', value: 6 },
      ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-white/30 hover:text-white/60 mb-2 transition-colors">
            <ArrowLeft size={12} /> Back
          </button>
          <h1 className="text-xl font-bold">{caseData?.company_name}</h1>
          <p className="text-sm text-white/40 mt-0.5">{caseData?.case_number} — Decision Report</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate(`/cases/${caseId}/cam`)} className="flex items-center gap-2 rounded-xl border border-white/10 px-5 py-2.5 text-sm hover:bg-white/5 transition-colors">
            <FileText size={14} /> View CAM
          </button>
          <button onClick={handleDownloadPDF} className="flex items-center gap-2 rounded-xl bg-white text-black px-5 py-2.5 text-sm font-semibold hover:bg-white/90 transition-colors">
            <Download size={14} /> Download PDF
          </button>
        </div>
      </div>

      {/* Decision Hero */}
      <div className={clsx(
        'rounded-2xl border-2 p-8 text-center transition-all',
        isApprove ? 'border-nexus-green/30 bg-nexus-green/5' :
        isDecline ? 'border-nexus-red/30 bg-nexus-red/5' :
        'border-nexus-amber/30 bg-nexus-amber/5',
      )}>
        <div className="flex items-center justify-center gap-3 mb-2">
          {isApprove ? <CheckCircle size={32} className="text-nexus-green" /> :
           isDecline ? <XCircle size={32} className="text-nexus-red" /> :
           <AlertTriangle size={32} className="text-nexus-amber" />}
          <span className={clsx(
            'text-4xl font-bold',
            isApprove ? 'text-nexus-green' : isDecline ? 'text-nexus-red' : 'text-nexus-amber',
          )}>
            {decision}
          </span>
        </div>
        <p className="text-sm text-white/40">
          {isApprove ? 'Recommended for approval based on strong credit profile' :
           isDecline ? 'Application declined due to elevated risk indicators' :
           'Conditional approval subject to covenant compliance'}
        </p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard label="Credit Grade" value={scores.credit_grade} className={GRADE_COLORS[scores.credit_grade] ?? ''} large />
        <MetricCard label="Credit Score" value={scores.credit_score.toString()} mono />
        <MetricCard label="Recommended Limit" value={formatINR(scores.recommended_limit)} mono />
        <MetricCard label="Interest Rate" value={`${scores.recommended_rate.toFixed(2)}%`} sublabel="p.a." mono />
        <MetricCard label="Confidence" value={`${(scores.confidence * 100).toFixed(0)}%`} mono />
        <MetricCard label="Expected Loss" value={formatINR(scores.expected_loss)} sublabel={`PD: ${(scores.pd_score * 100).toFixed(2)}%`} mono />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* SHAP Waterfall */}
        <div className="rounded-xl border border-nexus-dark-border bg-nexus-dark-card p-6">
          <h3 className="text-sm font-semibold mb-4">SHAP Feature Importance</h3>
          {waterfallData.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={waterfallData} layout="vertical" margin={{ left: 100 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2530" />
                <XAxis type="number" tick={{ fill: '#666', fontSize: 10 }} />
                <YAxis type="category" dataKey="feature" tick={{ fill: '#999', fontSize: 10 }} width={95} />
                <Tooltip
                  contentStyle={{ background: '#141820', border: '1px solid #1E2530', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#fff' }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[350px] flex items-center justify-center text-white/20 text-sm">No SHAP data available</div>
          )}
        </div>

        {/* Risk Radar */}
        <div className="rounded-xl border border-nexus-dark-border bg-nexus-dark-card p-6">
          <h3 className="text-sm font-semibold mb-4">Risk Radar</h3>
          <ResponsiveContainer width="100%" height={350}>
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
              <PolarGrid stroke="#1E2530" />
              <PolarAngleAxis dataKey="axis" tick={{ fill: '#999', fontSize: 10 }} />
              <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fill: '#555', fontSize: 9 }} />
              <Radar dataKey="value" stroke="#00E5FF" fill="#00E5FF" fillOpacity={0.15} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* EWS Panel */}
      {ews.length > 0 && (
        <div className="rounded-xl border border-nexus-dark-border bg-nexus-dark-card p-6">
          <h3 className="text-sm font-semibold mb-4">Early Warning Signals</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {ews.map((e, i) => (
              <div
                key={i}
                className={clsx(
                  'rounded-lg border p-4',
                  e.severity === 'RED' ? 'border-nexus-red/20 bg-nexus-red/5' :
                  e.severity === 'AMBER' ? 'border-nexus-amber/20 bg-nexus-amber/5' :
                  'border-nexus-green/20 bg-nexus-green/5',
                )}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={clsx(
                    'text-xs font-bold uppercase',
                    e.severity === 'RED' ? 'text-nexus-red' : e.severity === 'AMBER' ? 'text-nexus-amber' : 'text-nexus-green',
                  )}>
                    {e.severity}
                  </span>
                  <span className={clsx(
                    'h-3 w-3 rounded-full',
                    e.severity === 'RED' ? 'bg-nexus-red' : e.severity === 'AMBER' ? 'bg-nexus-amber' : 'bg-nexus-green',
                  )} />
                </div>
                <p className="text-sm font-medium mb-1">{e.signal_type.replace(/_/g, ' ')}</p>
                <p className="text-xs text-white/40">{e.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SHAP Summary */}
      {shapData?.natural_language_summary && (
        <div className="rounded-xl border border-nexus-dark-border bg-nexus-dark-card p-6">
          <h3 className="text-sm font-semibold mb-3">AI Explanation</h3>
          <p className="text-sm text-white/60 leading-relaxed">{shapData.natural_language_summary}</p>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, sublabel, mono, large, className }: {
  label: string; value: string; sublabel?: string; mono?: boolean; large?: boolean; className?: string;
}) {
  return (
    <div className={clsx('rounded-xl border bg-nexus-dark-card p-4', className ? `border ${className}` : 'border-nexus-dark-border')}>
      <span className="text-[10px] text-white/30 uppercase tracking-wider">{label}</span>
      <div className={clsx('mt-1', large ? 'text-2xl font-bold' : 'text-xl font-bold', mono && 'font-mono')}>
        {value}
      </div>
      {sublabel && <span className="text-xs text-white/30">{sublabel}</span>}
    </div>
  );
}
