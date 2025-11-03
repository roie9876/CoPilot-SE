"""
Runtime Domain Agent - Expert in Azure compute platforms and container orchestration.

DOMAIN EXPERTISE:
- Azure Kubernetes Service (AKS) - deep CNI and networking knowledge
- App Service (Web Apps, API Apps)
- Azure Functions (serverless compute)
- Virtual Machines and VM Scale Sets
- Container Instances
- Batch processing

CRITICAL KNOWLEDGE (AKS):
1. **CNI Plugin is IRREVERSIBLE** after cluster creation
   - Azure CNI: Best performance, uses VNet IPs directly
     * Requires LARGE subnet (/22 or /23 for 256+ IPs)
     * Formula: Subnet size = (max_pods_per_node × max_nodes) + 30
     * Example: 30 pods/node × 10 nodes = 300 IPs needed = /23 subnet minimum
   - Azure CNI Overlay: RECOMMENDED for most scenarios
     * Good performance + IP efficiency
     * Pods get overlay IPs, nodes use VNet IPs
     * Only nodes consume VNet IPs (not every pod)
   - Kubenet: Legacy option
     * Saves VNet IPs (pods use overlay network)
     * Adds network hop (slightly slower)
     * Requires route tables

2. **Network Policy is IRREVERSIBLE**
   - Azure Network Policy: Native, good for simple scenarios
   - Calico: Advanced features (GlobalNetworkPolicy, egress control)
   - Cilium: eBPF-based, best performance, observability

3. **Private vs Public cluster**
   - Private cluster: Control plane has no public FQDN (more secure)
   - Public cluster: Easier to manage but needs NSG rules

4. **Ingress model impacts networking**
   - Application Gateway Ingress Controller: Layer 7 LB, WAF integration
   - NGINX Ingress: Most common, flexible
   - Public Load Balancer: Layer 4, simple
   - Internal Load Balancer only: Private apps

CONFLICT DETECTION:
- Azure CNI selected but networking team allocated /24 subnet (too small)
- Private cluster but no VPN/private connectivity for management
- Public Load Balancer but networking says "private_only"
- Containerized workload but target_runtime = "vm"
"""

from typing import List
from src.agents.domain_agents.base_agent import BaseDomainAgent, DomainAgentQuestion
from src.models.knowledge_graph import KnowledgeGraph, Conflict, Intent, WorkloadType


class RuntimeDomainAgent(BaseDomainAgent):
    """
    Domain agent responsible for compute platform and runtime requirements.
    
    Focuses on:
    - Compute platform selection (AKS, App Service, Functions, VMs)
    - AKS-specific decisions (CNI, network policy, ingress)
    - Containerization strategy
    - Scaling and deployment patterns
    """
    
    def __init__(self):
        super().__init__(domain_name="runtime_platform")
        
        # Define CRITICAL fields
        self.critical_fields = [
            "target_runtime",      # CRITICAL: Which compute platform?
            "containerized",       # CRITICAL: Container-based or not?
            "aks_cni",            # CRITICAL if AKS: IRREVERSIBLE decision!
        ]
        
        # Optional fields
        self.optional_fields = [
            "is_existing_runtime",
            "os_requirements",
            "needs_gpu",
            "aks_network_policy",
            "aks_private_cluster",
            "aks_ingress_model",
            "app_service_plan_tier",
            "scaling_strategy",
            "deployment_style",
        ]
    
    def get_missing_critical_fields(self, graph: KnowledgeGraph) -> List[str]:
        """
        Identify missing critical runtime fields.
        
        Logic:
        1. target_runtime is ALWAYS critical
        2. containerized is critical UNLESS workload type is clearly non-container (batch, ML)
        3. aks_cni is critical ONLY if target_runtime = "aks"
        """
        missing = []
        runtime = graph.runtime_platform
        workload = graph.context.workload_type
        
        # CRITICAL: Which compute platform?
        if not self._is_field_filled(runtime, "target_runtime"):
            missing.append("target_runtime")
        
        # CRITICAL: Containerized? (unless clearly not container workload)
        if (not self._is_field_filled(runtime, "containerized") and
            workload not in [WorkloadType.BATCH_JOB, WorkloadType.ML_SERVICE]):
            missing.append("containerized")
        
        # CRITICAL: If AKS, MUST know CNI (irreversible!)
        if (runtime.target_runtime and "aks" in runtime.target_runtime.lower() and
            not self._is_field_filled(runtime, "aks_cni")):
            missing.append("aks_cni")
        
        return missing
    
    def generate_questions(
        self,
        missing_fields: List[str],
        graph: KnowledgeGraph
    ) -> List[DomainAgentQuestion]:
        """
        Generate runtime-related questions for missing fields.
        
        Questions adapt to:
        - Workload type (web app vs API vs microservices)
        - Brownfield vs greenfield
        - Developer experience level
        """
        questions = []
        runtime = graph.runtime_platform
        workload = graph.context.workload_type
        
        # Question 1: Application architecture pattern (leads to compute choice)
        if "target_runtime" in missing_fields:
            question_text = (
                "How is your application **architected**? "
                "(This helps us recommend the right compute platform)"
            )
            options = [
                "Single monolithic application (one deployable unit)",
                "Multiple microservices (5+ independent services)",
                "Few services (2-4 loosely coupled components)",
                "Serverless functions (event-driven, stateless)",
                "Legacy application requiring full OS control"
            ]
            rationale = (
                "Your architecture pattern determines the optimal compute platform:\n\n"
                "• **Monolithic app** → App Service (simplest, managed)\n"
                "• **Many microservices (5+)** → AKS (Kubernetes orchestration needed)\n"
                "• **Few services (2-4)** → App Service or Container Instances\n"
                "• **Event-driven/stateless** → Azure Functions (serverless)\n"
                "• **Legacy/special OS needs** → Virtual Machines\n\n"
                "We'll recommend the most suitable platform based on your answer."
            )
            
            questions.append({
                "question": question_text,
                "field": "target_runtime",
                "type": "choice",
                "options": options,
                "critical": True,
                "rationale": rationale,
                "domain": self.domain_name
            })
        
        # Question 2: Containerized?
        if "containerized" in missing_fields:
            if graph.existing_environment.has_existing_env:
                question_text = "Is your application **already containerized** (Docker images)?"
            else:
                question_text = "Will your application be **containerized** (run in Docker containers)?"
            
            questions.append({
                "question": question_text,
                "field": "containerized",
                "type": "boolean",
                "options": ["Yes, containerized", "No, not containerized"],
                "critical": True,
                "rationale": (
                    "Containerization affects platform choice. If already containerized, "
                    "AKS or App Service with containers are natural fits. If not containerized, "
                    "App Service or VMs may be simpler."
                ),
                "domain": self.domain_name
            })
        
        # Question 3: AKS CNI (CRITICAL - IRREVERSIBLE!)
        if "aks_cni" in missing_fields:
            questions.append({
                "question": (
                    "⚠️ **CRITICAL DECISION (IRREVERSIBLE)**: "
                    "Which **AKS CNI (Container Network Interface)** plugin will you use? "
                    "\n\n"
                    "⚡ This decision **cannot be changed** after cluster creation without recreating the cluster!"
                ),
                "field": "aks_cni",
                "type": "choice",
                "options": [
                    "Azure CNI Overlay - **RECOMMENDED**: Good performance + IP efficiency (GA 2024)",
                    "Azure CNI - Best performance, but requires LARGE subnet (/22 or /23 minimum)",
                    "Kubenet - Legacy option, saves IPs but adds network hop (not recommended)"
                ],
                "critical": True,
                "rationale": (
                    "**CNI choice is IRREVERSIBLE after cluster creation!**\n\n"
                    "- **Azure CNI Overlay** (recommended): Best of both worlds. Pods get overlay IPs, "
                    "only nodes consume VNet IPs. Good performance + IP efficiency.\n\n"
                    "- **Azure CNI**: Pods use VNet IPs directly (best performance). "
                    "But requires LARGE subnet: (max_pods_per_node × max_nodes) + 30 IPs. "
                    "Example: 30 pods/node × 10 nodes = 300 IPs = /23 subnet minimum.\n\n"
                    "- **Kubenet**: Legacy. Saves VNet IPs but adds network hop (slightly slower). "
                    "Requires route tables. Not recommended for new clusters."
                ),
                "domain": self.domain_name,
                "extra_info": {
                    "irreversible": True,
                    "requires_coordination_with": ["networking_connectivity"],
                    "subnet_requirements": {
                        "azure_cni": "/22 or /23 (256-512 IPs)",
                        "azure_cni_overlay": "/24 (only nodes need VNet IPs)",
                        "kubenet": "/24 (only nodes need VNet IPs)"
                    }
                }
            })
        
        return questions
    
    def detect_conflicts(self, graph: KnowledgeGraph) -> List[Conflict]:
        """
        Detect runtime-related conflicts with other domains.
        
        Common conflicts:
        1. Azure CNI selected but subnet too small
        2. Containerized=true but target_runtime=vm
        3. Private cluster but no VPN/private connectivity
        4. Public Load Balancer but networking says private_only
        """
        conflicts = []
        runtime = graph.runtime_platform
        networking = graph.networking_connectivity
        existing = graph.existing_environment
        
        # Conflict 1: Azure CNI but potentially small subnet
        if (runtime.aks_cni == "azure_cni" and
            networking.subnet_requirements and
            "/24" in networking.subnet_requirements):
            conflicts.append(Conflict(
                conflict_id="runtime_network_001",
                domains_involved=["runtime_platform", "networking_connectivity"],
                description=(
                    "Azure CNI selected, but subnet sizing notes indicate /24 (254 IPs). "
                    "Azure CNI requires LARGE subnet: (max_pods_per_node × max_nodes) + 30. "
                    "For 30 pods/node and 10 nodes, you need 330 IPs = /23 subnet minimum."
                ),
                question=(
                    "Do you have sufficient IP address space for Azure CNI? "
                    "If subnet is /24 (254 IPs), consider switching to Azure CNI Overlay instead."
                ),
                severity="critical"
            ))
        
        # Conflict 2: Containerized but target is VM
        if (runtime.containerized is True and
            runtime.target_runtime and "vm" in runtime.target_runtime.lower() and
            "vmss" not in runtime.target_runtime.lower()):
            conflicts.append(Conflict(
                conflict_id="runtime_container_001",
                domains_involved=["runtime_platform"],
                description=(
                    "Application is containerized (Docker), but target platform is Virtual Machines. "
                    "While VMs can run Docker, this loses many benefits of container orchestration."
                ),
                question=(
                    "Should we use AKS (Kubernetes) or App Service with containers instead? "
                    "These provide better orchestration, scaling, and management for containerized apps."
                ),
                severity="high"
            ))
        
        # Conflict 3: Private cluster but no existing environment
        if (runtime.aks_private_cluster is True and
            not existing.has_existing_env):
            conflicts.append(Conflict(
                conflict_id="runtime_network_002",
                domains_involved=["runtime_platform", "existing_environment"],
                description=(
                    "AKS private cluster selected (control plane has no public FQDN), "
                    "but this appears to be a new deployment. Private clusters require VPN "
                    "or Azure Bastion for management access."
                ),
                question=(
                    "Do you have VPN or private connectivity set up for managing a private AKS cluster? "
                    "Or should we use a public cluster with NSG rules for security?"
                ),
                severity="high"
            ))
        
        # Conflict 4: Public ingress but networking says private only
        if (runtime.aks_ingress_model and "public" in runtime.aks_ingress_model.lower() and
            networking.exposure == "private_only"):
            conflicts.append(Conflict(
                conflict_id="runtime_network_003",
                domains_involved=["runtime_platform", "networking_connectivity"],
                description=(
                    "AKS ingress configured as 'public_lb' but networking exposure set to 'private_only'. "
                    "This is contradictory."
                ),
                question=(
                    "Should the application be publicly accessible (change networking exposure), "
                    "or should AKS ingress be internal-only (change to internal_lb_only)?"
                ),
                severity="critical"
            ))
        
        # Conflict 5: App Service but multi-region active-active
        if (runtime.target_runtime and "app_service" in runtime.target_runtime.lower() and
            graph.resiliency_dr.ha_model == "active_active" and
            graph.resiliency_dr.multi_region is True):
            conflicts.append(Conflict(
                conflict_id="runtime_resiliency_001",
                domains_involved=["runtime_platform", "resiliency_dr"],
                description=(
                    "App Service selected with multi-region active-active HA. "
                    "App Service doesn't have built-in multi-region active-active. "
                    "You'll need Traffic Manager or Front Door for traffic distribution."
                ),
                question=(
                    "Are you aware that multi-region active-active requires Front Door or Traffic Manager "
                    "for traffic routing between App Service instances in different regions?"
                ),
                severity="medium"
            ))
        
        return conflicts
    
    def is_relevant_for_intent(self, graph: KnowledgeGraph) -> bool:
        """
        Runtime is relevant for ALL intents except pure cost/security optimization.
        
        - New deployment: CRITICAL
        - Extend existing: CRITICAL (need to understand existing runtime)
        - DR only: MEDIUM (runtime already chosen, focus on DR)
        - Migration: CRITICAL (runtime choice for migration target)
        - Optimize cost: MEDIUM (may change runtime tier/size)
        """
        intent = graph.context.intent
        
        # Runtime less critical for DR-only (already deployed)
        if intent == Intent.DR_ONLY:
            # Still somewhat relevant (DR may affect runtime config)
            return True
        
        # Highly relevant for everything else
        return True
