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
}

export interface Conflict {
  id: string;
  domains: string[];
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  detected_at?: string;
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

export interface KGArchitectureResponse {
  session_id: string;
  status: 'success' | 'error';
  architecture?: ArchitectureOutput;
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
};

// Domain colors for UI
export const DOMAIN_COLORS: Record<string, string> = {
  identity: '#3B82F6', // blue-500
  runtime: '#10B981', // green-500
  networking: '#8B5CF6', // purple-500
  data: '#F59E0B', // amber-500
  resiliency: '#EF4444', // red-500
  security: '#EC4899', // pink-500
};
