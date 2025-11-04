"""
Knowledge Graph Models for Adaptive Requirements Gathering.

This module defines the central Knowledge Graph schema that serves as
the single source of truth for all domain agents during requirements discovery.

Architecture:
- Each domain agent owns a section of the graph
- Agents read/write their section and update shared status
- Orchestrator uses the graph to determine which domain to run next
- Graph is complete when ready_for_design = True

Domain Sections:
1. Context - User intent and scenario classification
2. ExistingEnvironment - Brownfield vs greenfield detection
3. IdentityAccess - Azure AD, authentication, authorization
4. RuntimePlatform - Compute (AKS, App Service, Functions, VMs)
5. NetworkingConnectivity - VNet, subnets, public/private exposure
6. DataPersistence - Databases, storage, backup, compliance
7. ResiliencyDR - Multi-region, HA, RTO/RPO, failover
8. SecurityGovernance - Compliance frameworks, secrets, monitoring
9. Status - Critical gaps, conflicts, readiness flag
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class Intent(str, Enum):
    """User's high-level intent for the engagement."""
    NEW_DEPLOYMENT = "new_deployment"
    EXTEND_EXISTING = "extend_existing"
    DR_ONLY = "dr_only"
    MIGRATION = "migration"
    OPTIMIZE_SECURITY = "optimize_security"
    OPTIMIZE_COST = "optimize_cost"
    UNKNOWN = "unknown"


class CloudProvider(str, Enum):
    """Target cloud platform."""
    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"
    ORACLE = "oracle"
    MULTI_CLOUD = "multi_cloud"
    UNKNOWN = "unknown"


class WorkloadType(str, Enum):
    """Type of workload being deployed."""
    WEB_APP = "web_app"
    API = "api"
    E_COMMERCE = "e_commerce"
    DATA_PIPELINE = "data_pipeline"
    ML_SERVICE = "ml_service"
    BATCH_JOB = "batch_job"
    MICROSERVICES = "microservices"
    MOBILE_BACKEND = "mobile_backend"
    IOT = "iot"
    OTHER = "other"
    UNKNOWN = "unknown"


# ============================================================================
# DOMAIN MODELS
# ============================================================================

class Context(BaseModel):
    """
    High-level context about the user's request.
    
    This is extracted from the initial user input and guides which
    domain agents are relevant.
    """
    intent: Optional[Intent] = None
    cloud_provider: Optional[CloudProvider] = None
    workload_type: Optional[WorkloadType] = None
    business_description: Optional[str] = Field(
        None,
        description="Free text: what the application does, who uses it"
    )
    given_input_raw: str = Field(
        default="",
        description="Full original user message for reference"
    )


class ExistingEnvironment(BaseModel):
    """
    Information about existing infrastructure (brownfield scenarios).
    
    CRITICAL QUESTIONS:
    - Is this greenfield or brownfield?
    - Must we reuse existing subscriptions/tenants/landing zones?
    - Are there existing governance policies we must follow?
    """
    has_existing_env: Optional[bool] = Field(
        None,
        description="Is there existing cloud infrastructure we must work with?"
    )
    has_landing_zone: Optional[bool] = Field(
        None,
        description="Is there an existing Azure Landing Zone / AWS Control Tower?"
    )
    reuse_existing_subscription: Optional[bool] = Field(
        None,
        description="Must we deploy in an existing subscription/account?"
    )
    must_follow_existing_standards: Optional[bool] = Field(
        None,
        description="Are there existing governance/naming/tagging standards?"
    )
    notes: Optional[str] = Field(
        None,
        description="Free text about existing environment (e.g., 'AKS already in West Europe')"
    )


class IdentityAccess(BaseModel):
    """
    Identity and access management requirements.
    
    CRITICAL KNOWLEDGE (Azure AD / Entra ID):
    - Existing tenant vs new tenant changes EVERYTHING
    - Internal vs external users require different auth models
    - B2C vs B2B vs employee auth are fundamentally different
    - MFA policy impacts security and licensing costs
    
    CRITICAL QUESTIONS:
    1. Do you have an existing Azure AD tenant? (Cannot create new if enterprise)
    2. Who authenticates? (Internal employees vs external customers)
    3. Is MFA required? (Compliance and cost implications)
    """
    existing_tenant: Optional[bool] = Field(
        None,
        description="Is there an existing Azure AD (Entra ID) tenant to reuse?"
    )
    tenant_description: Optional[str] = Field(
        None,
        description="Details about existing tenant (e.g., 'Corporate Entra ID tenant')"
    )
    auth_users: Optional[str] = Field(
        None,
        description="Who authenticates? Options: internal_employees | external_partners | external_customers | public_users | mix"
    )
    federation_or_b2b: Optional[bool] = Field(
        None,
        description="Do external users need B2B guest access or federation?"
    )
    mfa_policy: Optional[str] = Field(
        None,
        description="MFA requirement: required | optional | not_required"
    )
    compliance_identity_constraints: Optional[str] = Field(
        None,
        description="Identity-related compliance requirements (e.g., 'Must use existing Conditional Access policies')"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this domain (0.0 = no info, 1.0 = complete)"
    )


class RuntimePlatform(BaseModel):
    """
    Compute platform and runtime requirements.
    
    CRITICAL KNOWLEDGE (AKS):
    - CNI plugin choice is IRREVERSIBLE after cluster creation
    - Azure CNI: Best performance, requires large subnet (/22 or /23)
    - Azure CNI Overlay: Recommended - good performance + saves IPs
    - Kubenet: Minimal IPs, adds network hop (slightly slower)
    - Network policy (Azure vs Calico vs Cilium) is also irreversible
    
    CRITICAL QUESTIONS:
    1. Which compute platform? (AKS, App Service, Functions, VMs)
    2. If AKS: Which CNI? (IRREVERSIBLE!)
    3. If AKS: Private cluster or public?
    4. Containerized or not?
    """
    target_runtime: Optional[str] = Field(
        None,
        description="Target platform: aks | app_service | functions | vm | vmss | container_instances | batch"
    )
    is_existing_runtime: Optional[bool] = Field(
        None,
        description="Is this extending an existing cluster/app service?"
    )
    containerized: Optional[bool] = Field(
        None,
        description="Is the workload containerized (Docker)?"
    )
    os_requirements: Optional[str] = Field(
        None,
        description="OS requirement: windows | linux | both"
    )
    needs_gpu: Optional[bool] = Field(
        None,
        description="Does workload require GPU nodes?"
    )
    
    # AKS-specific fields (CRITICAL - irreversible decisions)
    aks_cni: Optional[str] = Field(
        None,
        description="⚠️ IRREVERSIBLE: azure_cni | azure_cni_overlay | kubenet"
    )
    aks_network_policy: Optional[str] = Field(
        None,
        description="⚠️ IRREVERSIBLE: azure | calico | cilium | none"
    )
    aks_private_cluster: Optional[bool] = Field(
        None,
        description="Should AKS control plane be private (no public FQDN)?"
    )
    aks_ingress_model: Optional[str] = Field(
        None,
        description="Ingress: app_gateway_ingress | nginx_ingress | public_lb | internal_lb_only"
    )
    
    # App Service specific
    app_service_plan_tier: Optional[str] = Field(
        None,
        description="App Service tier: basic | standard | premium | isolated"
    )
    
    # General runtime settings
    scaling_strategy: Optional[str] = Field(
        None,
        description="Scaling: auto_scale | manual_scale | burst_spiky | steady_load"
    )
    deployment_style: Optional[str] = Field(
        None,
        description="Deployment: blue_green | rolling | canary | manual"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this domain"
    )


class NetworkingConnectivity(BaseModel):
    """
    Networking, connectivity, and exposure requirements.
    
    CRITICAL KNOWLEDGE:
    - Public vs private exposure changes EVERYTHING (WAF, ingress, cost)
    - Hub-spoke topology is best practice for enterprise
    - Private Link/Private Endpoints add cost but improve security
    - Subnet sizing must accommodate AKS CNI if using Azure CNI
    
    CRITICAL QUESTIONS:
    1. Is app public-facing or internal-only?
    2. Which Azure regions?
    3. Hub-spoke topology or flat VNet?
    4. Egress restrictions (no internet, restricted, open)?
    """
    exposure: Optional[str] = Field(
        None,
        description="Exposure: public_internet | private_only | internal_vpn_only | hybrid"
    )
    ingress_control_point: Optional[str] = Field(
        None,
        description="Ingress: global_lb | app_gateway | api_gateway | ingress_controller | none"
    )
    egress_policy: Optional[str] = Field(
        None,
        description="Egress: no_internet_egress | egress_restricted | full_open"
    )
    topology: Optional[str] = Field(
        None,
        description="Network topology: hub_spoke | flat_vnet | transit_gateway"
    )
    private_link_required: Optional[bool] = Field(
        None,
        description="Require Private Link/Private Endpoints for PaaS services?"
    )
    regions_in_scope: List[str] = Field(
        default_factory=list,
        description="Azure regions in scope (e.g., ['westeurope', 'northeurope'])"
    )
    subnet_requirements: Optional[str] = Field(
        None,
        description="Subnet sizing notes (e.g., 'AKS needs /22 for Azure CNI')"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this domain"
    )


class DataPersistence(BaseModel):
    """
    Data storage, databases, and persistence requirements.
    
    CRITICAL KNOWLEDGE:
    - SQL Database collation is IRREVERSIBLE after creation
    - Cosmos DB partition key design is hard to change
    - Hyperscale tier in Azure SQL cannot be downgraded
    - Data residency may block multi-region replication
    
    CRITICAL QUESTIONS:
    1. Which database engine? (Postgres, MySQL, SQL Server, Cosmos)
    2. Managed PaaS or self-hosted?
    3. Data residency requirements? (EU-only, US-only, etc.)
    4. PII/sensitive data? (Impacts encryption, compliance)
    """
    primary_db_engine: Optional[str] = Field(
        None,
        description="Database: postgres | mysql | mssql | cosmos | oracle | mongodb | redis | other"
    )
    managed_vs_self_hosted: Optional[str] = Field(
        None,
        description="Deployment: managed_paas | self_hosted | hybrid"
    )
    statefulness: Optional[str] = Field(
        None,
        description="Consistency: strongly_consistent_tx | eventual | mostly_read | stateless_session"
    )
    backup_expectation: Optional[str] = Field(
        None,
        description="Backup: point_in_time_restore | daily_backup_ok | manual | none"
    )
    data_residency: Optional[str] = Field(
        None,
        description="Data residency: eu_only | us_only | apac_only | global_ok | specific_country"
    )
    pii_sensitivity: Optional[bool] = Field(
        None,
        description="Does data include PII or sensitive information?"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this domain"
    )


class ResiliencyDR(BaseModel):
    """
    High availability and disaster recovery requirements.
    
    CRITICAL KNOWLEDGE:
    - Multi-region without RTO/RPO is meaningless
    - Active-active requires cross-region data replication
    - Data replication may violate data residency laws
    - RPO=0 (zero data loss) is expensive and complex
    
    CRITICAL QUESTIONS:
    1. Multi-region HA required?
    2. What is RTO (Recovery Time Objective) in minutes?
    3. What is RPO (Recovery Point Objective) in minutes?
    4. Can data be replicated across regions legally?
    """
    multi_region: Optional[bool] = Field(
        None,
        description="Is multi-region deployment required?"
    )
    ha_model: Optional[str] = Field(
        None,
        description="HA model: active_active | active_passive | single_region"
    )
    rto_minutes: Optional[int] = Field(
        None,
        description="Recovery Time Objective (RTO) in minutes. How quickly must service restore after regional failure?"
    )
    rpo_minutes: Optional[int] = Field(
        None,
        description="Recovery Point Objective (RPO) in minutes. How much data loss is acceptable?"
    )
    failover_method: Optional[str] = Field(
        None,
        description="Failover: dns_failover | global_lb | manual_runbook | automated"
    )
    can_replicate_data_cross_region: Optional[bool] = Field(
        None,
        description="Is cross-region data replication allowed (legally and technically)?"
    )
    regulatory_block_on_replication: Optional[bool] = Field(
        None,
        description="Do regulations prevent data from leaving specific regions?"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this domain"
    )


class SecurityGovernance(BaseModel):
    """
    Security, compliance, and governance requirements.
    
    CRITICAL KNOWLEDGE:
    - Compliance frameworks (PCI, HIPAA, ISO27001) have specific requirements
    - No public endpoints is a common enterprise policy
    - Key Vault is required for secrets management
    - Logging and monitoring are often mandatory
    
    CRITICAL QUESTIONS:
    1. Are public endpoints allowed?
    2. Which compliance frameworks apply? (PCI, HIPAA, ISO27001, SOC2)
    3. Secrets management approach?
    4. Logging/monitoring required?
    """
    internet_policy: Optional[str] = Field(
        None,
        description="Internet policy: no_public_endpoints | public_allowed_with_waf | public_ok | waf_required"
    )
    secrets_management: Optional[str] = Field(
        None,
        description="Secrets: key_vault | secrets_manager | env_vars | config_server"
    )
    logging_monitoring_required: Optional[bool] = Field(
        None,
        description="Is centralized logging/monitoring mandatory?"
    )
    compliance_frameworks: List[str] = Field(
        default_factory=list,
        description="Compliance: ['PCI', 'HIPAA', 'ISO27001', 'SOC2', 'GDPR', 'FedRAMP']"
    )
    must_use_existing_controls: Optional[bool] = Field(
        None,
        description="Must use existing security controls (policies, RBAC, etc)?"
    )
    encryption_requirements: Optional[str] = Field(
        None,
        description="Encryption: tde_and_transit | transit_only | at_rest_only | none"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this domain"
    )


class MonitoringObservability(BaseModel):
    """
    Monitoring, observability, and operational insights requirements.
    
    Covers:
    - Application monitoring (Application Insights, custom metrics)
    - Infrastructure monitoring (Azure Monitor, VM Insights)
    - Log aggregation (Log Analytics, diagnostic settings)
    - Alerting and dashboards
    - Distributed tracing (APM)
    """
    
    # CRITICAL FIELDS
    monitoring_strategy: Optional[str] = Field(
        None,
        description="Monitoring approach: full_observability | basic_monitoring | custom_only | none"
    )
    log_retention_days: Optional[int] = Field(
        None,
        description="How long to retain logs (30, 90, 180, 365 days)"
    )
    apm_required: Optional[bool] = Field(
        None,
        description="Need Application Performance Monitoring (distributed tracing, dependency mapping)?"
    )
    alert_integrations: Optional[str] = Field(
        None,
        description="Alert routing: teams | email | pagerduty | servicenow | webhook"
    )
    
    # OPTIONAL FIELDS
    custom_metrics: Optional[bool] = Field(
        None,
        description="Need custom business metrics beyond standard Azure metrics?"
    )
    centralized_logging: Optional[bool] = Field(
        None,
        description="Aggregate logs from multiple services into single Log Analytics workspace?"
    )
    dashboard_requirements: Optional[str] = Field(
        None,
        description="Dashboard needs: azure_portal | grafana | power_bi | custom"
    )
    compliance_logging: Optional[bool] = Field(
        None,
        description="Need audit logs for compliance (SOC 2, HIPAA, PCI-DSS)?"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this domain"
    )


class Conflict(BaseModel):
    """
    Represents a detected contradiction between domain requirements.
    
    Example conflicts:
    - networking.exposure = "private_only" BUT runtime.aks_ingress_model = "public_lb"
    - resiliency.multi_region = True BUT data.can_replicate_data_cross_region = False
    - resiliency.rto_minutes = 5 BUT no multi-region deployment
    """
    conflict_id: str = Field(
        ...,
        description="Unique identifier for this conflict"
    )
    domains_involved: List[str] = Field(
        ...,
        description="Which domains are in conflict (e.g., ['networking', 'runtime'])"
    )
    description: str = Field(
        ...,
        description="Human-readable description of the conflict"
    )
    question: str = Field(
        ...,
        description="Clarification question to resolve the conflict"
    )
    severity: str = Field(
        default="high",
        description="Severity: critical | high | medium | low"
    )


class Status(BaseModel):
    """
    Overall status of the Knowledge Graph.
    
    Used by orchestrator to determine:
    1. Which domains still need questions
    2. Whether there are unresolved conflicts
    3. Whether we're ready to generate architecture
    """
    critical_gaps: List[str] = Field(
        default_factory=list,
        description="List of required fields still missing (e.g., ['identity.existing_tenant', 'runtime.aks_cni'])"
    )
    conflicts: List[Conflict] = Field(
        default_factory=list,
        description="Detected contradictions that need clarification"
    )
    ready_for_design: bool = Field(
        default=False,
        description="True when all critical gaps filled and conflicts resolved"
    )
    domains_completed: List[str] = Field(
        default_factory=list,
        description="Which domains have high confidence and no missing critical fields"
    )
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average confidence across all relevant domains"
    )


# ============================================================================
# MAIN KNOWLEDGE GRAPH
# ============================================================================

class KnowledgeGraph(BaseModel):
    """
    Central shared state for adaptive requirements gathering.
    
    This is the single source of truth for all domain agents.
    
    Workflow:
    1. Intent Extractor fills Context from user input
    2. Orchestrator determines which domains are relevant
    3. Each domain agent reads its section, identifies gaps, asks questions
    4. Domain agents update their section and detect conflicts
    5. When ready_for_design = True, pass to Architecture Agent (Stage 2)
    
    Design Principles:
    - Adaptive: Only asks what's missing (not fixed rounds)
    - Domain experts: Each agent knows its specialty
    - Conflict detection: Explicit contradiction handling
    - Confidence tracking: Know what's certain vs uncertain
    - Extensible: Easy to add new domains
    """
    # Core context
    context: Context = Field(
        default_factory=Context,
        description="High-level intent and scenario classification"
    )
    
    # Domain sections (each owned by a domain agent)
    existing_environment: ExistingEnvironment = Field(
        default_factory=ExistingEnvironment,
        description="Brownfield vs greenfield information"
    )
    identity_access: IdentityAccess = Field(
        default_factory=IdentityAccess,
        description="Identity, authentication, authorization (Azure AD)"
    )
    runtime_platform: RuntimePlatform = Field(
        default_factory=RuntimePlatform,
        description="Compute platform (AKS, App Service, Functions, VMs)"
    )
    networking_connectivity: NetworkingConnectivity = Field(
        default_factory=NetworkingConnectivity,
        description="Networking, VNet, subnets, public/private exposure"
    )
    data_persistence: DataPersistence = Field(
        default_factory=DataPersistence,
        description="Databases, storage, backup, data residency"
    )
    resiliency_dr: ResiliencyDR = Field(
        default_factory=ResiliencyDR,
        description="High availability, disaster recovery, RTO/RPO"
    )
    security_governance: SecurityGovernance = Field(
        default_factory=SecurityGovernance,
        description="Security, compliance, governance requirements"
    )
    monitoring_observability: MonitoringObservability = Field(
        default_factory=MonitoringObservability,
        description="Monitoring, logging, observability, and alerting requirements"
    )
    
    # Overall status
    status: Status = Field(
        default_factory=Status,
        description="Critical gaps, conflicts, readiness flag"
    )
    
    # Metadata
    session_id: Optional[str] = Field(
        None,
        description="Session identifier for tracking"
    )
    created_at: Optional[str] = Field(
        None,
        description="ISO timestamp when graph was created"
    )
    updated_at: Optional[str] = Field(
        None,
        description="ISO timestamp of last update"
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "context": {
                    "intent": "new_deployment",
                    "cloud_provider": "azure",
                    "workload_type": "web_app",
                    "business_description": "E-commerce platform for retail",
                    "given_input_raw": "I want to build an e-commerce site on Azure"
                },
                "identity_access": {
                    "existing_tenant": True,
                    "auth_users": "external_customers",
                    "mfa_policy": "required",
                    "confidence": 0.9
                },
                "runtime_platform": {
                    "target_runtime": "aks",
                    "containerized": True,
                    "aks_cni": "azure_cni_overlay",
                    "aks_private_cluster": False,
                    "confidence": 0.85
                },
                "resiliency_dr": {
                    "multi_region": True,
                    "ha_model": "active_active",
                    "rto_minutes": 15,
                    "rpo_minutes": 5,
                    "confidence": 0.9
                },
                "status": {
                    "critical_gaps": [],
                    "conflicts": [],
                    "ready_for_design": True,
                    "overall_confidence": 0.88
                }
            }
        }
