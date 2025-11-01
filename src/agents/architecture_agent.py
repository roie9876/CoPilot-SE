"""
Architecture Agent - Designs Azure cloud architectures.

This agent:
1. Analyzes requirements and selects appropriate Azure services
2. Applies Azure Well-Architected Framework principles
3. Generates architecture diagrams (Mermaid syntax)
4. Provides design rationale and trade-offs
5. Considers security, scalability, and cost optimization
"""

from typing import Dict, List, Optional
import logging

from src.agents.base_agent import BaseAgent
from src.models.schemas import (
    ArchitectureInput,
    ArchitectureOutput,
    ServiceSelection,
    ServiceConfiguration,
    WellArchitectedAnalysis,
    Citation,
    RequirementsOutput,
    CloudPlatform,
    ErrorType,
)

logger = logging.getLogger(__name__)


class ArchitectureAgent(BaseAgent):
    """
    Azure architecture design agent.
    
    Follows Azure best practices:
    - Managed Identity for authentication
    - Encryption at rest and in transit
    - Multi-AZ deployment for high availability
    - Auto-scaling for performance
    - Cost optimization with reserved instances
    """
    
    # Azure service catalog by category
    AZURE_SERVICES = {
        "compute": {
            "Azure App Service": {
                "use_case": "Web apps, REST APIs, mobile backends",
                "best_for": ["web applications", "api", "rest", "mobile backend"],
                "sku_options": ["F1 (Free)", "B1 (Basic)", "S1 (Standard)", "P1v2 (Premium)"],
                "features": ["Built-in CI/CD", "Auto-scaling", "Custom domains", "SSL"],
                "managed_identity": True
            },
            "Azure Functions": {
                "use_case": "Serverless compute, event-driven",
                "best_for": ["serverless", "event-driven", "microservices", "background jobs"],
                "sku_options": ["Consumption", "Premium", "Dedicated"],
                "features": ["Auto-scaling", "Pay-per-execution", "Multiple triggers"],
                "managed_identity": True
            },
            "Azure Kubernetes Service (AKS)": {
                "use_case": "Container orchestration, microservices",
                "best_for": ["containers", "microservices", "kubernetes", "complex applications"],
                "sku_options": ["Free", "Standard", "Premium"],
                "features": ["Auto-scaling", "Azure AD integration", "Private cluster"],
                "managed_identity": True
            },
            "Azure Container Instances (ACI)": {
                "use_case": "Simple container deployments",
                "best_for": ["containers", "simple deployments", "batch jobs"],
                "sku_options": ["Per-second billing"],
                "features": ["Fast startup", "Public IP", "Virtual network"],
                "managed_identity": True
            },
            "Azure Virtual Machines": {
                "use_case": "Full control over OS and software",
                "best_for": ["legacy applications", "custom software", "full control"],
                "sku_options": ["B-series (Burstable)", "D-series (General)", "E-series (Memory)"],
                "features": ["Multiple OS choices", "Hybrid benefit", "Reserved instances"],
                "managed_identity": True
            }
        },
        "storage": {
            "Azure Blob Storage": {
                "use_case": "Object storage for unstructured data",
                "best_for": ["files", "images", "videos", "backups", "data lake"],
                "tiers": ["Hot", "Cool", "Archive"],
                "features": ["Versioning", "Soft delete", "Lifecycle management"],
                "encryption": True
            },
            "Azure Files": {
                "use_case": "Managed file shares (SMB/NFS)",
                "best_for": ["file shares", "smb", "shared storage"],
                "tiers": ["Premium", "Transaction optimized", "Hot", "Cool"],
                "features": ["Active Directory integration", "Snapshots"],
                "encryption": True
            },
            "Azure Queue Storage": {
                "use_case": "Message queue for async processing",
                "best_for": ["message queue", "async", "decoupling"],
                "features": ["At-least-once delivery", "Large messages"],
                "encryption": True
            }
        },
        "database": {
            "Azure SQL Database": {
                "use_case": "Fully managed relational database",
                "best_for": ["relational", "sql", "transactional"],
                "tiers": ["Basic", "Standard", "Premium", "Business Critical"],
                "features": ["Auto-scaling", "Built-in HA", "Geo-replication", "Backup"],
                "managed_identity": True
            },
            "Azure Cosmos DB": {
                "use_case": "Globally distributed NoSQL database",
                "best_for": ["nosql", "global", "low latency", "multi-model"],
                "apis": ["SQL", "MongoDB", "Cassandra", "Gremlin", "Table"],
                "features": ["Multi-region writes", "Automatic failover", "SLA"],
                "managed_identity": True
            },
            "Azure Database for PostgreSQL": {
                "use_case": "Managed PostgreSQL database",
                "best_for": ["postgresql", "postgres", "open source"],
                "tiers": ["Flexible Server", "Hyperscale"],
                "features": ["Built-in HA", "Automated backups", "Read replicas"],
                "managed_identity": True
            },
            "Azure Database for MySQL": {
                "use_case": "Managed MySQL database",
                "best_for": ["mysql", "open source"],
                "tiers": ["Flexible Server"],
                "features": ["Built-in HA", "Automated backups"],
                "managed_identity": True
            },
            "Azure Cache for Redis": {
                "use_case": "In-memory caching",
                "best_for": ["cache", "redis", "session", "performance"],
                "tiers": ["Basic", "Standard", "Premium"],
                "features": ["Clustering", "Persistence", "Geo-replication"],
                "managed_identity": True
            }
        },
        "networking": {
            "Azure Application Gateway": {
                "use_case": "Web traffic load balancer with WAF",
                "best_for": ["load balancer", "waf", "ssl termination"],
                "features": ["SSL offload", "Auto-scaling", "WAF", "URL routing"],
                "security": True
            },
            "Azure Front Door": {
                "use_case": "Global load balancer and CDN",
                "best_for": ["cdn", "global", "low latency", "ddos protection"],
                "features": ["WAF", "SSL", "Caching", "URL rewrite"],
                "security": True
            },
            "Azure Load Balancer": {
                "use_case": "Layer 4 load balancing",
                "best_for": ["load balancer", "high availability"],
                "tiers": ["Basic", "Standard"],
                "features": ["Health probes", "Outbound rules"],
                "security": False
            }
        },
        "security": {
            "Azure Key Vault": {
                "use_case": "Secrets, keys, and certificates management",
                "best_for": ["secrets", "keys", "certificates", "security"],
                "features": ["RBAC", "Soft delete", "Purge protection"],
                "managed_identity": True,
                "required": True  # Always recommended
            },
            "Azure Active Directory (Entra ID)": {
                "use_case": "Identity and access management",
                "best_for": ["authentication", "authorization", "sso"],
                "features": ["SSO", "MFA", "Conditional access"],
                "required": True  # Always recommended
            }
        },
        "monitoring": {
            "Azure Monitor": {
                "use_case": "Monitoring and diagnostics",
                "best_for": ["monitoring", "logging", "metrics"],
                "features": ["Application Insights", "Log Analytics", "Alerts"],
                "required": True  # Always recommended
            }
        }
    }
    
    def __init__(self):
        """Initialize Architecture Agent."""
        super().__init__(name="ArchitectureAgent")
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Design Azure architecture based on requirements.
        
        Args:
            input_data: Dict with 'requirements', 'target_cloud', 'region'
            
        Returns:
            ArchitectureOutput dict
        """
        self._record_invocation()
        
        try:
            # Validate input
            arch_input = ArchitectureInput(**input_data)
            
            # Only process Azure (for now)
            if arch_input.target_cloud != CloudPlatform.AZURE:
                raise self._create_error(
                    f"Only Azure is supported in current implementation. Got: {arch_input.target_cloud}",
                    error_type=ErrorType.VALIDATION_ERROR,
                    retryable=False
                )
            
            self.logger.info(f"Designing Azure architecture for region: {arch_input.region}")
            
            # Select services based on requirements
            services = self._select_azure_services(arch_input.requirements)
            
            # Generate architecture diagram
            diagram = self._generate_mermaid_diagram(services, arch_input.requirements)
            
            # Apply Well-Architected Framework
            well_architected = self._analyze_well_architected(services, arch_input.requirements)
            
            # Deployment considerations
            deployment = self._get_deployment_considerations(
                services, arch_input.requirements, arch_input.region
            )
            
            # Trade-offs
            trade_offs = self._identify_trade_offs(services)
            
            # Technology stack
            tech_stack = self._determine_tech_stack(arch_input.requirements)
            
            # Citations
            citations = self._generate_citations(services)
            
            # Build output
            output = ArchitectureOutput(
                target_cloud=CloudPlatform.AZURE,
                region=arch_input.region or "eastus",
                architecture_summary=self._generate_summary(services, arch_input.requirements),
                services=services,
                architecture_diagram=diagram,
                diagram_format="mermaid",
                design_rationale=well_architected,
                deployment_considerations=deployment,
                trade_offs=trade_offs,
                technology_stack=tech_stack,
                citations=citations
            )
            
            self.logger.info(f"Architecture designed with {len(services)} services")
            
            return output
        
        except Exception as e:
            self.logger.error(f"Error designing architecture: {e}", exc_info=True)
            error = self._create_error(
                f"Failed to design architecture: {str(e)}",
                error_type=ErrorType.UNKNOWN_ERROR,
                retryable=True
            )
            raise error
    
    def _select_azure_services(
        self, requirements: RequirementsOutput
    ) -> List[ServiceSelection]:
        """
        Select appropriate Azure services based on requirements.
        
        Args:
            requirements: Extracted requirements
            
        Returns:
            List of selected services with rationale
        """
        services = []
        
        # Always include foundational services
        services.extend(self._add_foundational_services())
        
        # Compute services
        compute_service = self._select_compute_service(requirements)
        if compute_service:
            services.append(compute_service)
        
        # Storage services
        storage_services = self._select_storage_services(requirements)
        services.extend(storage_services)
        
        # Database services
        database_service = self._select_database_service(requirements)
        if database_service:
            services.append(database_service)
        
        # Networking services
        networking_services = self._select_networking_services(requirements)
        services.extend(networking_services)
        
        # Caching if needed
        if self._needs_caching(requirements):
            services.append(self._add_redis_cache())
        
        return services
    
    def _add_foundational_services(self) -> List[ServiceSelection]:
        """Add foundational Azure services (always required)."""
        return [
            ServiceSelection(
                category="security",
                service_name="Azure Key Vault",
                rationale="Secure storage for secrets, keys, and certificates. Required for secure credential management.",
                configuration=ServiceConfiguration(
                    sku="Standard",
                    additional_settings={
                        "soft_delete_enabled": True,
                        "purge_protection_enabled": True,
                        "rbac_enabled": True
                    }
                ),
                alternatives=["Hardcoded secrets (NOT RECOMMENDED)"],
                estimated_monthly_cost=5.0
            ),
            ServiceSelection(
                category="security",
                service_name="Azure Active Directory (Entra ID)",
                rationale="Identity and access management for secure authentication and authorization.",
                configuration=ServiceConfiguration(
                    sku="Free",
                    additional_settings={
                        "mfa_enabled": True,
                        "conditional_access": True
                    }
                ),
                alternatives=["Custom auth implementation (NOT RECOMMENDED)"],
                estimated_monthly_cost=0.0
            ),
            ServiceSelection(
                category="monitoring",
                service_name="Azure Monitor",
                rationale="Comprehensive monitoring, logging, and diagnostics for all Azure resources.",
                configuration=ServiceConfiguration(
                    additional_settings={
                        "application_insights": True,
                        "log_analytics_workspace": True
                    }
                ),
                alternatives=["Third-party monitoring (Datadog, New Relic)"],
                estimated_monthly_cost=50.0
            )
        ]
    
    def _select_compute_service(
        self, requirements: RequirementsOutput
    ) -> Optional[ServiceSelection]:
        """Select appropriate compute service."""
        func_reqs = ' '.join(requirements.functional_requirements).lower()
        constraints = requirements.technical_constraints
        
        # Check for serverless indicators
        if any(kw in func_reqs for kw in ['serverless', 'event-driven', 'background', 'scheduled']):
            return ServiceSelection(
                category="compute",
                service_name="Azure Functions",
                rationale="Serverless compute ideal for event-driven workloads. Pay only for execution time, automatic scaling.",
                configuration=ServiceConfiguration(
                    sku="Consumption Plan",
                    auto_scaling={"enabled": True, "min_instances": 0, "max_instances": 200}
                ),
                alternatives=["Azure App Service", "Azure Container Instances"],
                estimated_monthly_cost=20.0
            )
        
        # Check for container/microservices
        if any(kw in func_reqs for kw in ['container', 'kubernetes', 'microservices', 'k8s']):
            # Check if team has K8s skills
            if 'kubernetes' in str(constraints.team_skills).lower():
                return ServiceSelection(
                    category="compute",
                    service_name="Azure Kubernetes Service (AKS)",
                    rationale="Container orchestration for complex microservices. Team has Kubernetes expertise.",
                    configuration=ServiceConfiguration(
                        sku="Standard",
                        replicas=3,
                        auto_scaling={"enabled": True, "min_nodes": 3, "max_nodes": 10}
                    ),
                    alternatives=["Azure Container Instances", "Azure App Service for Containers"],
                    estimated_monthly_cost=200.0
                )
            else:
                return ServiceSelection(
                    category="compute",
                    service_name="Azure Container Instances (ACI)",
                    rationale="Simple container deployment without orchestration complexity. Easier to manage for smaller teams.",
                    configuration=ServiceConfiguration(
                        replicas=2
                    ),
                    alternatives=["Azure App Service for Containers"],
                    estimated_monthly_cost=50.0
                )
        
        # Default to App Service for web applications
        return ServiceSelection(
            category="compute",
            service_name="Azure App Service",
            rationale="Fully managed platform for web apps and APIs. Built-in CI/CD, auto-scaling, and custom domains.",
            configuration=ServiceConfiguration(
                sku="S1 (Standard)" if self._needs_scaling(requirements) else "B1 (Basic)",
                replicas=2 if self._needs_ha(requirements) else 1,
                auto_scaling={"enabled": self._needs_scaling(requirements)}
            ),
            alternatives=["Azure Functions", "Azure Virtual Machines"],
            estimated_monthly_cost=74.0  # S1 tier
        )
    
    def _select_storage_services(
        self, requirements: RequirementsOutput
    ) -> List[ServiceSelection]:
        """Select storage services."""
        services = []
        func_reqs = ' '.join(requirements.functional_requirements).lower()
        
        # Always add blob storage for general file storage
        services.append(
            ServiceSelection(
                category="storage",
                service_name="Azure Blob Storage",
                rationale="Scalable object storage for images, files, backups, and unstructured data.",
                configuration=ServiceConfiguration(
                    storage_gb=100,
                    additional_settings={
                        "tier": "Hot",
                        "redundancy": "LRS",
                        "encryption": True,
                        "versioning": True
                    }
                ),
                alternatives=["Azure Files", "Third-party storage"],
                estimated_monthly_cost=20.0
            )
        )
        
        # Add queue storage for async processing
        if any(kw in func_reqs for kw in ['queue', 'async', 'background', 'message']):
            services.append(
                ServiceSelection(
                    category="storage",
                    service_name="Azure Queue Storage",
                    rationale="Reliable message queue for asynchronous processing and decoupling components.",
                    configuration=ServiceConfiguration(),
                    alternatives=["Azure Service Bus", "Azure Event Grid"],
                    estimated_monthly_cost=5.0
                )
            )
        
        return services
    
    def _select_database_service(
        self, requirements: RequirementsOutput
    ) -> Optional[ServiceSelection]:
        """Select appropriate database service."""
        func_reqs = ' '.join(requirements.functional_requirements).lower()
        constraints = requirements.technical_constraints
        
        # Check for NoSQL indicators
        if any(kw in func_reqs for kw in ['nosql', 'document', 'json', 'flexible schema', 'global']):
            return ServiceSelection(
                category="database",
                service_name="Azure Cosmos DB",
                rationale="Globally distributed NoSQL database with multi-model support. Low latency and automatic scaling.",
                configuration=ServiceConfiguration(
                    additional_settings={
                        "api": "SQL (Core)",
                        "consistency": "Session",
                        "multi_region": self._needs_global(requirements)
                    }
                ),
                alternatives=["Azure Table Storage", "MongoDB on Azure VM"],
                estimated_monthly_cost=150.0
            )
        
        # Check for PostgreSQL preference
        if 'postgresql' in str(constraints.team_skills).lower() or 'postgres' in func_reqs:
            return ServiceSelection(
                category="database",
                service_name="Azure Database for PostgreSQL",
                rationale="Fully managed PostgreSQL database. Team familiar with PostgreSQL.",
                configuration=ServiceConfiguration(
                    sku="Flexible Server - B1ms",
                    storage_gb=32,
                    additional_settings={
                        "high_availability": self._needs_ha(requirements),
                        "backup_retention_days": 7
                    }
                ),
                alternatives=["Azure SQL Database", "Cosmos DB"],
                estimated_monthly_cost=80.0
            )
        
        # Default to Azure SQL Database
        return ServiceSelection(
            category="database",
            service_name="Azure SQL Database",
            rationale="Fully managed relational database with built-in HA, auto-scaling, and intelligent performance.",
            configuration=ServiceConfiguration(
                sku="Standard S1",
                storage_gb=250,
                additional_settings={
                    "geo_replication": self._needs_global(requirements),
                    "auto_failover": self._needs_ha(requirements),
                    "backup_retention_days": 7
                }
            ),
            alternatives=["Azure Database for PostgreSQL", "Azure Database for MySQL"],
            estimated_monthly_cost=100.0
        )
    
    def _select_networking_services(
        self, requirements: RequirementsOutput
    ) -> List[ServiceSelection]:
        """Select networking services."""
        services = []
        
        # Check if WAF/security is needed
        compliance = requirements.non_functional_requirements.compliance
        if compliance or self._needs_security(requirements):
            services.append(
                ServiceSelection(
                    category="networking",
                    service_name="Azure Application Gateway",
                    rationale="Layer 7 load balancer with Web Application Firewall (WAF) for security and SSL termination.",
                    configuration=ServiceConfiguration(
                        sku="WAF_v2",
                        additional_settings={
                            "waf_enabled": True,
                            "auto_scaling": True,
                            "ssl_policy": "AppGwSslPolicy20220101"
                        }
                    ),
                    alternatives=["Azure Front Door", "Azure Load Balancer"],
                    estimated_monthly_cost=140.0
                )
            )
        elif self._needs_global(requirements):
            # Global apps need CDN
            services.append(
                ServiceSelection(
                    category="networking",
                    service_name="Azure Front Door",
                    rationale="Global load balancer and CDN for low latency worldwide. Includes WAF and DDoS protection.",
                    configuration=ServiceConfiguration(
                        sku="Standard",
                        additional_settings={
                            "waf_enabled": True,
                            "caching_enabled": True
                        }
                    ),
                    alternatives=["Azure Application Gateway + CDN"],
                    estimated_monthly_cost=200.0
                )
            )
        
        return services
    
    def _add_redis_cache(self) -> ServiceSelection:
        """Add Redis cache for performance."""
        return ServiceSelection(
            category="database",
            service_name="Azure Cache for Redis",
            rationale="In-memory caching for improved performance, session management, and reduced database load.",
            configuration=ServiceConfiguration(
                sku="Basic C0",
                storage_gb=1,  # Changed from 0.25 to 1 (minimum is 1 GB for Basic C0)
                additional_settings={"clustering": False}
            ),
            alternatives=["Application-level caching"],
            estimated_monthly_cost=16.0
        )
    
    def _needs_caching(self, requirements: RequirementsOutput) -> bool:
        """Check if caching is needed."""
        scalability = requirements.non_functional_requirements.scalability
        performance = requirements.non_functional_requirements.performance
        
        # Cache if many users or performance is critical
        if scalability and scalability.get("target_users", 0) > 5000:
            return True
        if performance and performance.get("latency_requirement") == "low":
            return True
        
        return False
    
    def _needs_scaling(self, requirements: RequirementsOutput) -> bool:
        """Check if auto-scaling is needed."""
        scalability = requirements.non_functional_requirements.scalability
        return scalability and scalability.get("target_users", 0) > 1000
    
    def _needs_ha(self, requirements: RequirementsOutput) -> bool:
        """Check if high availability is needed."""
        availability = requirements.non_functional_requirements.availability
        return bool(availability and availability.get("target_uptime"))
    
    def _needs_global(self, requirements: RequirementsOutput) -> bool:
        """Check if global distribution is needed."""
        func_reqs = ' '.join(requirements.functional_requirements).lower()
        return any(kw in func_reqs for kw in ['global', 'worldwide', 'multi-region', 'international'])
    
    def _needs_security(self, requirements: RequirementsOutput) -> bool:
        """Check if enhanced security is needed."""
        security = requirements.non_functional_requirements.security
        compliance = requirements.non_functional_requirements.compliance
        return bool(security or compliance)
    
    def _generate_mermaid_diagram(
        self, services: List[ServiceSelection], requirements: RequirementsOutput
    ) -> str:
        """
        Generate Mermaid architecture diagram.
        
        Args:
            services: Selected services
            requirements: Requirements
            
        Returns:
            Mermaid syntax diagram
        """
        # Group services by category
        by_category = {}
        for service in services:
            if service.category not in by_category:
                by_category[service.category] = []
            by_category[service.category].append(service)
        
        diagram = "graph TB\n"
        diagram += "    User[Users/Clients]\n\n"
        
        # Networking layer
        if "networking" in by_category:
            for svc in by_category["networking"]:
                node_id = svc.service_name.replace(" ", "")
                diagram += f"    {node_id}[\"{svc.service_name}\"]\n"
                diagram += f"    User --> {node_id}\n"
        
        # Compute layer
        if "compute" in by_category:
            for svc in by_category["compute"]:
                node_id = svc.service_name.replace(" ", "")
                diagram += f"    {node_id}[\"{svc.service_name}\"]\n"
                if "networking" in by_category:
                    net_id = by_category["networking"][0].service_name.replace(" ", "")
                    diagram += f"    {net_id} --> {node_id}\n"
                else:
                    diagram += f"    User --> {node_id}\n"
        
        # Storage layer
        if "storage" in by_category:
            compute_id = by_category["compute"][0].service_name.replace(" ", "") if "compute" in by_category else "User"
            for svc in by_category["storage"]:
                node_id = svc.service_name.replace(" ", "")
                diagram += f"    {node_id}[\"{svc.service_name}\"]\n"
                diagram += f"    {compute_id} --> {node_id}\n"
        
        # Database layer
        if "database" in by_category:
            compute_id = by_category["compute"][0].service_name.replace(" ", "") if "compute" in by_category else "User"
            for svc in by_category["database"]:
                node_id = svc.service_name.replace(" ", "")
                diagram += f"    {node_id}[(\"{svc.service_name}\")]\n"
                diagram += f"    {compute_id} --> {node_id}\n"
        
        # Security layer (Key Vault, AAD)
        if "security" in by_category:
            compute_id = by_category["compute"][0].service_name.replace(" ", "") if "compute" in by_category else "User"
            for svc in by_category["security"]:
                node_id = svc.service_name.replace(" ", "")
                diagram += f"    {node_id}[[\"{svc.service_name}\"]]\n"
                diagram += f"    {compute_id} -.->|Uses| {node_id}\n"
        
        # Monitoring
        if "monitoring" in by_category:
            for svc in by_category["monitoring"]:
                node_id = svc.service_name.replace(" ", "")
                diagram += f"    {node_id}[\"{svc.service_name}\"]\n"
                # All services connect to monitoring
                for category in ["compute", "storage", "database"]:
                    if category in by_category:
                        for s in by_category[category]:
                            s_id = s.service_name.replace(" ", "")
                            diagram += f"    {s_id} -.->|Logs/Metrics| {node_id}\n"
        
        # Add styling
        diagram += "\n    classDef compute fill:#0078D4,stroke:#004578,color:#fff\n"
        diagram += "    classDef storage fill:#FFB900,stroke:#FF8C00,color:#000\n"
        diagram += "    classDef database fill:#00BCF2,stroke:#0086A8,color:#fff\n"
        diagram += "    classDef security fill:#E81123,stroke:#A80015,color:#fff\n"
        diagram += "    classDef networking fill:#00B294,stroke:#00785A,color:#fff\n"
        
        return diagram
    
    def _analyze_well_architected(
        self, services: List[ServiceSelection], requirements: RequirementsOutput
    ) -> WellArchitectedAnalysis:
        """
        Analyze against Azure Well-Architected Framework.
        
        Returns:
            WellArchitectedAnalysis with 5 pillars
        """
        return WellArchitectedAnalysis(
            operational_excellence=(
                "Infrastructure as Code with Azure Bicep/Terraform recommended. "
                "Azure Monitor provides comprehensive logging and diagnostics. "
                "Managed services reduce operational overhead."
            ),
            security=(
                "Managed Identity eliminates credential management. "
                "Azure Key Vault secures all secrets. "
                "Entra ID provides enterprise-grade authentication. "
                f"{'WAF enabled for threat protection. ' if self._needs_security(requirements) else ''}"
                "All data encrypted at rest and in transit."
            ),
            reliability=(
                f"{'Multi-AZ deployment for high availability. ' if self._needs_ha(requirements) else ''}"
                "Automated backups and disaster recovery. "
                "Built-in failover for critical services. "
                f"{'Geo-replication for global resilience. ' if self._needs_global(requirements) else ''}"
            ),
            performance_efficiency=(
                "Auto-scaling adapts to demand. "
                f"{'Redis caching reduces latency. ' if self._needs_caching(requirements) else ''}"
                f"{'CDN for global content delivery. ' if self._needs_global(requirements) else ''}"
                "Managed services optimized for performance."
            ),
            cost_optimization=(
                "Consumption-based pricing for Azure Functions. "
                "Reserved instances recommended for predictable workloads. "
                "Lifecycle policies for storage cost reduction. "
                "Auto-scaling prevents over-provisioning."
            )
        )
    
    def _get_deployment_considerations(
        self, services: List[ServiceSelection], requirements: RequirementsOutput, region: str
    ) -> Dict:
        """Get deployment considerations."""
        return {
            "region": region or "eastus",
            "multi_az": self._needs_ha(requirements),
            "prerequisites": [
                "Azure subscription with appropriate permissions",
                "Resource group created",
                "Service Principal for CI/CD",
                "DNS zone for custom domains (if applicable)"
            ],
            "deployment_methods": [
                "Azure Bicep (recommended)",
                "Terraform",
                "Azure CLI",
                "Azure Portal"
            ],
            "estimated_deployment_time": "30-60 minutes"
        }
    
    def _identify_trade_offs(self, services: List[ServiceSelection]) -> List[str]:
        """Identify architectural trade-offs."""
        trade_offs = []
        
        # Check for serverless
        if any(s.service_name == "Azure Functions" for s in services):
            trade_offs.append(
                "Serverless (Functions): Lower cost but cold start latency. "
                "Consider Premium plan for always-warm instances."
            )
        
        # Check for managed vs. self-managed
        trade_offs.append(
            "Managed services: Higher convenience but less control. "
            "Acceptable trade-off for POC and most production workloads."
        )
        
        # Check for cost vs. performance
        trade_offs.append(
            "Standard/Basic SKUs: Cost-effective but may need upgrade for production scale. "
            "Monitor performance and adjust tiers as needed."
        )
        
        return trade_offs
    
    def _determine_tech_stack(self, requirements: RequirementsOutput) -> List[str]:
        """Determine recommended technology stack."""
        stack = []
        team_skills = [s.lower() for s in requirements.technical_constraints.team_skills]
        
        # Backend
        if 'python' in team_skills:
            stack.append("Backend: Python 3.11+ (FastAPI or Flask)")
        elif 'node' in team_skills or 'javascript' in team_skills:
            stack.append("Backend: Node.js 20 LTS (Express or NestJS)")
        elif 'c#' in team_skills or '.net' in team_skills:
            stack.append("Backend: .NET 8 (ASP.NET Core)")
        else:
            stack.append("Backend: Python 3.11+ or Node.js 20 LTS")
        
        # Frontend
        if 'react' in team_skills:
            stack.append("Frontend: React 18+ with TypeScript")
        elif 'angular' in team_skills:
            stack.append("Frontend: Angular 17+")
        elif 'vue' in team_skills:
            stack.append("Frontend: Vue 3")
        else:
            stack.append("Frontend: React 18+ with TypeScript (recommended)")
        
        # Infrastructure
        stack.append("Infrastructure as Code: Azure Bicep or Terraform")
        stack.append("CI/CD: GitHub Actions or Azure DevOps")
        stack.append("Monitoring: Azure Monitor + Application Insights")
        
        return stack
    
    def _generate_summary(
        self, services: List[ServiceSelection], requirements: RequirementsOutput
    ) -> str:
        """Generate architecture summary."""
        compute = [s for s in services if s.category == "compute"]
        database = [s for s in services if s.category == "database"]
        
        summary = f"Azure architecture with {len(services)} services. "
        
        if compute:
            summary += f"Compute: {compute[0].service_name}. "
        if database:
            summary += f"Database: {database[0].service_name}. "
        
        if self._needs_ha(requirements):
            summary += "High availability with multi-AZ deployment. "
        if self._needs_security(requirements):
            summary += "Enhanced security with WAF and compliance controls. "
        
        summary += "All services use Managed Identity and Azure Key Vault for secure authentication."
        
        return summary
    
    def _generate_citations(self, services: List[ServiceSelection]) -> List[Citation]:
        """Generate citations for Azure documentation."""
        citations = []
        
        # Add general Azure docs
        citations.append(
            Citation(
                title="Azure Well-Architected Framework",
                url="https://learn.microsoft.com/en-us/azure/well-architected/",
                relevance="Architecture design principles and best practices"
            )
        )
        
        # Add service-specific docs
        service_urls = {
            "Azure App Service": "https://learn.microsoft.com/en-us/azure/app-service/",
            "Azure Functions": "https://learn.microsoft.com/en-us/azure/azure-functions/",
            "Azure Kubernetes Service (AKS)": "https://learn.microsoft.com/en-us/azure/aks/",
            "Azure SQL Database": "https://learn.microsoft.com/en-us/azure/azure-sql/",
            "Azure Cosmos DB": "https://learn.microsoft.com/en-us/azure/cosmos-db/",
            "Azure Blob Storage": "https://learn.microsoft.com/en-us/azure/storage/blobs/",
            "Azure Key Vault": "https://learn.microsoft.com/en-us/azure/key-vault/"
        }
        
        for service in services:
            if service.service_name in service_urls:
                citations.append(
                    Citation(
                        title=f"{service.service_name} Documentation",
                        url=service_urls[service.service_name],
                        relevance=f"Service-specific configuration and best practices"
                    )
                )
        
        return citations
