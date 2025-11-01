"""
Pydantic schemas for all agents and orchestrator.

Based on: .copilot/api-schemas.md
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Literal
from datetime import datetime
from enum import Enum
import re


# ============================================================
# ENUMS
# ============================================================

class CloudPlatform(str, Enum):
    """Supported cloud platforms."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ORACLE = "oracle"


class IndustryVertical(str, Enum):
    """Industry verticals for domain-specific requirements."""
    PUBLIC_SECTOR = "public_sector"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    GENERAL = "general"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    SUCCESS = "success"
    ERROR = "error"
    NEEDS_CLARIFICATION = "needs_clarification"
    IN_PROGRESS = "in_progress"


class ErrorType(str, Enum):
    """Types of errors in workflow."""
    VALIDATION_ERROR = "validation_error"
    API_ERROR = "api_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    UNKNOWN_ERROR = "unknown_error"


# ============================================================
# BASE MODELS
# ============================================================

class Citation(BaseModel):
    """Source citation."""
    title: str
    url: str
    relevance: str
    accessed_at: datetime = Field(default_factory=datetime.now)


class WorkflowMetadata(BaseModel):
    """Metadata about workflow execution."""
    stages_completed: List[str] = Field(default_factory=list)
    total_duration_seconds: float = 0.0
    agents_invoked: List[str] = Field(default_factory=list)
    start_time: datetime
    end_time: Optional[datetime] = None


class AgentError(BaseModel):
    """Error from an agent (data model)."""
    agent_name: str
    error_type: ErrorType
    error_message: str
    details: Optional[Dict] = None
    retryable: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentException(Exception):
    """Exception raised by agents (wraps AgentError model)."""
    
    def __init__(self, agent_error: AgentError):
        self.agent_error = agent_error
        super().__init__(agent_error.error_message)


# ============================================================
# ORCHESTRATOR MODELS
# ============================================================

class OrchestratorInput(BaseModel):
    """Input for Master Orchestrator."""
    
    user_request: str = Field(
        ...,
        description="Natural language request from user",
        min_length=10,
        max_length=5000,
        example="Design an AWS e-commerce platform for 10k users with $2000 budget"
    )
    
    context: Optional[Dict] = Field(
        None,
        description="Previous conversation context for multi-turn interactions"
    )
    
    options: Dict = Field(
        default_factory=lambda: {
            "generate_documentation": True,
            "output_format": "markdown",
            "include_cost_scenarios": True
        },
        description="Optional workflow settings"
    )
    
    @validator('user_request')
    def validate_request(cls, v):
        """Validate user request is not empty."""
        if not v.strip():
            raise ValueError("Request cannot be empty")
        return v.strip()


class OrchestratorOutput(BaseModel):
    """Output from Master Orchestrator."""
    
    status: WorkflowStatus
    
    # Agent outputs (optional based on status)
    requirements: Optional[Dict] = None
    architecture: Optional[Dict] = None
    costs: Optional[Dict] = None
    documentation: Optional[Dict] = None
    
    # Metadata
    citations: List[Citation] = Field(default_factory=list)
    workflow_metadata: WorkflowMetadata
    
    # If needs_clarification
    clarifying_questions: Optional[List[str]] = None
    ambiguities: Optional[List[str]] = None
    
    # If error
    error_message: Optional[str] = None
    errors: List[Dict] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


# ============================================================
# REQUIREMENTS AGENT MODELS
# ============================================================

class RequirementsInput(BaseModel):
    """Input for Requirements Agent."""
    
    user_input: str = Field(
        ...,
        description="Raw natural language request",
        min_length=10,
        example="Build a healthcare platform on Azure with HIPAA compliance"
    )
    
    context: Optional[Dict] = Field(
        None,
        description="Previous conversation context"
    )
    
    @validator('user_input')
    def clean_input(cls, v):
        """Clean and validate input."""
        return v.strip()


class NonFunctionalRequirements(BaseModel):
    """Non-functional requirements."""
    scalability: Dict = Field(default_factory=dict)
    performance: Dict = Field(default_factory=dict)
    availability: Dict = Field(default_factory=dict)
    security: Dict = Field(default_factory=dict)
    compliance: List[str] = Field(default_factory=list)


class TechnicalConstraints(BaseModel):
    """Technical constraints."""
    budget: Optional[Dict] = None  # {"monthly": 2000, "currency": "USD"}
    timeline: Optional[str] = None
    team_skills: List[str] = Field(default_factory=list)
    existing_infrastructure: List[str] = Field(default_factory=list)
    preferred_technologies: List[str] = Field(default_factory=list)


class RequirementsOutput(BaseModel):
    """Output from Requirements Agent."""
    
    # Core extraction
    target_cloud: Optional[CloudPlatform] = None
    region: Optional[str] = None
    industry_vertical: IndustryVertical = IndustryVertical.GENERAL
    
    # Requirements
    functional_requirements: List[str] = Field(
        default_factory=list,
        description="What the system must do"
    )
    non_functional_requirements: NonFunctionalRequirements = Field(
        default_factory=NonFunctionalRequirements
    )
    technical_constraints: TechnicalConstraints = Field(
        default_factory=TechnicalConstraints
    )
    implied_requirements: List[str] = Field(
        default_factory=list,
        description="Requirements inferred from context"
    )
    
    # Clarification
    needs_clarification: bool = False
    clarifying_questions: List[str] = Field(default_factory=list)
    ambiguities_detected: List[str] = Field(default_factory=list)
    
    # Metadata
    confidence_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in extracted requirements"
    )
    extraction_method: str = "gpt-5-cot"  # Chain of thought
    citations: List['Citation'] = Field(default_factory=list, description="Sources used")
    
    class Config:
        use_enum_values = True


# ============================================================
# ARCHITECTURE AGENT MODELS
# ============================================================

class ServiceConfiguration(BaseModel):
    """Configuration for a cloud service."""
    sku: Optional[str] = None
    instance_type: Optional[str] = None
    replicas: Optional[int] = 1
    storage_gb: Optional[int] = None
    auto_scaling: Optional[Dict] = None
    additional_settings: Dict = Field(default_factory=dict)


class ServiceSelection(BaseModel):
    """Selected cloud service."""
    category: str = Field(
        ...,
        description="Service category",
        example="compute"
    )
    service_name: str = Field(
        ...,
        description="Cloud service name",
        example="Azure App Service"
    )
    rationale: str = Field(
        ...,
        description="Why this service was chosen"
    )
    configuration: ServiceConfiguration = Field(
        default_factory=ServiceConfiguration
    )
    alternatives: List[str] = Field(
        default_factory=list,
        description="Other services considered"
    )
    estimated_monthly_cost: Optional[float] = None


class WellArchitectedAnalysis(BaseModel):
    """Well-Architected Framework analysis."""
    operational_excellence: str
    security: str
    reliability: str
    performance_efficiency: str
    cost_optimization: str


class ArchitectureInput(BaseModel):
    """Input for Architecture Agent."""
    
    requirements: RequirementsOutput = Field(
        ...,
        description="Structured requirements from Requirements Agent"
    )
    
    target_cloud: CloudPlatform = Field(
        ...,
        description="Target cloud platform"
    )
    
    region: Optional[str] = Field(
        None,
        description="Preferred cloud region",
        example="eastus"
    )
    
    @validator('target_cloud', pre=True)
    def validate_cloud(cls, v):
        """Validate and normalize cloud platform."""
        if isinstance(v, str):
            return CloudPlatform(v.lower())
        return v


class ArchitectureOutput(BaseModel):
    """Output from Architecture Agent."""
    
    target_cloud: CloudPlatform
    region: str = "eastus"
    architecture_summary: str = Field(
        ...,
        description="High-level architecture description"
    )
    
    # Services
    services: List[ServiceSelection] = Field(
        default_factory=list,
        description="Selected cloud services with rationale"
    )
    
    # Diagram
    architecture_diagram: str = Field(
        ...,
        description="Architecture diagram in mermaid syntax"
    )
    diagram_format: str = "mermaid"
    
    # Explanations
    design_rationale: WellArchitectedAnalysis
    
    # Additional info
    deployment_considerations: Dict = Field(
        default_factory=dict,
        description="Multi-AZ, multi-region, prerequisites"
    )
    trade_offs: List[str] = Field(
        default_factory=list,
        description="Design trade-offs and alternatives"
    )
    technology_stack: List[str] = Field(
        default_factory=list,
        description="Programming languages, frameworks, tools"
    )
    
    # Citations
    citations: List[Citation] = Field(
        default_factory=list,
        description="Sources used (official docs, community)"
    )
    
    class Config:
        use_enum_values = True


# ============================================================
# COST AGENT MODELS
# ============================================================

class UsageAssumptions(BaseModel):
    """Usage assumptions for cost calculation."""
    hours_per_month: int = 730  # 24*30.5
    requests_per_second: Optional[int] = None
    storage_gb: Optional[int] = None
    data_transfer_gb: Optional[int] = None
    additional_metrics: Dict = Field(default_factory=dict)


class ServiceCost(BaseModel):
    """Cost for a single cloud service."""
    service_name: str
    category: str  # compute, storage, database, networking, other
    pricing_model: str  # hourly, monthly, per-request, per-GB
    
    # Costs by scenario (monthly in USD)
    low_usage_monthly: float = Field(ge=0)
    medium_usage_monthly: float = Field(ge=0)
    high_usage_monthly: float = Field(ge=0)
    
    # Details
    assumptions: UsageAssumptions = Field(default_factory=UsageAssumptions)
    pricing_tier: str = ""
    pricing_url: str = Field(
        "",
        description="Link to pricing calculator or docs"
    )
    
    # Breakdown
    cost_breakdown: Dict = Field(
        default_factory=dict,
        description="Detailed cost components"
    )


class CostOptimization(BaseModel):
    """Cost optimization recommendation."""
    category: str
    recommendation: str
    estimated_savings_monthly: Optional[float] = None
    effort: Literal["low", "medium", "high"] = "medium"


class CostScenario(BaseModel):
    """Cost scenario for different usage patterns."""
    scenario: Literal["LOW", "MEDIUM", "HIGH"]
    usage_profile: str = Field(
        ...,
        description="Description of usage pattern (e.g., 'Dev/test workloads')"
    )
    total_monthly_cost: float = Field(ge=0, description="Total monthly cost in USD")
    service_breakdown: List['ServiceCost'] = Field(
        default_factory=list,
        description="Cost breakdown by service"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions for this scenario"
    )


class CostInput(BaseModel):
    """Input for Cost Agent."""
    
    architecture: ArchitectureOutput = Field(
        ...,
        description="Architecture design from Architecture Agent"
    )
    
    target_cloud: CloudPlatform
    
    region: str = Field(
        default="eastus",
        description="Cloud region for pricing"
    )
    
    usage_profile: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Expected usage profile"
    )


class CostOutput(BaseModel):
    """Output from Cost Agent."""
    
    target_cloud: CloudPlatform
    region: str
    currency: str = "USD"
    time_period: str = "monthly"
    
    # Cost scenarios (LOW, MEDIUM, HIGH)
    cost_scenarios: List[CostScenario] = Field(
        default_factory=list,
        description="Cost breakdown for different usage scenarios"
    )
    
    # Service costs (for backward compatibility)
    service_costs: List[ServiceCost] = Field(
        default_factory=list,
        description="Cost breakdown by service"
    )
    
    # Totals by scenario (for backward compatibility)
    total_monthly_cost_low: float = Field(ge=0, default=0.0)
    total_monthly_cost_medium: float = Field(ge=0, default=0.0)
    total_monthly_cost_high: float = Field(ge=0, default=0.0)
    
    # Category breakdown
    cost_by_category: Dict[str, float] = Field(
        default_factory=dict,
        description="Total cost per category (compute, storage, etc.)"
    )
    
    # Optimizations
    cost_optimizations: List[CostOptimization] = Field(
        default_factory=list,
        description="Cost optimization recommendations"
    )
    cost_optimization_recommendations: List[CostOptimization] = Field(
        default_factory=list,
        description="Cost optimization recommendations (deprecated, use cost_optimizations)"
    )
    
    # Metadata
    assumptions: List[str] = Field(
        default_factory=list,
        description="General assumptions made"
    )
    disclaimers: List[str] = Field(
        default_factory=lambda: [
            "Prices are estimates based on public data and may vary",
            "Actual costs depend on usage patterns and pricing changes",
            "±30% accuracy expected for POC"
        ]
    )
    confidence_level: Literal["low", "medium", "high"] = "medium"
    
    # Citations
    sources: List[Citation] = Field(
        default_factory=list,
        description="Pricing calculator links and documentation"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="Citations for pricing sources"
    )
    
    class Config:
        use_enum_values = True


# ============================================================
# DOCUMENTATION AGENT MODELS
# ============================================================

class DiagramOutput(BaseModel):
    """Generated diagram."""
    name: str
    format: Literal["mermaid", "drawio", "png", "svg"]
    content: str = Field(
        ...,
        description="Diagram content (syntax or base64)"
    )
    description: str = ""


class DocumentMetadata(BaseModel):
    """Document metadata."""
    title: str
    generated_at: datetime = Field(default_factory=datetime.now)
    cloud_platform: CloudPlatform
    version: str = "1.0"
    filename: str
    author: str = "Co-Pilot SE v2.0"


class DocumentationInput(BaseModel):
    """Input for Documentation Agent."""
    
    requirements: RequirementsOutput
    architecture: ArchitectureOutput
    costs: CostOutput
    
    output_format: Literal["markdown", "drawio", "pdf", "pptx"] = Field(
        default="markdown",
        description="Desired output format"
    )
    
    include_sections: List[str] = Field(
        default_factory=lambda: [
            "executive_summary",
            "requirements",
            "architecture",
            "cost_estimate",
            "deployment",
            "references"
        ],
        description="Sections to include in document"
    )


class DocumentationOutput(BaseModel):
    """Output from Documentation Agent."""
    
    format: str
    content: str = Field(
        ...,
        description="Generated document content (markdown, XML, etc.)"
    )
    
    diagrams: List[DiagramOutput] = Field(
        default_factory=list,
        description="Generated diagrams"
    )
    
    metadata: DocumentMetadata
    
    # Export options
    export_formats: List[str] = Field(
        default_factory=lambda: ["markdown", "pdf"],
        description="Available export formats"
    )
    
    class Config:
        use_enum_values = True


# ============================================================
# VALIDATION UTILITIES
# ============================================================

def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return pattern.match(url) is not None


def normalize_cloud_platform(platform: str) -> CloudPlatform:
    """Validate and normalize cloud platform."""
    platform_lower = platform.lower().strip()
    mapping = {
        'aws': CloudPlatform.AWS,
        'amazon': CloudPlatform.AWS,
        'amazon web services': CloudPlatform.AWS,
        'gcp': CloudPlatform.GCP,
        'google': CloudPlatform.GCP,
        'google cloud': CloudPlatform.GCP,
        'azure': CloudPlatform.AZURE,
        'microsoft azure': CloudPlatform.AZURE,
        'oracle': CloudPlatform.ORACLE,
        'oci': CloudPlatform.ORACLE,
        'oracle cloud': CloudPlatform.ORACLE,
    }
    return mapping.get(platform_lower, CloudPlatform.AZURE)
