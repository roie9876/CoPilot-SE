// Type definitions for Co-Pilot SE API

export interface RequirementsOutput {
  target_cloud: string;
  region: string | null;
  industry_vertical: string;
  functional_requirements: string[];
  non_functional_requirements: {
    scalability: Record<string, any>;
    performance: Record<string, any>;
    availability: Record<string, any>;
    security: Record<string, any>;
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
  needs_clarification: boolean;
  clarifying_questions: string[];
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
    auto_scaling?: Record<string, any>;
    additional_settings: Record<string, any>;
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
}

export interface ServiceCost {
  service_name: string;
  category: string;
  pricing_model: string;
  low_usage_monthly: number;
  medium_usage_monthly: number;
  high_usage_monthly: number;
  assumptions: Record<string, any>;
  pricing_tier: string;
  pricing_url: string;
  cost_breakdown: Record<string, any>;
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
}

export interface OrchestratorOutput {
  status: string;
  requirements: RequirementsOutput;
  architecture: ArchitectureOutput;
  costs: CostOutput;
  documentation: DocumentationOutput;
  citations: Citation[];
  workflow_metadata: WorkflowMetadata;
  clarifying_questions?: string[];
  ambiguities?: string[];
  error_message?: string;
  errors: any[];
}

export interface ApiError {
  error: string;
  details?: string;
  status?: number;
}
