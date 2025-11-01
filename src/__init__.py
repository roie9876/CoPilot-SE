"""
Co-Pilot SE - Multi-Cloud Architecture Assistant

A POC AI-powered assistant that helps Solution Engineers design cloud architectures
across AWS, GCP, Azure, and Oracle Cloud using online data sources.

Version: 2.0.0
"""

from .orchestrator import MasterOrchestrator
from .agents import (
    RequirementsAgent,
    ArchitectureAgent,
    CostAgent,
    DocumentationAgent,
)
from .services import AzureOpenAIClient, BingSearchClient
from .models.schemas import OrchestratorInput, OrchestratorOutput

__version__ = "2.0.0"
__author__ = "Microsoft"

__all__ = [
    "MasterOrchestrator",
    "RequirementsAgent",
    "ArchitectureAgent",
    "CostAgent",
    "DocumentationAgent",
    "AzureOpenAIClient",
    "BingSearchClient",
    "OrchestratorInput",
    "OrchestratorOutput",
]
