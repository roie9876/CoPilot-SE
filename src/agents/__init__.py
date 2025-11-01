"""
Specialized agents for Co-Pilot SE

This package contains the 4 specialized agents:
- Requirements Analysis Agent
- Multi-Cloud Architecture Design Agent
- Cost Estimation Agent
- Documentation Generation Agent

See docs/03-agent-specifications.md for details.
"""

from .base_agent import BaseAgent
from .requirements_agent import RequirementsAgent
from .architecture_agent import ArchitectureAgent
from .cost_agent import CostAgent
from .documentation_agent import DocumentationAgent

__all__ = [
    "BaseAgent",
    "RequirementsAgent",
    "ArchitectureAgent",
    "CostAgent",
    "DocumentationAgent",
]
