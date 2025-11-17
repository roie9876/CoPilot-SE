// Type definitions for Co-Pilot SE API

export interface ClarificationQuestion {
  question: string;
  rationale: string;
  options?: string[];
  category?: string;
}

export interface RequirementsOutput {
  target_cloud: string;
  region: string | null;
  industry_vertical: string;
  functional_requirements: string[];
  non_functional_requirements: {
    scalability: Record<string, unknown>;
    performance: Record<string, unknown>;
    availability: Record<string, unknown>;
    security: Record<string, unknown>;
    compliance: string[];
  };
  technical_constraints: {
    budget: string | null;
    timeline: string | null;
    team_skills: string[];
    existing_infrastructure: string[];
    preferred_technologies: string[];
  };
  implied_requirements: string[];
  // Chain of thought fields
  chain_of_thought?: string;
  decisions_made?: string[];
  current_understanding?: string;
  // Clarification fields
  needs_clarification: boolean;
  clarifying_questions: ClarificationQuestion[];
  ambiguities_detected: string[];
  confidence_score: number;
  extraction_method: string;
  citations: Citation[];
}

export interface ServiceSelection {
  category: string;
  service_name: string;
  rationale: string;
  configuration: {
    sku?: string;
    instance_type?: string;
    replicas: number;
    storage_gb?: number;
    auto_scaling?: Record<string, unknown>;
    additional_settings: Record<string, unknown>;
  };
  alternatives: string[];
  estimated_monthly_cost: number;
}

export interface ArchitectureOutput {
  target_cloud: string;
  region: string;
  architecture_summary: string;
  services: ServiceSelection[];
  architecture_diagram: string;
  diagram_format: string;
  design_rationale: {
    operational_excellence: string;
    security: string;
    reliability: string;
    performance_efficiency: string;
    cost_optimization: string;
  };
  deployment_considerations: {
    region: string;
    multi_az: boolean;
    prerequisites: string[];
    deployment_methods: string[];
    estimated_deployment_time: string;
  };
  trade_offs: string[];
  technology_stack: string[];
  citations: Citation[];
  validation_warnings?: string[];
}

export interface ServiceCost {
  service_name: string;
  category: string;
  pricing_model: string;
  low_usage_monthly: number;
  medium_usage_monthly: number;
  high_usage_monthly: number;
  assumptions: Record<string, unknown>;
  pricing_tier: string;
  pricing_url: string;
  cost_breakdown: Record<string, unknown>;
}

export interface CostOutput {
  target_cloud: string;
  region: string;
  currency: string;
  time_period: string;
  service_costs: ServiceCost[];
  total_monthly_cost_low: number;
  total_monthly_cost_medium: number;
  total_monthly_cost_high: number;
  cost_by_category: Record<string, number>;
  cost_optimization_recommendations: Array<{
    category: string;
    recommendation: string;
    estimated_savings_monthly: number | null;
    effort: string;
  }>;
  assumptions: string[];
  disclaimers: string[];
  confidence_level: string;
  sources: Citation[];
  citations: Citation[];
}

export interface DocumentationOutput {
  format: string;
  content: string;
  diagrams: Array<{
    name: string;
    format: string;
    content: string;
    description: string;
  }>;
  metadata: {
    title: string;
    generated_at: string;
    cloud_platform: string;
    version: string;
    filename: string;
    author: string;
  };
  export_formats: string[];
}

export interface Citation {
  title: string;
  url: string;
  relevance: string;
  accessed_at: string;
}

export interface WorkflowMetadata {
  stages_completed: string[];
  total_duration_seconds: number;
  agents_invoked: string[];
  start_time: string;
  end_time: string;
  clarification_rounds?: number;
  requirements_diff?: Record<string, unknown> | null;
  reviewer_context?: Record<string, unknown> | null;
  architecture_validation_warnings?: string[];
}

// Multi-stage wizard types
export type ConversationStage = 
  | 'stage_1_requirements'
  | 'stage_2_compute'
  | 'stage_3_data'
  | 'stage_4_security'
  | 'stage_5_review'
  | 'complete';

export interface TradeOff {
  option_name: string;
  pros: string[];
  cons: string[];
  cost_impact: string;
  performance_impact?: string;
  recommended: boolean;
}

export interface StageRecommendation {
  decision_name: string;
  recommendation: string;
  reasoning: string;
  trade_offs: TradeOff[];
  alternatives: string[];
  cost_impact: string;
  dependencies?: string[];
  follow_up_questions?: ClarificationQuestion[];
}

export interface StageOutput {
  stage: ConversationStage;
  stage_title: string;
  stage_description: string;
  recommendations: StageRecommendation[];
  questions: ClarificationQuestion[];
  chain_of_thought?: string;
  decisions_made: string[];
  estimated_cost?: string;
  can_proceed: boolean;
  requires_approval: boolean;
}

export interface OrchestratorOutput {
  status: string;
  current_stage?: string;
  requirements?: RequirementsOutput;
  architecture?: ArchitectureOutput;
  costs?: CostOutput;
  documentation?: DocumentationOutput;
  citations: Citation[];
  workflow_metadata: WorkflowMetadata;
  architecture_validation_warnings?: string[];
  // Interactive clarification fields
  clarifying_questions?: ClarificationQuestion[];
  chain_of_thought?: string;
  decisions_made?: string[];
  current_understanding?: string;
  ambiguities?: string[];
  // Session management
  session_id?: string;
  awaiting_response?: boolean;
  // Multi-stage wizard fields
  conversation_stage?: ConversationStage;
  stage_output?: StageOutput;
  stages_completed?: ConversationStage[];
  all_stage_decisions?: Record<string, string[]>;
  total_estimated_cost?: string;
  can_go_back?: boolean;
  // Error fields
  error_message?: string;
  errors: Array<Record<string, unknown>>;
}

export interface ApiError {
  error: string;
  details?: string;
  status?: number;
}
