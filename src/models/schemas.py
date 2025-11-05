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
    """Supported cloud platforms - Azure only for POC."""
    AZURE = "azure"


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
    AWAITING_STAGE_APPROVAL = "awaiting_stage_approval"  # NEW: Waiting for user to approve stage


class ConversationStage(str, Enum):
    """5-stage wizard workflow for interactive architecture design."""
    STAGE_1_REQUIREMENTS = "stage_1_requirements"  # Basic requirements discovery
    STAGE_2_COMPUTE = "stage_2_compute"            # Compute & scalability decisions
    STAGE_3_DATA = "stage_3_data"                  # Data architecture decisions
    STAGE_4_SECURITY = "stage_4_security"          # Security & compliance decisions
    STAGE_5_REVIEW = "stage_5_review"              # Final review & approval
    COMPLETE = "complete"                           # All stages approved, ready for architecture


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

class ClarificationQuestion(BaseModel):
    """A clarification question with context."""
    question: str = Field(..., description="The question to ask the user")
    rationale: str = Field(..., description="Why this question is important")
    options: Optional[List[str]] = Field(None, description="Optional predefined answer choices")
    category: Optional[str] = Field(None, description="Category of question (e.g., 'availability', 'security')")


class TradeOff(BaseModel):
    """A trade-off comparison between options."""
    option_name: str = Field(..., description="Name of this option (e.g., 'Premium Tier', 'Standard Tier')")
    pros: List[str] = Field(..., description="Advantages of this option")
    cons: List[str] = Field(..., description="Disadvantages of this option")
    cost_impact: str = Field(..., description="Cost impact (e.g., '$1,500/month', '+$800/month')")
    performance_impact: Optional[str] = Field(None, description="Performance implications")
    recommended: bool = Field(False, description="Whether this is the AI's recommended option")


class StageRecommendation(BaseModel):
    """AI's recommendation for a specific decision with full reasoning."""
    decision_name: str = Field(..., description="Name of the decision (e.g., 'Database Selection', 'Compute Platform')")
    recommendation: str = Field(..., description="The AI's recommended solution")
    reasoning: str = Field(..., description="Detailed explanation of WHY this is recommended")
    trade_offs: List[TradeOff] = Field(default_factory=list, description="Comparison of different options")
    alternatives: List[str] = Field(default_factory=list, description="Other viable alternatives with brief description")
    cost_impact: str = Field(..., description="Cost impact of this decision")
    dependencies: List[str] = Field(default_factory=list, description="What previous decisions this depends on")
    follow_up_questions: List[ClarificationQuestion] = Field(default_factory=list, description="Additional questions if user wants to modify")


class StageOutput(BaseModel):
    """Output from a single stage of the wizard."""
    stage: ConversationStage = Field(..., description="Which stage this output is for")
    stage_title: str = Field(..., description="Human-readable stage title")
    stage_description: str = Field(..., description="What this stage is about")
    recommendations: List[StageRecommendation] = Field(default_factory=list, description="AI recommendations for this stage")
    questions: List[ClarificationQuestion] = Field(default_factory=list, description="Questions for this stage")
    chain_of_thought: Optional[str] = Field(None, description="AI's reasoning process for this stage")
    decisions_made: List[str] = Field(default_factory=list, description="Key decisions made based on previous answers")
    estimated_cost: Optional[str] = Field(None, description="Running cost estimate with this stage's decisions")
    can_proceed: bool = Field(True, description="Whether user can proceed to next stage")
    requires_approval: bool = Field(True, description="Whether this stage requires explicit approval")


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

class ClarificationResponse(BaseModel):
    """User's response to clarification questions (legacy single-round)."""
    session_id: str = Field(..., description="Session ID from previous request")
    answers: Dict[str, str] = Field(..., description="Map of question to answer")
    
    @validator('answers')
    def validate_answers(cls, v):
        """Ensure at least one answer provided."""
        if not v:
            raise ValueError("At least one answer must be provided")
        return v


class StageApprovalResponse(BaseModel):
    """User's response to stage recommendations (new multi-stage flow)."""
    session_id: str = Field(..., description="Session ID from previous request")
    stage: ConversationStage = Field(..., description="Which stage this approval is for")
    
    # User action
    action: Literal["approve", "modify", "back", "see_alternatives"] = Field(
        ..., 
        description="What user wants to do: approve (proceed), modify (ask questions), back (previous stage), see_alternatives"
    )
    
    # If action == "modify", these provide additional context
    modification_request: Optional[str] = Field(None, description="What user wants to change or clarify")
    selected_alternative: Optional[str] = Field(None, description="If user selected a different option")
    
    # Answers to follow-up questions (if any were asked)
    answers: Optional[Dict[str, str]] = Field(None, description="Answers to follow-up clarification questions")
    
    # User feedback on recommendations
    feedback: Optional[str] = Field(None, description="Optional feedback on the recommendations")


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
    
    # For continuing after clarification
    session_id: Optional[str] = Field(
        None,
        description="Session ID for continuing a previous conversation"
    )
    clarification_answers: Optional[Dict[str, str]] = Field(
        None,
        description="Answers to clarifying questions from previous interaction"
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
    current_stage: Optional[str] = Field(None, description="Current workflow stage")
    
    # Agent outputs (optional based on status)
    requirements: Optional[Dict] = None
    architecture: Optional[Dict] = None
    costs: Optional[Dict] = None
    documentation: Optional[Dict] = None
    
    # Metadata
    citations: List[Citation] = Field(default_factory=list)
    workflow_metadata: WorkflowMetadata
    
    # ===== LEGACY SINGLE-ROUND CLARIFICATION (backwards compatible) =====
    # Interactive clarification (if status == NEEDS_CLARIFICATION)
    clarifying_questions: Optional[List[ClarificationQuestion]] = None
    chain_of_thought: Optional[str] = Field(None, description="Agent's reasoning process")
    decisions_made: Optional[List[str]] = Field(None, description="Decisions made so far")
    current_understanding: Optional[str] = Field(None, description="Current understanding summary")
    ambiguities: Optional[List[str]] = None
    
    # ===== NEW MULTI-STAGE WIZARD FLOW =====
    # Stage-based workflow (if status == AWAITING_STAGE_APPROVAL)
    conversation_stage: Optional[ConversationStage] = Field(None, description="Current conversation stage (1-5)")
    stage_output: Optional[StageOutput] = Field(None, description="Output for current stage")
    stages_completed: List[ConversationStage] = Field(default_factory=list, description="Stages user has approved")
    all_stage_decisions: Dict[str, List[str]] = Field(default_factory=dict, description="All decisions from previous stages")
    total_estimated_cost: Optional[str] = Field(None, description="Running total cost across all stages")
    can_go_back: bool = Field(False, description="Whether user can go back to previous stage")
    
    # Session management for multi-turn interaction
    session_id: Optional[str] = Field(None, description="Session ID for continuing conversation")
    awaiting_response: bool = Field(False, description="Whether system is waiting for user input")
    
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
    
    @validator('compliance', pre=True)
    def convert_compliance_to_list(cls, v):
        """Auto-convert string to list for compliance field."""
        if isinstance(v, str):
            return [v] if v else []
        elif isinstance(v, list):
            return v
        return []


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
    
    # Chain of Thought & Transparency
    chain_of_thought: Optional[str] = Field(
        None,
        description="Agent's reasoning process and understanding"
    )
    decisions_made: List[str] = Field(
        default_factory=list,
        description="Key decisions and assumptions made by the agent"
    )
    current_understanding: Optional[str] = Field(
        None,
        description="Summary of what the agent currently understands"
    )
    
    # Clarification
    needs_clarification: bool = False
    clarifying_questions: List[ClarificationQuestion] = Field(default_factory=list)
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
    """Validate and normalize cloud platform - always returns Azure for POC."""
    platform_lower = platform.lower().strip()
    mapping = {
        'azure': CloudPlatform.AZURE,
        'microsoft azure': CloudPlatform.AZURE,
        'microsoft': CloudPlatform.AZURE,
    }
    # Always default to Azure (POC is Azure-only)
    return mapping.get(platform_lower, CloudPlatform.AZURE)
