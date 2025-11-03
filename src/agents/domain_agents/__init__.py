"""
Domain Agents for Knowledge Graph-based Requirements Gathering.

Each domain agent is a specialist in one area:
- IdentityDomainAgent: Azure AD, authentication, authorization
- RuntimeDomainAgent: AKS, App Service, Functions, VMs
- ResiliencyDomainAgent: HA, DR, RTO, RPO, multi-region
- NetworkingDomainAgent: VNet, subnets, public/private exposure
- DataDomainAgent: Databases, storage, backup, data residency
- SecurityDomainAgent: Compliance, secrets, logging, encryption

All agents inherit from BaseDomainAgent and implement:
- get_missing_critical_fields() - What's still unknown?
- generate_questions() - Ask only what's missing
- detect_conflicts() - Find contradictions
- update_confidence() - Calculate completeness score
"""

from src.agents.domain_agents.base_agent import BaseDomainAgent, DomainAgentQuestion
from src.agents.domain_agents.identity_agent import IdentityDomainAgent
from src.agents.domain_agents.runtime_agent import RuntimeDomainAgent
from src.agents.domain_agents.resiliency_agent import ResiliencyDomainAgent
from src.agents.domain_agents.networking_agent import NetworkingDomainAgent
from src.agents.domain_agents.data_agent import DataDomainAgent

__all__ = [
    "BaseDomainAgent",
    "DomainAgentQuestion",
    "IdentityDomainAgent",
    "RuntimeDomainAgent",
    "ResiliencyDomainAgent",
    "NetworkingDomainAgent",
    "DataDomainAgent",
]
