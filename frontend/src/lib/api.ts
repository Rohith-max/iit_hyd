import axios from 'axios';
import type { CreditCase, MLScore, EarlyWarningSignal, SHAPExplanation, DashboardStats, CompanyLookup } from '../types';

const api = axios.create({ baseURL: '/api/v1' });

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get('/dashboard/stats');
  return data;
}

export async function fetchCases(status?: string): Promise<CreditCase[]> {
  const params = status ? { status } : {};
  const { data } = await api.get('/cases', { params });
  return data.cases ?? data;
}

export async function fetchCase(caseId: string): Promise<CreditCase> {
  const { data } = await api.get(`/cases/${caseId}`);
  return data;
}

export async function createCase(payload: Record<string, unknown>): Promise<CreditCase> {
  const { data } = await api.post('/cases', payload);
  return data;
}

export async function triggerAnalysis(caseId: string): Promise<void> {
  await api.post(`/cases/${caseId}/analyze`);
}

export async function fetchDecision(caseId: string): Promise<{ scores: MLScore; ews: EarlyWarningSignal[] }> {
  const { data } = await api.get(`/cases/${caseId}/decision`);
  return { scores: data.ml_score, ews: data.early_warnings ?? [] };
}

export async function fetchCAM(caseId: string): Promise<Record<string, unknown>> {
  const { data } = await api.get(`/cases/${caseId}/cam`);
  return data;
}

export async function downloadCAMPDF(caseId: string): Promise<Blob> {
  const { data } = await api.get(`/cases/${caseId}/cam/pdf`, { responseType: 'blob' });
  return data;
}

export async function fetchSHAP(caseId: string): Promise<SHAPExplanation> {
  const { data } = await api.get(`/cases/${caseId}/shap`);
  return data;
}

export async function fetchEWS(caseId: string): Promise<EarlyWarningSignal[]> {
  const { data } = await api.get(`/cases/${caseId}/ews`);
  return data;
}

export async function lookupCompany(cin: string): Promise<CompanyLookup> {
  const { data } = await api.post('/companies/lookup', { cin });
  return data;
}

export async function fetchBenchmarks(nicCode: string) {
  const { data } = await api.get(`/industry/${nicCode}/benchmarks`);
  return data;
}

export async function fetchDemoMetrics() {
  const { data } = await api.get('/demo/metrics');
  return data;
}
