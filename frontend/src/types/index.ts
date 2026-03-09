export interface CreditCase {
  id: string;
  case_number: string;
  company_name: string;
  cin: string;
  gstin: string;
  pan: string;
  industry_code: string;
  loan_type: string;
  requested_amount: number;
  requested_tenure_months: number;
  purpose: string;
  status: string;
  created_at: string;
  updated_at: string;
  priority: string;
}

export interface MLScore {
  pd_score: number;
  lgd_score: number;
  ead: number;
  expected_loss: number;
  credit_grade: string;
  credit_score: number;
  recommended_limit: number;
  recommended_rate: number;
  risk_premium: number;
  decision: string;
  confidence: number;
  shap_values: Record<string, number>;
  feature_importances: Record<string, number>;
}

export interface EarlyWarningSignal {
  id: string;
  signal_type: string;
  severity: 'RED' | 'AMBER' | 'GREEN';
  description: string;
  triggered_by: string;
}

export interface SHAPFeature {
  feature: string;
  value: number;
  shap_value: number;
  direction: 'positive' | 'negative';
}

export interface SHAPExplanation {
  waterfall_data: SHAPFeature[];
  natural_language_summary: string;
  risk_radar: Record<string, number>;
}

export interface AgentEvent {
  type: string;
  agent?: string;
  thought?: string;
  action?: string;
  status?: string;
  data?: Record<string, unknown>;
  section?: string;
  delta?: string;
  timestamp?: string;
}

export interface DashboardStats {
  total_cases: number;
  approved_this_month: number;
  avg_processing_time: string;
  avg_credit_score: number;
  recent_cases: CreditCase[];
}

export interface CompanyLookup {
  company_name: string;
  cin: string;
  date_of_incorporation: string;
  registered_address: string;
  industry: string;
  directors: { name: string; din: string; designation: string }[];
}
