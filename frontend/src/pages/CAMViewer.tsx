import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Download, Printer, ArrowLeft, FileText, CheckCircle2 } from 'lucide-react';
import { fetchCAM, fetchCase, downloadCAMPDF } from '../lib/api';
import clsx from 'clsx';

const SECTION_ORDER = [
  'executive_summary', 'company_background', 'industry_analysis',
  'financial_analysis', 'banking_conduct', 'collateral_assessment',
  'risk_assessment', 'credit_decision', 'covenants_conditions', 'appendices',
];

function sectionLabel(key: string) {
  return key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

export default function CAMViewer() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();

  const { data: caseData } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => fetchCase(caseId!),
    enabled: !!caseId,
  });

  const { data: camData, isLoading } = useQuery({
    queryKey: ['cam', caseId],
    queryFn: () => fetchCAM(caseId!),
    enabled: !!caseId,
  });

  const handleDownload = async () => {
    if (!caseId) return;
    const blob = await downloadCAMPDF(caseId);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CAM-${caseData?.case_number ?? caseId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => window.print();

  const rawSections = (camData?.sections ?? camData ?? {}) as Record<string, unknown>;
  // Normalize: sections may be strings or {title, content} objects
  const sections: Record<string, string> = {};
  for (const [k, v] of Object.entries(rawSections)) {
    if (typeof v === 'string') sections[k] = v;
    else if (v && typeof v === 'object' && 'content' in v) sections[k] = (v as {content: string}).content;
  }
  // Also map 'covenants' → 'covenants_conditions' if needed
  if (!sections['covenants_conditions'] && sections['covenants']) sections['covenants_conditions'] = sections['covenants'];
  const availableSections = SECTION_ORDER.filter(k => sections[k]);

  const scrollToSection = (key: string) => {
    document.getElementById(`cam-${key}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="flex gap-6">
      {/* Sticky TOC Sidebar */}
      <aside className="hidden lg:block w-64 flex-shrink-0">
        <div className="sticky top-24 space-y-1">
          <div className="mb-4">
            <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-white/30 hover:text-white/60 transition-colors">
              <ArrowLeft size={12} /> Back
            </button>
          </div>
          <h3 className="text-xs text-white/30 uppercase tracking-wider mb-3">Table of Contents</h3>
          {SECTION_ORDER.map((key, i) => {
            const hasContent = !!sections[key];
            return (
              <button
                key={key}
                onClick={() => hasContent && scrollToSection(key)}
                className={clsx(
                  'w-full flex items-center gap-2 rounded-lg px-3 py-2 text-left text-xs transition-colors',
                  hasContent ? 'text-white/60 hover:text-white hover:bg-white/5' : 'text-white/15 cursor-not-allowed',
                )}
              >
                {hasContent ? (
                  <CheckCircle2 size={12} className="text-nexus-green flex-shrink-0" />
                ) : (
                  <div className="h-3 w-3 rounded-full border border-white/10 flex-shrink-0" />
                )}
                <span className="font-mono text-[10px] text-white/20 w-5">{i + 1}.</span>
                {sectionLabel(key)}
              </button>
            );
          })}

          {/* Actions */}
          <div className="border-t border-white/5 pt-4 mt-4 space-y-2">
            <button onClick={handleDownload} className="w-full flex items-center gap-2 rounded-lg bg-white text-black px-4 py-2.5 text-xs font-semibold hover:bg-white/90 transition-colors">
              <Download size={12} /> Download PDF
            </button>
            <button onClick={handlePrint} className="w-full flex items-center gap-2 rounded-lg border border-white/10 px-4 py-2.5 text-xs hover:bg-white/5 transition-colors">
              <Printer size={12} /> Print
            </button>
          </div>
        </div>
      </aside>

      {/* Main Document */}
      <div className="flex-1 min-w-0">
        {isLoading ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-white/30">
              <div className="h-10 w-10 rounded-full border-2 border-white/20 border-t-nexus-cyan animate-spin mx-auto mb-4" />
              <p className="text-sm">Loading CAM document...</p>
            </div>
          </div>
        ) : availableSections.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-96 text-white/20">
            <FileText size={40} className="mb-4 opacity-30" />
            <p>No CAM data available yet</p>
            <button onClick={() => navigate(`/cases/${caseId}/live`)} className="text-nexus-cyan text-sm mt-3 hover:underline">
              Go to Live Analysis →
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Document Header */}
            <div className="rounded-xl bg-white/[0.02] border border-white/5 p-8 mb-6 text-center">
              <p className="text-xs text-white/20 uppercase tracking-widest mb-2">Nexus Bank Limited</p>
              <h1 className="text-2xl font-bold font-display">Credit Appraisal Memorandum</h1>
              <h2 className="text-lg text-white/60 mt-2">{caseData?.company_name}</h2>
              <div className="flex items-center justify-center gap-6 mt-4 text-xs text-white/30">
                <span>Case: {caseData?.case_number}</span>
                <span>•</span>
                <span>{new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
              </div>
            </div>

            {/* Sections */}
            {availableSections.map((key, i) => (
              <div
                key={key}
                id={`cam-${key}`}
                className="rounded-xl bg-white/[0.02] border border-white/5 p-8 scroll-mt-24"
              >
                <div className="flex items-center gap-3 mb-4 pb-3 border-b border-white/5">
                  <span className="text-xs font-mono text-white/20">{i + 1}.0</span>
                  <h2 className="text-lg font-semibold">{sectionLabel(key)}</h2>
                </div>
                <div className="prose prose-invert prose-sm max-w-none text-white/60 leading-relaxed whitespace-pre-wrap">
                  {sections[key]}
                </div>
              </div>
            ))}

            {/* Document Footer */}
            <div className="rounded-xl bg-white/[0.02] border border-white/5 p-6 text-center text-xs text-white/20">
              <p className="font-semibold mb-2">— CONFIDENTIAL —</p>
              <p>Generated by NEXUS CREDIT AI Engine v1.0 | {new Date().toISOString()}</p>
              <p className="mt-1">This document is computer-generated and requires authorized review before execution.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
