import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Building2, FileUp, CreditCard, Shield, CheckCircle, ArrowRight, ArrowLeft, Upload, Rocket, Loader2, Search } from 'lucide-react';
import { createCase, triggerAnalysis, lookupCompany } from '../lib/api';
import clsx from 'clsx';

const STEPS = [
  { label: 'Company', icon: Building2 },
  { label: 'Financials', icon: FileUp },
  { label: 'Loan', icon: CreditCard },
  { label: 'Collateral', icon: Shield },
  { label: 'Review', icon: CheckCircle },
];

const LOAN_TYPES = ['TERM_LOAN', 'WCDL', 'CC_LIMIT', 'LAP', 'BG'];
const LOAN_LABELS: Record<string, string> = { TERM_LOAN: 'Term Loan', WCDL: 'Working Capital', CC_LIMIT: 'Cash Credit', LAP: 'Loan Against Property', BG: 'Bank Guarantee' };

function formatINR(v: number) {
  if (v >= 1e7) return `₹${(v / 1e7).toFixed(1)} Cr`;
  if (v >= 1e5) return `₹${(v / 1e5).toFixed(1)} L`;
  return `₹${v.toLocaleString('en-IN')}`;
}

export default function Intake() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [lookingUp, setLookingUp] = useState(false);

  // Step 1: Company
  const [companyName, setCompanyName] = useState('');
  const [cin, setCin] = useState('');
  const [gstin, setGstin] = useState('');
  const [pan, setPan] = useState('');
  const [industryCode, setIndustryCode] = useState('');

  // Step 2: Files
  const [files, setFiles] = useState<Record<string, File[]>>({
    financials: [],
    bankStatements: [],
    itr: [],
    gst: [],
  });

  // Step 3: Loan
  const [loanType, setLoanType] = useState('TERM_LOAN');
  const [amount, setAmount] = useState(10_00_00_000);
  const [tenure, setTenure] = useState(60);
  const [purpose, setPurpose] = useState('');

  // Step 4: Collateral
  const [collateralType, setCollateralType] = useState('immovable_property');
  const [collateralValue, setCollateralValue] = useState(0);
  const [collateralDesc, setCollateralDesc] = useState('');

  const handleCINLookup = async () => {
    if (!cin || cin.length < 10) return;
    setLookingUp(true);
    try {
      const data = await lookupCompany(cin);
      setCompanyName(data.company_name || companyName);
      if (data.industry) setIndustryCode(data.industry);
    } catch { /* ignore */ }
    setLookingUp(false);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const caseData = await createCase({
        company_name: companyName,
        cin, gstin, pan,
        industry_code: industryCode,
        loan_type: loanType,
        requested_amount: amount,
        requested_tenure_months: tenure,
        purpose,
      });
      await triggerAnalysis(caseData.id);
      navigate(`/cases/${caseData.id}/live`);
    } catch (err) {
      console.error('Failed to create case:', err);
      setSubmitting(false);
    }
  };

  const canNext = () => {
    if (step === 0) return companyName.trim().length > 0;
    if (step === 2) return amount > 0 && purpose.trim().length > 0;
    return true;
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Step Indicator */}
      <div className="flex items-center justify-center gap-2 mb-10">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center gap-2">
            <button
              onClick={() => i < step && setStep(i)}
              className={clsx(
                'flex items-center gap-2 rounded-full px-4 py-2 text-xs font-medium transition-all',
                i === step ? 'bg-white text-black' :
                i < step ? 'bg-nexus-cyan/20 text-nexus-cyan' :
                'bg-white/5 text-white/30',
              )}
            >
              {i < step ? <CheckCircle size={14} /> : <s.icon size={14} />}
              <span className="hidden sm:inline">{s.label}</span>
            </button>
            {i < STEPS.length - 1 && <div className={clsx('h-px w-8', i < step ? 'bg-nexus-cyan/30' : 'bg-white/10')} />}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="rounded-2xl border border-nexus-dark-border bg-nexus-dark-card p-8">

        {/* STEP 0: Company Info */}
        {step === 0 && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Company Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="text-xs text-white/40 uppercase tracking-wider mb-1.5 block">CIN (Auto-lookup)</label>
                <div className="flex gap-2">
                  <input
                    value={cin} onChange={e => setCin(e.target.value)}
                    placeholder="U40106RJ2015PTC048123"
                    className="flex-1 rounded-lg bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:border-nexus-cyan/50 focus:outline-none transition-colors font-mono"
                  />
                  <button onClick={handleCINLookup} disabled={lookingUp} className="rounded-lg bg-white/5 border border-white/10 px-4 hover:bg-white/10 transition-colors">
                    {lookingUp ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
                  </button>
                </div>
              </div>
              <div className="md:col-span-2">
                <label className="text-xs text-white/40 uppercase tracking-wider mb-1.5 block">Company Name *</label>
                <input value={companyName} onChange={e => setCompanyName(e.target.value)} placeholder="Rajasthan Solar Tech Pvt Ltd" className="w-full rounded-lg bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:border-nexus-cyan/50 focus:outline-none transition-colors" />
              </div>
              <div>
                <label className="text-xs text-white/40 uppercase tracking-wider mb-1.5 block">GSTIN</label>
                <input value={gstin} onChange={e => setGstin(e.target.value)} placeholder="08AABCU9603R1ZM" className="w-full rounded-lg bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:border-nexus-cyan/50 focus:outline-none transition-colors font-mono" />
              </div>
              <div>
                <label className="text-xs text-white/40 uppercase tracking-wider mb-1.5 block">PAN</label>
                <input value={pan} onChange={e => setPan(e.target.value)} placeholder="AABCU9603R" className="w-full rounded-lg bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:border-nexus-cyan/50 focus:outline-none transition-colors font-mono" />
              </div>
              <div>
                <label className="text-xs text-white/40 uppercase tracking-wider mb-1.5 block">Industry Code (NIC)</label>
                <input value={industryCode} onChange={e => setIndustryCode(e.target.value)} placeholder="26" className="w-full rounded-lg bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:border-nexus-cyan/50 focus:outline-none transition-colors font-mono" />
              </div>
            </div>
          </div>
        )}

        {/* STEP 1: Financial Uploads */}
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Upload Financial Documents</h2>
            <p className="text-sm text-white/40">Drag & drop or click to upload. PDFs accepted.</p>
            {[
              { key: 'financials', label: 'Audited Financials (3 years)' },
              { key: 'bankStatements', label: 'Bank Statements (12 months)' },
              { key: 'itr', label: 'ITR (3 years)' },
              { key: 'gst', label: 'GST Returns (12 months)' },
            ].map(({ key, label }) => (
              <DropZone
                key={key}
                label={label}
                files={files[key]}
                onDrop={(accepted) => setFiles(f => ({ ...f, [key]: [...f[key], ...accepted] }))}
              />
            ))}
          </div>
        )}

        {/* STEP 2: Loan Parameters */}
        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Loan Parameters</h2>
            <div>
              <label className="text-xs text-white/40 uppercase tracking-wider mb-3 block">Facility Type</label>
              <div className="flex flex-wrap gap-2">
                {LOAN_TYPES.map(t => (
                  <button
                    key={t}
                    onClick={() => setLoanType(t)}
                    className={clsx(
                      'rounded-full px-5 py-2 text-sm font-medium transition-all border',
                      loanType === t ? 'bg-white text-black border-white' : 'bg-white/5 text-white/60 border-white/10 hover:border-white/20'
                    )}
                  >
                    {LOAN_LABELS[t]}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-white/40 uppercase tracking-wider mb-1.5 block">Requested Amount: {formatINR(amount)}</label>
              <input type="range" min={10_00_000} max={100_00_00_000} step={10_00_000} value={amount} onChange={e => setAmount(Number(e.target.value))} className="w-full accent-nexus-cyan" />
              <div className="flex justify-between text-xs text-white/20 mt-1">
                <span>₹10L</span><span>₹100Cr</span>
              </div>
            </div>
            <div>
              <label className="text-xs text-white/40 uppercase tracking-wider mb-3 block">Tenure (Months)</label>
              <div className="flex gap-2">
                {[12, 24, 36, 60, 84, 120].map(t => (
                  <button key={t} onClick={() => setTenure(t)} className={clsx('rounded-lg px-4 py-2 text-sm font-mono transition-all border', tenure === t ? 'bg-white text-black border-white' : 'bg-white/5 border-white/10 hover:border-white/20')}>
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-white/40 uppercase tracking-wider mb-1.5 block">Purpose *</label>
              <textarea value={purpose} onChange={e => setPurpose(e.target.value)} rows={3} placeholder="Capex for manufacturing expansion..." className="w-full rounded-lg bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:border-nexus-cyan/50 focus:outline-none transition-colors resize-none" />
            </div>
          </div>
        )}

        {/* STEP 3: Collateral */}
        {step === 3 && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Collateral Details</h2>
            <div>
              <label className="text-xs text-white/40 uppercase tracking-wider mb-3 block">Collateral Type</label>
              <div className="flex flex-wrap gap-2">
                {[
                  { k: 'immovable_property', l: 'Immovable Property' },
                  { k: 'movable_assets', l: 'Movable Assets' },
                  { k: 'financial_assets', l: 'Financial Assets' },
                  { k: 'none', l: 'Unsecured' },
                ].map(({ k, l }) => (
                  <button key={k} onClick={() => setCollateralType(k)} className={clsx('rounded-full px-5 py-2 text-sm font-medium transition-all border', collateralType === k ? 'bg-white text-black border-white' : 'bg-white/5 text-white/60 border-white/10 hover:border-white/20')}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-white/40 uppercase tracking-wider mb-1.5 block">Estimated Value: {formatINR(collateralValue)}</label>
              <input type="range" min={0} max={200_00_00_000} step={25_00_000} value={collateralValue} onChange={e => setCollateralValue(Number(e.target.value))} className="w-full accent-nexus-cyan" />
            </div>
            <div>
              <label className="text-xs text-white/40 uppercase tracking-wider mb-1.5 block">Description</label>
              <textarea value={collateralDesc} onChange={e => setCollateralDesc(e.target.value)} rows={3} placeholder="Property at Survey No. 123, Jodhpur..." className="w-full rounded-lg bg-white/5 border border-white/10 px-4 py-2.5 text-sm focus:border-nexus-cyan/50 focus:outline-none transition-colors resize-none" />
            </div>
          </div>
        )}

        {/* STEP 4: Review & Submit */}
        {step === 4 && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Review & Launch Analysis</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <ReviewItem label="Company" value={companyName} />
              <ReviewItem label="CIN" value={cin || '—'} mono />
              <ReviewItem label="GSTIN" value={gstin || '—'} mono />
              <ReviewItem label="Industry" value={industryCode || '—'} mono />
              <ReviewItem label="Facility" value={LOAN_LABELS[loanType]} />
              <ReviewItem label="Amount" value={formatINR(amount)} mono />
              <ReviewItem label="Tenure" value={`${tenure} months`} mono />
              <ReviewItem label="Collateral" value={collateralType.replace(/_/g, ' ')} />
            </div>
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
              <span className="text-xs text-white/30">Purpose</span>
              <p className="text-sm mt-1 text-white/70">{purpose || '—'}</p>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/5">
          {step > 0 ? (
            <button onClick={() => setStep(s => s - 1)} className="flex items-center gap-2 text-sm text-white/50 hover:text-white transition-colors">
              <ArrowLeft size={14} /> Back
            </button>
          ) : <div />}

          {step < 4 ? (
            <button
              onClick={() => setStep(s => s + 1)}
              disabled={!canNext()}
              className="flex items-center gap-2 rounded-xl bg-white text-black px-6 py-2.5 text-sm font-semibold transition-all hover:bg-white/90 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Continue <ArrowRight size={14} />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="group flex items-center gap-3 rounded-xl bg-gradient-to-r from-nexus-cyan to-blue-500 text-black px-8 py-3 text-sm font-bold transition-all hover:shadow-[0_0_30px_rgba(0,229,255,0.3)] disabled:opacity-50"
            >
              {submitting ? (
                <><Loader2 size={16} className="animate-spin" /> Initiating...</>
              ) : (
                <><Rocket size={16} /> Initiate AI Analysis</>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Sub-components ─── */

function DropZone({ label, files, onDrop }: { label: string; files: File[]; onDrop: (f: File[]) => void }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        'rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-all',
        isDragActive ? 'border-nexus-cyan/50 bg-nexus-cyan/5' : 'border-white/10 hover:border-white/20',
      )}
    >
      <input {...getInputProps()} />
      <Upload size={20} className="mx-auto mb-2 text-white/30" />
      <p className="text-sm font-medium">{label}</p>
      {files.length > 0 && (
        <p className="text-xs text-nexus-cyan mt-2">{files.length} file(s) selected</p>
      )}
      {files.length === 0 && <p className="text-xs text-white/30 mt-1">Drop PDFs here or click to browse</p>}
    </div>
  );
}

function ReviewItem({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-lg bg-white/[0.02] border border-white/5 p-3">
      <span className="text-xs text-white/30">{label}</span>
      <p className={clsx('text-sm mt-0.5', mono && 'font-mono')}>{value}</p>
    </div>
  );
}
