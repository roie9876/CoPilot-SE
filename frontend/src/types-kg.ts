// Knowledge Graph specific types
import type { ArchitectureOutput } from './types';

export interface KGQuestion {
  question_text: string;
  field_name: string;
  priority: 'critical' | 'important' | 'optional';
  context?: string;
  options?: string[];
  validation?: {
    type: string;
    min?: number;
    max?: number;
    pattern?: string;
  };
}

export interface DomainConfidence {
  identity: number;
  runtime: number;
  networking: number;
  data: number;
  resiliency: number;
  security: number;
  monitoring: number;
}

export interface Conflict {
  id: string;
  domains: string[];
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  detected_at?: string;
}

export interface KGValidateRequest {
  requirements: string;
}

export interface KGValidateResponse {
  is_valid: boolean;
  confidence: number;
  reason: string;
  suggestion: string;
}

export interface KGStartRequest {
  requirements: string;
}

export interface KGStartResponse {
  session_id: string;
  status: 'needs_clarification' | 'complete';
  domain: string;
  questions: KGQuestion[];
  ready_for_design: boolean;
  critical_gaps: number;
  conflicts: number;
  domain_confidence: DomainConfidence;
  overall_confidence: number;
}

export interface KGAnswerRequest {
  session_id: string;
  domain: string;
  answers: Record<string, string | number | boolean | string[]>;
}

export interface KGAnswerResponse {
  session_id: string;
  status: 'needs_clarification' | 'complete';
  domain: string;
  questions: KGQuestion[];
  ready_for_design: boolean;
  critical_gaps: number;
  conflicts: number;
  domain_confidence: DomainConfidence;
  overall_confidence: number;
}

export interface KGStatusResponse {
  session_id: string;
  ready_for_design: boolean;
  critical_gaps: number;
  conflicts: number;
  domain_confidence: DomainConfidence;
  overall_confidence: number;
  conflicts_detail: Conflict[];
}

export interface KGArchitectureRequest {
  session_id: string;
}

export interface ServiceCost {
  service_name: string;
  category?: string;
  pricing_model?: string;
  low_usage_monthly: number;
  medium_usage_monthly: number;
  high_usage_monthly: number;
  pricing_tier?: string;
  pricing_url?: string;
  // Legacy fields for backward compatibility
  sku?: string;
  tier?: string;
}

export interface CostOutput {
  total_monthly_cost_low: number;
  total_monthly_cost_medium: number;
  total_monthly_cost_high: number;
  currency: string;
  time_period: string;
  service_costs: ServiceCost[];
  assumptions?: string[];
  citations?: string[];
}

export interface DocumentationOutput {
  content: string;
  format: string;
  sections?: string[];
}

export interface KGArchitectureResponse {
  session_id: string;
  status: 'success' | 'error';
  architecture?: ArchitectureOutput;
  cost_estimate?: CostOutput;
  documentation?: DocumentationOutput;
  message?: string;
  error?: string;
}

// Domain names for display
export const DOMAIN_NAMES: Record<string, string> = {
  identity: 'Identity & Access',
  runtime: 'Runtime Platform',
  networking: 'Networking',
  data: 'Data Persistence',
  resiliency: 'Resiliency & DR',
  security: 'Security & Governance',
  monitoring: 'Monitoring & Observability',
};

// Domain colors for UI
export const DOMAIN_COLORS: Record<string, string> = {
  identity: '#3B82F6', // blue-500
  runtime: '#10B981', // green-500
  networking: '#8B5CF6', // purple-500
  data: '#F59E0B', // amber-500
  resiliency: '#EF4444', // red-500
  security: '#EC4899', // pink-500
  monitoring: '#06B6D4', // cyan-500
};
