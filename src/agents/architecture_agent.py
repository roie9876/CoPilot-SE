"""
Architecture Agent - Designs multi-cloud architectures.

This agent:
1. Analyzes requirements and selects appropriate cloud services
2. Applies cloud best practices and well-architected frameworks
3. Generates architecture diagrams (Mermaid syntax)
4. Provides design rationale and trade-offs
5. Considers security, scalability, and cost optimization

REFACTORED: Now uses Agent Framework SDK with ChatAgent + Bing grounding
"""

from typing import Dict, List, Optional, TYPE_CHECKING
import logging
import json

if TYPE_CHECKING:
    from src.models.knowledge_graph import KnowledgeGraph

from src.services.agent_framework_client import AgentFrameworkClient
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
    NonFunctionalRequirements,
    TechnicalConstraints,
    IndustryVertical,
)

logger = logging.getLogger(__name__)


class ArchitectureAgent:
    """
    Multi-cloud architecture design agent using Agent Framework SDK.
    
    Uses ChatAgent with Bing grounding to:
    - Research latest cloud services and best practices
    - Select appropriate services for requirements
    - Apply well-architected framework principles
    - Generate architecture diagrams
    - Provide citations from official documentation
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
        """Initialize Architecture Agent with Agent Framework and Bing."""
        self.logger = logging.getLogger(__name__)
        self.client = AgentFrameworkClient()
        
        # System instructions for multi-cloud architecture design
        self.instructions = """You are a Multi-Cloud Architecture Design Agent with expertise in AWS, Azure, GCP, and Oracle Cloud.

Your task is to design cloud architectures based on customer requirements.

**KEY RESPONSIBILITIES:**

1. **Service Selection**: Choose appropriate cloud services for the target platform
   - For AWS: EC2, Lambda, RDS, S3, ECS/EKS, etc.
   - For Azure: App Service, Functions, SQL Database, Blob Storage, AKS, etc.
   - For GCP: Compute Engine, Cloud Functions, Cloud SQL, Cloud Storage, GKE, etc.
   - For Oracle: Compute, Autonomous Database, Object Storage, OKE, etc.

2. **Best Practices**: Apply cloud well-architected framework principles
   - Security: Encryption, IAM, network isolation
   - Reliability: High availability, disaster recovery, multi-AZ
   - Performance: Caching, CDN, auto-scaling
   - Cost Optimization: Right-sizing, reserved instances, spot instances
   - Operational Excellence: Monitoring, logging, automation

3. **Architecture Diagram**: Generate Mermaid flowchart with STRICT syntax rules:
   - User/client layer
   - Edge/CDN layer (if needed)
   - Load balancing layer
   - Application layer
   - Data layer
   - Supporting services (monitoring, logging, caching)
   
   **CRITICAL MERMAID SYNTAX RULES:**
   - Use `graph TD` for top-down or `graph LR` for left-right
   - Each node MUST be on its own line
   - Node format: `NodeID[Display Text]` - ALWAYS close brackets with `]`
   - Connection format: `NodeA --> NodeB` - each on separate line
   - For labels on arrows: `NodeA -->|Label| NodeB`
   - Node IDs: Use ONLY letters/numbers, no spaces (e.g., `AppService` not `App Service`)
   - Special chars in labels: Wrap in quotes if using parentheses (e.g., `AS1["App Service (Region 1)"]`)
   - NEVER concatenate statements on same line (BAD: `]NodeB -->`, GOOD: `]\n    NodeB -->`)
   
   **EXAMPLE (CORRECT):**
   ```mermaid
   graph TD
       Users[Users/Clients]
       CDN[Azure Front Door]
       AppService[Azure App Service]
       DB[Azure SQL Database]
       
       Users --> CDN
       CDN --> AppService
       AppService --> DB
   ```

4. **Design Rationale**: Explain why each service was chosen

5. **Trade-offs**: Identify alternatives and their pros/cons

6. **Technology Stack**: Recommend programming languages and frameworks

7. **Deployment Considerations**: Infrastructure as Code, CI/CD, monitoring

8. **Citations**: ALWAYS provide URLs to official documentation for each service

**USE BING SEARCH TO:**
- Find latest cloud service documentation
- Research pricing and SKU options
- Verify service availability in regions
- Check compliance certifications
- Find best practice guides

**OUTPUT JSON FORMAT:**
```json
{
  "services": [
    {
      "name": "Service Name",
      "category": "compute|storage|database|networking|security|monitoring",
      "purpose": "What this service does in the architecture",
      "sku": "Recommended SKU/tier",
      "configuration": {"key": "value"},
      "alternatives": ["Alternative 1", "Alternative 2"],
      "rationale": "Why this service was chosen"
    }
  ],
  "architecture_diagram": "```mermaid\\ngraph TD\\n    Users[Users/Clients]\\n    LB[Load Balancer]\\n    App[Application Server]\\n    DB[Database]\\n    \\n    Users --> LB\\n    LB --> App\\n    App --> DB\\n```",
  "well_architected_analysis": {
    "security": ["security measure 1", "security measure 2"],
    "reliability": ["reliability measure 1"],
    "performance": ["performance optimization 1"],
    "cost_optimization": ["cost measure 1"],
    "operational_excellence": ["ops measure 1"]
  },
  "deployment_considerations": {
    "iac_tool": "Terraform|Bicep|CloudFormation",
    "cicd_pipeline": "Description of CI/CD setup",
    "monitoring_strategy": "Monitoring approach",
    "backup_strategy": "Backup and DR approach"
  },
  "trade_offs": ["Trade-off 1", "Trade-off 2"],
  "technology_stack": {
    "backend": ["Python", "Node.js"],
    "frontend": ["React"],
    "infrastructure": ["Terraform"]
  },
  "citations": [
    {
      "title": "Service Documentation Title",
      "url": "https://docs.cloud.com/...",
      "relevance": "Why this citation is relevant"
    }
  ]
}
```

Search for official documentation and provide accurate citations."""
        
        # Create agent with Bing grounding enabled
        self.agent = self.client.create_agent(
            name="ArchitectureAgent",
            instructions=self.instructions,
            enable_bing=True  # Enable web search for latest documentation
        )
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Design cloud architecture using Agent Framework with Bing research.
        
        Args:
            input_data: Dict with 'requirements', 'target_cloud', 'region'
            
        Returns:
            ArchitectureOutput dict
        """
        try:
            # Validate input
            arch_input = ArchitectureInput(**input_data)
            
            self.logger.info(
                f"Designing {arch_input.target_cloud} architecture for region: {arch_input.region}"
            )
            
            # Build comprehensive prompt
            req = arch_input.requirements
            prompt = f"""Design a cloud architecture for the following requirements:

**Target Cloud Platform:** {arch_input.target_cloud}
**Region:** {arch_input.region}

**Functional Requirements:**
{chr(10).join(f"- {r}" for r in req.functional_requirements)}

**Non-Functional Requirements:**
- Scalability: {req.non_functional_requirements.scalability}
- Performance: {req.non_functional_requirements.performance}
- Availability: {req.non_functional_requirements.availability}
- Security: {req.non_functional_requirements.security}
- Compliance: {req.non_functional_requirements.compliance}

**Technical Constraints:**
- Budget: {req.technical_constraints.budget}
- Team Skills: {req.technical_constraints.team_skills}
- Timeline: {req.technical_constraints.timeline}

**Implied Requirements:**
{chr(10).join(f"- {r}" for r in req.implied_requirements)}

Use Bing search to find the latest service documentation, pricing, and best practices for {arch_input.target_cloud}.

Design a complete architecture and provide the JSON response with all sections filled."""
            
            # Run agent with Bing grounding
            self.logger.info("Invoking Agent Framework ChatAgent with Bing grounding")
            result = await self.agent.run(prompt)
            
            if not result or not result.messages:
                raise ValueError("Agent returned empty response")
            
            # Extract response
            response = result.messages[-1].text
            self.logger.info(f"Agent response length: {len(response)} chars")
            
            # Parse JSON
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            
            try:
                arch_data = json.loads(json_str)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    arch_data = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not parse JSON from agent response")
            
            # Convert to ArchitectureOutput
            output = self._parse_architecture_response(arch_data, arch_input.target_cloud)
            
            # Set region with default if not provided
            output.region = arch_input.region or self._get_default_region(arch_input.target_cloud)
            
            self.logger.info(
                f"Architecture designed: {len(output.services)} services selected"
            )
            
            return output
        
        except Exception as e:
            self.logger.error(f"Error designing architecture: {e}", exc_info=True)
            raise RuntimeError(f"Failed to design architecture: {str(e)}")
            
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
    
    def _parse_architecture_response(self, arch_data: Dict, target_cloud: CloudPlatform) -> ArchitectureOutput:
        """
        Parse agent's JSON response into ArchitectureOutput.
        
        Args:
            arch_data: Parsed JSON from agent
            target_cloud: Target cloud platform
            
        Returns:
            ArchitectureOutput instance
        """
        # Parse well-architected analysis
        wa_data = arch_data.get("well_architected_analysis", {})
        
        # WellArchitectedAnalysis requires string fields, not lists
        # Convert lists to comma-separated strings
        def list_to_string(items):
            if isinstance(items, list):
                return ", ".join(str(i) for i in items)
            return str(items) if items else "N/A"
        
        wa = WellArchitectedAnalysis(
            operational_excellence=list_to_string(wa_data.get("operational_excellence", [])),
            security=list_to_string(wa_data.get("security", [])),
            reliability=list_to_string(wa_data.get("reliability", [])),
            performance_efficiency=list_to_string(wa_data.get("performance", [])),
            cost_optimization=list_to_string(wa_data.get("cost_optimization", []))
        )
        
        # Parse services FIRST (needed for diagram validation)
        services = []
        for svc_data in arch_data.get("services", []):
            svc = ServiceSelection(
                service_name=svc_data.get("name", svc_data.get("service_name", "Unknown Service")),
                category=svc_data.get("category", "other"),
                rationale=svc_data.get("rationale", "Selected for this architecture"),
                alternatives=svc_data.get("alternatives", [])
            )
            
            services.append(svc)
        
        # Validate and potentially regenerate architecture diagram
        llm_diagram = arch_data.get("architecture_diagram", "")
        validated_diagram = self._validate_mermaid_diagram(llm_diagram, services)
        
        # Create output with required fields
        output = ArchitectureOutput(
            target_cloud=target_cloud,
            architecture_summary=f"Architecture designed for {target_cloud}",
            architecture_diagram=validated_diagram,
            design_rationale=wa
        )
        
        output.services = services
        
        # Deployment considerations
        output.deployment_considerations = arch_data.get("deployment_considerations", {})
        
        # Trade-offs
        output.trade_offs = arch_data.get("trade_offs", [])
        
        # Technology stack - convert dict to flat list if needed
        tech_stack = arch_data.get("technology_stack", [])
        if isinstance(tech_stack, dict):
            # Flatten nested structure: {'backend': ['Python'], 'frontend': ['React']} → ['Python', 'React']
            flat_list = []
            for category_techs in tech_stack.values():
                if isinstance(category_techs, list):
                    flat_list.extend(category_techs)
                else:
                    flat_list.append(str(category_techs))
            output.technology_stack = flat_list
        elif isinstance(tech_stack, list):
            output.technology_stack = tech_stack
        else:
            output.technology_stack = []
        
        # Citations
        citations = []
        for cit_data in arch_data.get("citations", []):
            cit = Citation(
                title=cit_data.get("title", ""),
                url=cit_data.get("url", ""),
                source=cit_data.get("source", "web_search"),
                relevance=cit_data.get("relevance", "")
            )
            citations.append(cit)
        
        output.citations = citations
        
        return output
    
    def _get_default_region(self, cloud_platform: CloudPlatform) -> str:
        """
        Get default region for a cloud platform.
        
        Args:
            cloud_platform: Target cloud platform
            
        Returns:
            Default region string
        """
        defaults = {
            CloudPlatform.AWS: "us-east-1",
            CloudPlatform.AZURE: "eastus",
            CloudPlatform.GCP: "us-central1",
            CloudPlatform.ORACLE: "us-ashburn-1"
        }
        return defaults.get(cloud_platform, "us-east-1")
    
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
    
    def _validate_mermaid_diagram(
        self, llm_diagram: str, services: List[ServiceSelection]
    ) -> str:
        """
        Validate LLM-generated Mermaid diagram and fix/regenerate if invalid.
        
        Args:
            llm_diagram: Diagram from LLM
            services: List of services
            
        Returns:
            Valid Mermaid diagram string
        """
        if not llm_diagram or not llm_diagram.strip():
            self.logger.warning("Empty diagram from LLM, generating Python fallback")
            # Use the requirements from context if available
            return self._generate_simple_diagram(services)
        
        # Strip markdown code fence
        diagram_code = llm_diagram.strip()
        if diagram_code.startswith("```mermaid"):
            diagram_code = diagram_code.replace("```mermaid\n", "").replace("\n```", "")
        elif diagram_code.startswith("```"):
            diagram_code = diagram_code.replace("```\n", "").replace("\n```", "")
        
        # Check for common syntax errors
        has_errors = False
        
        # Check 1: Unclosed brackets
        for line in diagram_code.split('\n'):
            open_brackets = line.count('[')
            close_brackets = line.count(']')
            if open_brackets > close_brackets:
                self.logger.warning(f"Found unclosed bracket in line: {line[:50]}")
                has_errors = True
                break
        
        # Check 2: Missing newlines (concatenated statements)
        if '][' in diagram_code and ']\n' not in diagram_code.replace('][', ']\n['):
            self.logger.warning("Found concatenated statements without newlines")
            has_errors = True
        
        # Check 3: Must start with graph declaration
        if not diagram_code.startswith('graph '):
            self.logger.warning("Missing graph declaration")
            has_errors = True
        
        if has_errors:
            self.logger.warning("LLM diagram has syntax errors, using Python fallback")
            return self._generate_simple_diagram(services)
        
        # Return validated diagram with code fence
        return f"```mermaid\n{diagram_code}\n```"
    
    def _generate_simple_diagram(self, services: List[ServiceSelection]) -> str:
        """
        Generate simple, guaranteed-valid Mermaid diagram.
        
        Args:
            services: List of services
            
        Returns:
            Mermaid diagram string with code fence
        """
        diagram = "graph TD\n"
        diagram += "    Users[Users/Clients]\n"
        
        # Create nodes for each service
        for i, svc in enumerate(services[:8]):  # Limit to 8 services for clarity
            node_id = f"S{i+1}"
            # Escape special characters in service names
            safe_name = svc.service_name.replace('"', "'")
            diagram += f'    {node_id}["{safe_name}"]\n'
        
        # Create connections (simple linear flow)
        diagram += "    Users --> S1\n"
        for i in range(1, min(len(services), 8)):
            diagram += f"    S{i} --> S{i+1}\n"
        
        return f"```mermaid\n{diagram}```"
    
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
    
    async def process_from_knowledge_graph(self, kg: 'KnowledgeGraph') -> ArchitectureOutput:
        """
        Generate architecture from a completed Knowledge Graph.
        
        This method bridges the new Knowledge Graph system with the existing
        Architecture Agent. It converts the KG to RequirementsOutput format
        and then calls the existing process() method.
        
        Args:
            kg: Completed KnowledgeGraph from orchestrator
            
        Returns:
            ArchitectureOutput
            
        Raises:
            ValueError: If knowledge graph is not ready for design
        """
        from src.models.knowledge_graph import KnowledgeGraph
        
        if not kg.status.ready_for_design:
            raise ValueError(
                "Knowledge graph is not ready for architecture design. "
                f"Critical gaps remaining: {len(kg.status.critical_gaps)}. "
                f"Unresolved conflicts: {len(kg.status.conflicts)}"
            )
        
        self.logger.info("Converting Knowledge Graph to RequirementsOutput format")
        
        # Convert KnowledgeGraph to RequirementsOutput
        requirements = self._convert_kg_to_requirements(kg)
        
        # Build architecture input
        arch_input = ArchitectureInput(
            requirements=requirements,
            target_cloud=kg.context.cloud_provider,
            region=kg.networking_connectivity.regions_in_scope[0] if kg.networking_connectivity.regions_in_scope else None
        )
        
        # Call existing architecture generation logic
        return await self.process(arch_input.dict())
    
    def _convert_kg_to_requirements(self, kg: 'KnowledgeGraph') -> RequirementsOutput:
        """
        Convert KnowledgeGraph to RequirementsOutput format.
        
        Maps knowledge graph domains to the existing requirements schema
        that the architecture agent expects.
        
        Args:
            kg: Knowledge graph with all domains populated
            
        Returns:
            RequirementsOutput compatible with existing architecture logic
        """
        from src.models.knowledge_graph import KnowledgeGraph, Intent, WorkloadType
        
        # Build functional requirements from context and domains
        functional_reqs = [kg.context.business_description]
        
        # Add runtime requirements
        if kg.runtime_platform.target_runtime:
            functional_reqs.append(
                f"Deploy using {kg.runtime_platform.target_runtime}"
            )
        if kg.runtime_platform.containerized:
            functional_reqs.append("Application is containerized")
        
        # Add networking requirements
        if kg.networking_connectivity.exposure:
            functional_reqs.append(
                f"Application requires {kg.networking_connectivity.exposure} exposure"
            )
        if kg.networking_connectivity.private_link_required:
            functional_reqs.append("Requires private connectivity (Private Link)")
        
        # Add data requirements
        if kg.data_persistence.primary_db_engine:
            functional_reqs.append(
                f"Database: {kg.data_persistence.primary_db_engine}"
            )
        if kg.data_persistence.pii_sensitivity:
            functional_reqs.append(
                f"Handles {kg.data_persistence.pii_sensitivity} data"
            )
        
        # Helper: Extract numeric user count from auth_users (can be string like "100-500 employees")
        def extract_user_count(auth_users_value) -> int:
            """Extract numeric user count from string or return default."""
            if not auth_users_value:
                return 1000  # Default
            
            if isinstance(auth_users_value, int):
                return auth_users_value
            
            # Parse string like "100-500 employees" or "< 100"
            import re
            if isinstance(auth_users_value, str):
                # Extract first number found
                numbers = re.findall(r'\d+', auth_users_value)
                if numbers:
                    return int(numbers[0])  # Use first number (conservative estimate)
            
            return 1000  # Fallback
        
        target_users = extract_user_count(kg.identity_access.auth_users)
        
        # Build non-functional requirements
        nfr = NonFunctionalRequirements(
            scalability={
                "target_users": target_users,
                "concurrent_users": int(target_users * 0.1),
            },
            performance={
                "latency_requirement": "low" if kg.resiliency_dr.rto_minutes and kg.resiliency_dr.rto_minutes < 60 else "moderate"
            },
            availability={
                "target_uptime": "99.9%" if kg.resiliency_dr.multi_region else "99%",
                "multi_region": kg.resiliency_dr.multi_region,
                "rto_minutes": kg.resiliency_dr.rto_minutes,
                "rpo_minutes": kg.resiliency_dr.rpo_minutes,
            },
            security={
                "authentication": kg.identity_access.existing_tenant or "Azure AD",
                "authorization": "RBAC",
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "mfa_required": kg.identity_access.mfa_policy == "required",
            },
            compliance=kg.security_governance.compliance_frameworks,
        )
        
        # Build technical constraints
        # Budget as dict: {"monthly": amount, "currency": "USD"}
        budget_dict = None
        if kg.context.intent == Intent.NEW_DEPLOYMENT:
            budget_dict = {"monthly": 5000, "currency": "USD", "note": "POC budget"}
        else:
            budget_dict = {"monthly": 20000, "currency": "USD", "note": "Production budget"}
        
        # Existing infrastructure as list
        infra_description = self._describe_existing_infra(kg)
        existing_infra_list = [infra_description] if infra_description else []
        
        constraints = TechnicalConstraints(
            budget=budget_dict,
            timeline="8-10 weeks for POC",
            team_skills=self._infer_team_skills(kg),
            existing_infrastructure=existing_infra_list,
        )
        
        # Build implied requirements
        implied_reqs = []
        
        # From identity domain
        if kg.identity_access.auth_users and "external_customers" in kg.identity_access.auth_users.lower():
            implied_reqs.append("Requires Azure AD B2C for customer authentication")
        
        # From runtime domain
        if kg.runtime_platform.aks_cni:
            implied_reqs.append(f"AKS requires {kg.runtime_platform.aks_cni} CNI (irreversible decision)")
        
        # From networking domain
        if kg.networking_connectivity.topology:
            implied_reqs.append(f"Network topology: {kg.networking_connectivity.topology}")
        
        # From resiliency domain
        if kg.resiliency_dr.ha_model:
            implied_reqs.append(f"High availability model: {kg.resiliency_dr.ha_model}")
        
        # From security domain
        if kg.security_governance.secrets_management:
            implied_reqs.append(f"Secrets management: {kg.security_governance.secrets_management}")
        
        # Create RequirementsOutput
        requirements = RequirementsOutput(
            target_cloud=kg.context.cloud_provider,
            region=kg.networking_connectivity.regions_in_scope[0] if kg.networking_connectivity.regions_in_scope else None,
            industry_vertical=IndustryVertical.GENERAL,
            functional_requirements=functional_reqs,
            non_functional_requirements=nfr,
            technical_constraints=constraints,
            implied_requirements=implied_reqs,
            confidence_score=self._calculate_overall_confidence(kg),
            extraction_method="knowledge-graph",
            current_understanding=self._generate_understanding_summary(kg),
            decisions_made=self._extract_key_decisions(kg),
        )
        
        return requirements
    
    def _infer_team_skills(self, kg: 'KnowledgeGraph') -> List[str]:
        """Infer team skills from knowledge graph choices."""
        skills = []
        
        # From runtime choices
        if kg.runtime_platform.target_runtime:
            runtime = kg.runtime_platform.target_runtime.lower()
            if "aks" in runtime or "kubernetes" in runtime:
                skills.append("Kubernetes")
            if "app service" in runtime:
                skills.append(".NET or Node.js")
            if "functions" in runtime:
                skills.append("Serverless")
        
        # From database choices
        if kg.data_persistence.primary_db_engine:
            db = kg.data_persistence.primary_db_engine.lower()
            if "sql" in db:
                skills.append("SQL Server")
            if "postgres" in db:
                skills.append("PostgreSQL")
            if "cosmos" in db:
                skills.append("NoSQL")
        
        return skills if skills else ["General cloud experience"]
    
    def _describe_existing_infra(self, kg: 'KnowledgeGraph') -> str:
        """Describe existing infrastructure from knowledge graph."""
        if kg.context.intent.value == "new_deployment":
            return "Greenfield - no existing infrastructure"
        
        parts = []
        if kg.existing_environment.azure_tenant_id:
            parts.append(f"Existing Azure tenant: {kg.existing_environment.azure_tenant_id}")
        if kg.existing_environment.onprem_systems:
            parts.append(f"On-premises systems: {', '.join(kg.existing_environment.onprem_systems)}")
        if kg.existing_environment.existing_cloud_resources:
            parts.append("Existing cloud resources present")
        
        return "; ".join(parts) if parts else "Brownfield - extending existing infrastructure"
    
    def _calculate_overall_confidence(self, kg: 'KnowledgeGraph') -> float:
        """Calculate overall confidence from domain confidence scores."""
        domain_confidences = [
            kg.identity_access.confidence,
            kg.runtime_platform.confidence,
            kg.networking_connectivity.confidence,
            kg.data_persistence.confidence,
            kg.resiliency_dr.confidence,
            kg.security_governance.confidence,
        ]
        
        # Filter out None values and calculate average
        valid_scores = [c for c in domain_confidences if c is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0.5
    
    def _generate_understanding_summary(self, kg: 'KnowledgeGraph') -> str:
        """Generate a summary of current understanding from knowledge graph."""
        summary_parts = [
            f"Intent: {kg.context.intent.value}",
            f"Target cloud: {kg.context.cloud_provider.value}",
            f"Workload type: {kg.context.workload_type.value}",
        ]
        
        if kg.runtime_platform.target_runtime:
            summary_parts.append(f"Runtime: {kg.runtime_platform.target_runtime}")
        
        if kg.data_persistence.primary_db_engine:
            summary_parts.append(f"Database: {kg.data_persistence.primary_db_engine}")
        
        if kg.resiliency_dr.multi_region:
            summary_parts.append("Multi-region deployment required")
        
        if kg.security_governance.compliance_frameworks:
            summary_parts.append(f"Compliance: {', '.join(kg.security_governance.compliance_frameworks)}")
        
        return ". ".join(summary_parts) + "."
    
    def _extract_key_decisions(self, kg: 'KnowledgeGraph') -> List[str]:
        """Extract key decisions made during requirements gathering."""
        decisions = []
        
        # Runtime decisions
        if kg.runtime_platform.aks_cni:
            decisions.append(f"IRREVERSIBLE: AKS CNI set to {kg.runtime_platform.aks_cni}")
        
        # Networking decisions
        if kg.networking_connectivity.topology:
            decisions.append(f"Network topology: {kg.networking_connectivity.topology}")
        
        # Data decisions
        if kg.data_persistence.primary_db_engine:
            decisions.append(f"Primary database: {kg.data_persistence.primary_db_engine}")
        
        # Resiliency decisions
        if kg.resiliency_dr.multi_region:
            decisions.append(f"Multi-region deployment with {kg.resiliency_dr.ha_model}")
        
        # Security decisions
        if kg.identity_access.mfa_policy:
            decisions.append(f"MFA policy: {kg.identity_access.mfa_policy}")
        
        return decisions

