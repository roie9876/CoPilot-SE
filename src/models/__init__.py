"""
Data models and schemas for Co-Pilot SE.

This module contains all Pydantic models used for:
- Input/output validation
- Agent communication
- API contracts
"""

from src.models.schemas import (
    # Enums
    CloudPlatform,
    IndustryVertical,
    WorkflowStatus,
    ErrorType,
    
    # Base models
    Citation,
    WorkflowMetadata,
    
    # Orchestrator models
    OrchestratorInput,
    OrchestratorOutput,
    
    # Requirements Agent models
    RequirementsInput,
    RequirementsOutput,
    NonFunctionalRequirements,
    TechnicalConstraints,
    
    # Architecture Agent models
    ArchitectureInput,
    ArchitectureOutput,
    ServiceSelection,
    ServiceConfiguration,
    WellArchitectedAnalysis,
    
    # Cost Agent models
    CostInput,
    CostOutput,
    ServiceCost,
    UsageAssumptions,
    CostOptimization,
    CostScenario,
    
    # Documentation Agent models
    DocumentationInput,
    DocumentationOutput,
    DiagramOutput,
    DocumentMetadata,
    
    # Error models
    AgentError,
    AgentException,
)

__all__ = [
    # Enums
    "CloudPlatform",
    "IndustryVertical",
    "WorkflowStatus",
    "ErrorType",
    
    # Base models
    "Citation",
    "WorkflowMetadata",
    
    # Orchestrator
    "OrchestratorInput",
    "OrchestratorOutput",
    
    # Requirements Agent
    "RequirementsInput",
    "RequirementsOutput",
    "NonFunctionalRequirements",
    "TechnicalConstraints",
    
    # Architecture Agent
    "ArchitectureInput",
    "ArchitectureOutput",
    "ServiceSelection",
    "ServiceConfiguration",
    "WellArchitectedAnalysis",
    
    # Cost Agent
    "CostInput",
    "CostOutput",
    "ServiceCost",
    "UsageAssumptions",
    "CostOptimization",
    "CostScenario",
    
    # Documentation Agent
    "DocumentationInput",
    "DocumentationOutput",
    "DiagramOutput",
    "DocumentMetadata",
    
    # Errors
    "AgentError",
    "AgentException",
]
