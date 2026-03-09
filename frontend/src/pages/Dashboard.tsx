import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Activity, CheckCircle, Clock, TrendingUp, Plus, ArrowRight, Loader2 } from 'lucide-react';
import { fetchDashboardStats } from '../lib/api';
import clsx from 'clsx';

const LOAN_TYPE_LABELS: Record<string, string> = {
  TERM_LOAN: 'Term Loan',
  WCDL: 'WCDL',
  CC_LIMIT: 'CC Limit',
  LAP: 'LAP',
  BG: 'Bank Guarantee',
};

const STATUS_STYLES: Record<string, string> = {
  INTAKE: 'bg-white/10 text-white/70',
  PROCESSING: 'bg-nexus-cyan/20 text-nexus-cyan',
  REVIEW: 'bg-nexus-amber/20 text-nexus-amber',
  APPROVED: 'bg-nexus-green/20 text-nexus-green',
  CONDITIONAL: 'bg-nexus-amber/20 text-nexus-amber',
  DECLINED: 'bg-nexus-red/20 text-nexus-red',
};

function formatINR(value: number) {
  if (value >= 1e7) return `₹${(value / 1e7).toFixed(1)}Cr`;
  if (value >= 1e5) return `₹${(value / 1e5).toFixed(1)}L`;
  return `₹${value.toLocaleString('en-IN')}`;
}

function AnimatedNumber({ target, duration = 1500 }: { target: number; duration?: number }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let curr = 0;
    const step = target / (duration / 16);
    const t = setInterval(() => {
      curr += step;
      if (curr >= target) { setVal(target); clearInterval(t); } else setVal(Math.floor(curr));
    }, 16);
    return () => clearInterval(t);
  }, [target, duration]);
  return <>{val.toLocaleString()}</>;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 30_000,
  });

  const statCards = [
    { label: 'Active Cases', value: stats?.total_cases ?? 0, icon: Activity, color: 'text-nexus-cyan', bgColor: 'bg-nexus-cyan/10', border: 'border-nexus-cyan/20' },
    { label: 'Approved This Month', value: stats?.approved_this_month ?? 0, icon: CheckCircle, color: 'text-nexus-green', bgColor: 'bg-nexus-green/10', border: 'border-nexus-green/20' },
    { label: 'Avg Process Time', value: stats?.avg_processing_time ?? '2m 43s', isString: true, icon: Clock, color: 'text-nexus-amber', bgColor: 'bg-nexus-amber/10', border: 'border-nexus-amber/20' },
    { label: 'Platform Accuracy', value: stats?.avg_credit_score ?? 94.2, suffix: '%', icon: TrendingUp, color: 'text-white', bgColor: 'bg-white/5', border: 'border-white/10' },
  ];

  const cases = stats?.recent_cases ?? [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Command Center</h1>
          <p className="text-sm text-white/40 mt-1">Real-time credit analysis overview</p>
        </div>
        <button
          onClick={() => navigate('/intake')}
          className="flex items-center gap-2 rounded-xl bg-white text-black px-5 py-2.5 text-sm font-semibold transition-all hover:bg-white/90"
        >
          <Plus size={16} />
          New Analysis
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) => (
          <div
            key={i}
            className={`rounded-xl border ${card.border} bg-nexus-dark-card p-5 transition-all hover:bg-white/[0.03]`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-white/40 uppercase tracking-wider">{card.label}</span>
              <div className={`h-8 w-8 rounded-lg ${card.bgColor} flex items-center justify-center`}>
                <card.icon size={16} className={card.color} />
              </div>
            </div>
            <div className={`text-3xl font-bold font-mono ${card.color}`}>
              {card.isString ? (
                <span>{card.value}</span>
              ) : (
                <>
                  <AnimatedNumber target={typeof card.value === 'number' ? card.value : 0} />
                  {card.suffix ?? ''}
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Cases Table */}
      <div className="rounded-xl border border-nexus-dark-border bg-nexus-dark-card overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-nexus-dark-border">
          <h2 className="font-semibold text-sm">Recent Cases</h2>
          <span className="text-xs text-white/30">{cases.length} cases</span>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={24} className="animate-spin text-white/30" />
          </div>
        ) : cases.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-white/30">
            <Activity size={40} className="mb-4 opacity-30" />
            <p className="text-sm">No cases yet</p>
            <button onClick={() => navigate('/intake')} className="mt-4 text-nexus-cyan text-sm hover:underline">
              Create your first analysis →
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-nexus-dark-border text-white/30">
                  <th className="px-6 py-3 text-left font-medium">Case #</th>
                  <th className="px-6 py-3 text-left font-medium">Company</th>
                  <th className="px-6 py-3 text-left font-medium">Loan Type</th>
                  <th className="px-6 py-3 text-right font-medium">Amount</th>
                  <th className="px-6 py-3 text-center font-medium">Status</th>
                  <th className="px-6 py-3 text-left font-medium">Submitted</th>
                  <th className="px-6 py-3 text-right font-medium" />
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => (
                  <tr
                    key={c.id}
                    className="border-b border-nexus-dark-border/50 hover:bg-white/[0.02] transition-colors cursor-pointer"
                    onClick={() => {
                      if (c.status === 'PROCESSING') navigate(`/cases/${c.id}/live`);
                      else if (['APPROVED', 'CONDITIONAL', 'DECLINED'].includes(c.status)) navigate(`/cases/${c.id}/decision`);
                      else navigate(`/cases/${c.id}/live`);
                    }}
                  >
                    <td className="px-6 py-4 font-mono text-white/60 text-xs">{c.case_number}</td>
                    <td className="px-6 py-4 font-medium">{c.company_name}</td>
                    <td className="px-6 py-4 text-white/60">{LOAN_TYPE_LABELS[c.loan_type] ?? c.loan_type}</td>
                    <td className="px-6 py-4 text-right font-mono">{formatINR(c.requested_amount)}</td>
                    <td className="px-6 py-4 text-center">
                      <span className={clsx('inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium', STATUS_STYLES[c.status] ?? 'bg-white/10 text-white/60')}>
                        {c.status === 'PROCESSING' && <span className="h-1.5 w-1.5 rounded-full bg-nexus-cyan animate-pulse" />}
                        {c.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-white/40 text-xs">{new Date(c.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-right">
                      <ArrowRight size={14} className="text-white/20" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
