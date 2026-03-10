import { useNavigate, useLocation } from 'react-router-dom';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { useAuthStore } from '../store/auth';
import { Shield, Brain, Zap, BarChart3, ArrowRight } from 'lucide-react';
import api from '../lib/api';
import { useState } from 'react';

const FEATURES = [
  { icon: Brain, label: '5 AI Agents', desc: 'Autonomous credit analysis pipeline' },
  { icon: BarChart3, label: 'ML Scoring', desc: 'XGBoost + LightGBM ensemble PD' },
  { icon: Zap, label: 'Real-time', desc: 'Live streaming CAM generation' },
  { icon: Shield, label: 'RBI Compliant', desc: 'Basel III & IRAC norms built-in' },
];

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((s) => s.login);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const redirectTo = (location.state as { from?: string })?.from || '/dashboard';

  // Already authenticated — redirect
  if (isAuthenticated) {
    navigate(redirectTo, { replace: true });
    return null;
  }

  const handleSuccess = async (response: CredentialResponse) => {
    if (!response.credential) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/auth/google', {
        credential: response.credential,
      });
      login(data.token, data.user);
      navigate(redirectTo, { replace: true });
    } catch {
      setError('Sign-in failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-nexus-dark-bg flex">

      {/* Left Panel — Branding & Features */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden">
        {/* Animated gradient background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-br from-nexus-cyan/8 via-indigo-600/6 to-transparent" />
          <div className="absolute top-0 right-0 w-[600px] h-[600px] rounded-full bg-nexus-cyan/4 blur-[150px] animate-pulse" style={{ animationDuration: '8s' }} />
          <div className="absolute bottom-0 left-0 w-[500px] h-[500px] rounded-full bg-indigo-500/4 blur-[130px] animate-pulse" style={{ animationDuration: '12s' }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] rounded-full bg-emerald-500/3 blur-[100px] animate-pulse" style={{ animationDuration: '10s' }} />
        </div>

        {/* Grid pattern overlay */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }} />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 xl:p-16 w-full">
          {/* Top — Logo */}
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-nexus-cyan to-indigo-500 flex items-center justify-center shadow-lg shadow-nexus-cyan/20">
              <span className="text-white font-bold text-lg">N</span>
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white">
                NEXUS <span className="text-nexus-cyan">CREDIT</span>
              </span>
              <p className="text-[10px] text-white/25 tracking-widest uppercase">AI Credit Decisioning Engine</p>
            </div>
          </div>

          {/* Center — Hero text */}
          <div className="space-y-8">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-nexus-cyan/20 bg-nexus-cyan/5 px-4 py-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-nexus-cyan animate-pulse" />
                <span className="text-xs text-nexus-cyan font-medium">Platform Active</span>
              </div>
              <h1 className="text-4xl xl:text-5xl font-bold text-white leading-[1.15] tracking-tight">
                Credit decisions<br />
                powered by<br />
                <span className="bg-gradient-to-r from-nexus-cyan via-indigo-400 to-nexus-cyan bg-clip-text text-transparent">
                  artificial intelligence
                </span>
              </h1>
              <p className="text-base text-white/35 max-w-md leading-relaxed">
                End-to-end autonomous credit analysis — from data ingestion to
                CAM generation — in under 90 seconds.
              </p>
            </div>

            {/* Feature pills */}
            <div className="grid grid-cols-2 gap-3">
              {FEATURES.map(({ icon: Icon, label, desc }) => (
                <div key={label} className="group flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 transition-all hover:border-white/10 hover:bg-white/[0.04]">
                  <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-nexus-cyan/10 border border-nexus-cyan/20 text-nexus-cyan">
                    <Icon size={16} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{label}</p>
                    <p className="text-xs text-white/30 mt-0.5">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom — Stats bar */}
          <div className="flex items-center gap-8">
            {[
              { val: '< 90s', lbl: 'Processing' },
              { val: '0.94', lbl: 'AUC-ROC' },
              { val: '5', lbl: 'AI Agents' },
              { val: '80+', lbl: 'Features' },
            ].map(({ val, lbl }) => (
              <div key={lbl}>
                <p className="text-lg font-bold text-white font-mono">{val}</p>
                <p className="text-[10px] text-white/25 uppercase tracking-wider">{lbl}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel — Sign In */}
      <div className="flex-1 flex items-center justify-center relative px-6">
        {/* Subtle background */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/3 right-1/4 w-72 h-72 rounded-full bg-nexus-cyan/3 blur-[100px]" />
          <div className="absolute bottom-1/3 left-1/4 w-72 h-72 rounded-full bg-indigo-500/3 blur-[100px]" />
        </div>

        <div className="relative z-10 w-full max-w-[400px]">
          {/* Mobile-only logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 mb-10">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-nexus-cyan to-indigo-500 flex items-center justify-center">
              <span className="text-white font-bold text-lg">N</span>
            </div>
            <span className="text-xl font-bold tracking-tight text-white">
              NEXUS <span className="text-nexus-cyan">CREDIT</span>
            </span>
          </div>

          {/* Card */}
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-sm p-8 sm:p-10 shadow-2xl">
            {/* Header */}
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-1">Sign in</h2>
              <p className="text-sm text-white/35">Continue with your Google account to get started</p>
            </div>

            {/* Google Sign-In */}
            <div className="space-y-4">
              <div className="flex justify-center">
                <GoogleLogin
                  onSuccess={handleSuccess}
                  onError={() => setError('Google sign-in encountered an error')}
                  theme="filled_black"
                  size="large"
                  width="360"
                  text="continue_with"
                  shape="pill"
                  logo_alignment="center"
                />
              </div>

              {loading && (
                <div className="flex items-center justify-center gap-2 text-sm text-white/40">
                  <div className="h-4 w-4 rounded-full border-2 border-white/20 border-t-nexus-cyan animate-spin" />
                  Signing you in...
                </div>
              )}

              {error && (
                <div className="rounded-lg border border-nexus-red/20 bg-nexus-red/5 px-4 py-3 text-center">
                  <p className="text-sm text-nexus-red">{error}</p>
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3 my-8">
              <div className="flex-1 h-px bg-white/[0.06]" />
              <Shield size={12} className="text-white/15" />
              <div className="flex-1 h-px bg-white/[0.06]" />
            </div>

            {/* Trust signals */}
            <div className="space-y-3">
              {[
                'Enterprise-grade encryption (AES-256)',
                'SOC 2 Type II compliant architecture',
                'Data processed per RBI guidelines',
              ].map((t) => (
                <div key={t} className="flex items-center gap-2.5">
                  <div className="h-1 w-1 rounded-full bg-nexus-cyan/50" />
                  <span className="text-[11px] text-white/20">{t}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Below card - CTA for landing */}
          <div className="mt-6 flex items-center justify-between">
            <p className="text-[11px] text-white/15">
              NEXUS CREDIT v1.0
            </p>
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-1 text-[11px] text-white/25 hover:text-white/50 transition-colors"
            >
              Back to home <ArrowRight size={10} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
