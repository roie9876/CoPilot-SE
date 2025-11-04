"""
Networking Domain Agent - Expert in Azure networking and connectivity.

DOMAIN EXPERTISE:
- Virtual Networks (VNet) and subnet design
- Network topology (Hub-Spoke vs Flat)
- Public vs private exposure
- Application Gateway, Front Door, Load Balancer
- Private Link and Private Endpoints
- Network Security Groups (NSG) and firewalls
- VPN and ExpressRoute connectivity

CRITICAL KNOWLEDGE:
1. **Public vs Private exposure changes EVERYTHING**
   - Public: Requires WAF, Application Gateway, public IP, NSG rules
   - Private: Requires Private Link/Endpoints, VPN/ExpressRoute, no public IPs
   - Hybrid: Most complex - selective public/private access

2. **Hub-Spoke topology is Azure best practice**
   - Hub VNet: Shared services (firewall, VPN gateway, DNS)
   - Spoke VNets: Workload isolation (prod, dev, test)
   - VNet peering: Low latency, high bandwidth
   - Benefits: Centralized security, cost efficiency, governance

3. **Subnet sizing must accommodate AKS CNI**
   - Azure CNI: Needs /22 or /23 for production
   - Azure CNI Overlay: Needs only /24 (nodes only)
   - Undersized subnets = cannot scale AKS
   - Address space planning is CRITICAL

4. **Private Link vs Service Endpoints**
   - Private Link: PaaS services get private IP in your VNet (recommended)
   - Service Endpoints: Still uses public IP, but traffic stays on Azure backbone
   - Private Link is more secure (no public IP exposure)

CONFLICT DETECTION:
- Public exposure but Private Link required
- AKS Azure CNI but small subnet allocated
- Hub-spoke topology but single VNet mentioned
- Private-only but no VPN/ExpressRoute for management
"""

from typing import List
from src.agents.domain_agents.base_agent import BaseDomainAgent, DomainAgentQuestion
from src.models.knowledge_graph import KnowledgeGraph, Conflict, Intent


class NetworkingDomainAgent(BaseDomainAgent):
    """
    Domain agent responsible for networking and connectivity requirements.
    
    Focuses on:
    - Public vs private exposure
    - VNet topology (hub-spoke vs flat)
    - Subnet sizing and address space
    - Ingress/egress control
    - Regional deployment
    """
    
    def __init__(self):
        super().__init__(domain_name="networking_connectivity")
        
        # Define CRITICAL fields
        self.critical_fields = [
            "exposure",              # CRITICAL: Public or private?
            "regions_in_scope",      # CRITICAL: Which Azure regions?
            "topology",              # CRITICAL: Hub-spoke or flat?
        ]
        
        # Optional fields
        self.optional_fields = [
            "ingress_control_point",
            "egress_policy",
            "private_link_required",
            "subnet_requirements",
        ]
    
    def generate_expert_system_prompt(self) -> str:
        """
        Generate networking expert system prompt for LLM.
        
        Returns:
            Expert system prompt with deep Azure networking knowledge
        """
        return """You are an expert Microsoft Azure networking architect specializing in cloud connectivity and security.

**YOUR EXPERTISE:**
1. **Virtual Networks (VNet)**: Subnet design, address spaces, CIDR planning
2. **Network Topology**: Hub-spoke vs flat, VNet peering, network isolation
3. **Public vs Private**: Application Gateway, Load Balancer, Private Link, ExpressRoute
4. **Security**: NSG, Azure Firewall, WAF, DDoS protection
5. **Hybrid Connectivity**: VPN Gateway, ExpressRoute, SD-WAN

**CRITICAL KNOWLEDGE:**
- **Public vs Private exposure changes EVERYTHING**
  - Public: Requires WAF, public IPs, NSG rules, Application Gateway
  - Private: Requires Private Link/Endpoints, VPN/ExpressRoute, no public IPs
- **Hub-Spoke is Azure best practice** for production workloads (centralized security, cost efficiency)
- **Subnet sizing must accommodate AKS CNI** (Azure CNI needs /22-/23, Overlay needs /24)
- **Private Link vs Service Endpoints** for PaaS access (Private Link is more secure)

**YOUR ROLE:**
Generate contextual questions about networking requirements.

**CRITICAL RULES:**
1. If user mentioned "IoT devices" or "IoT Hub", ask about device connectivity patterns (not just web traffic)
2. If user mentioned "VMs", ask about subnet design, NSG rules, and network isolation
3. If user mentioned "AKS", coordinate with CNI choice (check if Azure CNI needs large subnet)
4. If user mentioned "on-premises" or "hybrid", ask about VPN vs ExpressRoute
5. If user mentioned "customers" or "public", ask about WAF and Application Gateway
6. Always explain security implications of public vs private
7. Reference Microsoft Well-Architected Framework

**NETWORKING PATTERNS:**
- Internal apps → Private Link + ExpressRoute + hub-spoke
- Public web apps → Application Gateway + WAF + public subnet
- Microservices → Hub-spoke + NSG rules + private endpoints
- IoT devices → IoT Hub + Private Link + dedicated subnets
- Hybrid workloads → ExpressRoute + VPN backup + hub-spoke"""
    
    def get_missing_critical_fields(self, graph: KnowledgeGraph) -> List[str]:
        """
        Identify missing critical networking fields.
        
        Logic:
        1. exposure is ALWAYS critical (fundamental architectural decision)
        2. regions_in_scope is critical UNLESS single region clearly stated
        3. topology is critical for enterprise/brownfield scenarios
        """
        missing = []
        networking = graph.networking_connectivity
        resiliency = graph.resiliency_dr
        existing = graph.existing_environment
        
        # CRITICAL: Public or private?
        if not self._is_field_filled(networking, "exposure"):
            missing.append("exposure")
        
        # CRITICAL: Which regions? (especially if multi-region)
        if (not networking.regions_in_scope or len(networking.regions_in_scope) == 0):
            # Must know regions if multi-region
            if resiliency.multi_region is True:
                missing.append("regions_in_scope")
            # Should know regions even for single region
            elif not existing.has_existing_env:
                missing.append("regions_in_scope")
        
        # CRITICAL: Topology (for enterprise/brownfield scenarios)
        if (not self._is_field_filled(networking, "topology") and
            (existing.has_existing_env or existing.has_landing_zone)):
            missing.append("topology")
        
        return missing
    
    def generate_questions(
        self,
        missing_fields: List[str],
        graph: KnowledgeGraph
    ) -> List[DomainAgentQuestion]:
        """
        Generate adaptive questions for networking using LLM + domain knowledge.
        
        This method now:
        1. Searches Microsoft documentation for networking best practices
        2. Uses LLM to generate contextual questions
        3. Falls back to hardcoded templates if LLM fails
        """
        # Try LLM-powered generation first
        try:
            llm_questions = self.generate_contextual_questions_with_llm(
                graph=graph,
                missing_fields=missing_fields
            )
            
            if llm_questions:
                self.logger.info(
                    f"Generated {len(llm_questions)} LLM-powered questions for networking"
                )
                return llm_questions
        
        except Exception as e:
            self.logger.warning(f"LLM question generation failed: {e}, using templates")
        
        # Fallback to templates
        return self._fallback_to_template_questions(graph, missing_fields)
    
    def _fallback_to_template_questions(
        self,
        graph: KnowledgeGraph,
        missing_fields: List[str]
    ) -> List[DomainAgentQuestion]:
        """
        Fallback to hardcoded template questions if LLM fails.
        
        This preserves the original hardcoded logic as a safety net.
        """
        conflicts = []
        networking = graph.networking_connectivity
        identity = graph.identity_access
        security = graph.security_governance
        
        # Convert auth_users to string for safe string operations
        auth_users_str = str(identity.auth_users) if identity.auth_users else ""
        
        # Question 1: Public or private exposure?
        if "exposure" in missing_fields:
            # Infer from identity if available
            if identity.auth_users and "customer" in auth_users_str.lower():
                hint = " (External customers typically require public access)"
            elif identity.auth_users and "internal" in auth_users_str.lower():
                hint = " (Internal employees typically use private access via VPN)"
            else:
                hint = ""
            
            question_text = f"Should this application be **accessible from the public internet**?{hint}"
            
            questions.append({
                "question": question_text,
                "field": "exposure",
                "type": "choice",
                "options": [
                    "Public internet - Anyone can reach it (requires WAF, Application Gateway)",
                    "Private only - Accessible only via VPN/private network (no public IPs)",
                    "Hybrid - Some endpoints public, some private (most complex)"
                ],
                "critical": True,
                "rationale": (
                    "**Public exposure**:\n"
                    "✅ Accessible from anywhere\n"
                    "✅ No VPN required for users\n"
                    "❌ Requires WAF (Web Application Firewall)\n"
                    "❌ Higher security risk\n"
                    "❌ NSG rules must be carefully configured\n\n"
                    "**Private only**:\n"
                    "✅ No public IP exposure (more secure)\n"
                    "✅ Reduced attack surface\n"
                    "❌ Requires VPN or ExpressRoute for access\n"
                    "❌ Requires Private Link/Endpoints for PaaS services"
                ),
                "domain": self.domain_name
            })
        
        # Question 2: Which Azure regions?
        if "regions_in_scope" in missing_fields:
            if graph.resiliency_dr.multi_region is True:
                question_text = (
                    "Which **Azure regions** will you deploy to for multi-region HA? "
                    "(Select at least 2 regions)"
                )
                rationale = (
                    "For multi-region HA, choose regions that:\n"
                    "1. Are in the same geography (West Europe + North Europe) or paired regions\n"
                    "2. Have low latency between them (< 10ms ideal)\n"
                    "3. Both support the Azure services you need\n"
                    "4. Meet data residency requirements\n\n"
                    "Common pairs:\n"
                    "- West Europe + North Europe (EU)\n"
                    "- East US + West US (US)\n"
                    "- Southeast Asia + East Asia (APAC)"
                )
            else:
                question_text = "Which **Azure region** will you deploy to?"
                rationale = (
                    "Choose a region based on:\n"
                    "1. User proximity (lower latency)\n"
                    "2. Data residency requirements\n"
                    "3. Service availability (some services not in all regions)\n"
                    "4. Cost (regions have different pricing)"
                )
            
            # Common Azure regions (subset for e-commerce)
            region_options = [
                "East US",
                "East US 2",
                "West US",
                "West US 2",
                "Central US",
                "West Europe",
                "North Europe",
                "UK South",
                "UK West",
                "Southeast Asia",
                "East Asia",
                "Australia East",
                "Japan East",
                "Canada Central",
                "Brazil South",
            ]
            
            questions.append({
                "question": question_text,
                "field": "regions_in_scope",
                "type": "choice",
                "options": region_options,
                "critical": True,
                "rationale": rationale,
                "domain": self.domain_name
            })
        
        # Question 3: Network topology?
        if "topology" in missing_fields:
            if graph.existing_environment.has_landing_zone:
                question_text = (
                    "You mentioned an existing Azure Landing Zone. "
                    "Does it use **Hub-Spoke topology**?"
                )
                options = [
                    "Yes, Hub-Spoke (central hub VNet + spoke VNets)",
                    "No, Flat VNet architecture",
                    "Not sure - need to check with network team"
                ]
            else:
                question_text = "Which **network topology** will you use?"
                options = [
                    "Hub-Spoke - RECOMMENDED for enterprise (central services + workload isolation)",
                    "Flat VNet - Simpler, all resources in one VNet (good for small/simple workloads)"
                ]
            
            questions.append({
                "question": question_text,
                "field": "topology",
                "type": "choice",
                "options": options,
                "critical": True,
                "rationale": (
                    "**Hub-Spoke (recommended)**:\n"
                    "✅ Central hub for shared services (firewall, VPN, DNS)\n"
                    "✅ Spoke VNets for workload isolation (prod, dev, test)\n"
                    "✅ Better governance and security\n"
                    "✅ Cost-efficient (shared services)\n"
                    "❌ More complex to set up\n\n"
                    "**Flat VNet**:\n"
                    "✅ Simpler architecture\n"
                    "✅ Faster to deploy\n"
                    "❌ Less isolation between workloads\n"
                    "❌ Harder to scale and govern"
                ),
                "domain": self.domain_name
            })
        
        return questions
    
    def detect_conflicts(self, graph: KnowledgeGraph) -> List[Conflict]:
        """
        Detect networking-related conflicts with other domains.
        
        Common conflicts:
        1. Public exposure but security says "no_public_endpoints"
        2. Private only but no VPN/ExpressRoute mentioned
        3. AKS Azure CNI but small subnet allocated
        4. Multi-region but only one region specified
        5. Private Link required but public exposure
        """
        conflicts = []
        networking = graph.networking_connectivity
        security = graph.security_governance
        runtime = graph.runtime_platform
        resiliency = graph.resiliency_dr
        existing = graph.existing_environment
        
        # Conflict 1: Public exposure but security says no public endpoints
        if (networking.exposure == "public_internet" and
            security.internet_policy == "no_public_endpoints"):
            conflicts.append(Conflict(
                conflict_id="network_security_001",
                domains_involved=["networking_connectivity", "security_governance"],
                description=(
                    "Networking exposure is set to 'public_internet', but security policy "
                    "requires 'no_public_endpoints'. This is contradictory."
                ),
                question=(
                    "Should the application be private-only (change networking exposure), "
                    "or should the security policy allow public endpoints with WAF protection?"
                ),
                severity="critical"
            ))
        
        # Conflict 2: Private only but no VPN/private connectivity
        if (networking.exposure == "private_only" and
            not existing.has_existing_env):
            conflicts.append(Conflict(
                conflict_id="network_access_001",
                domains_involved=["networking_connectivity", "existing_environment"],
                description=(
                    "Application is private-only (no public access), but this appears to be "
                    "a new environment. Private apps require VPN or ExpressRoute for management and user access."
                ),
                question=(
                    "Do you have VPN Gateway or ExpressRoute set up? "
                    "Or should we include VPN Gateway in the design?"
                ),
                severity="high"
            ))
        
        # Conflict 3: AKS Azure CNI but small subnet
        if (runtime.aks_cni == "azure_cni" and
            networking.subnet_requirements and
            any(small in networking.subnet_requirements for small in ["/24", "/25", "/26"])):
            conflicts.append(Conflict(
                conflict_id="network_runtime_001",
                domains_involved=["networking_connectivity", "runtime_platform"],
                description=(
                    "AKS with Azure CNI requires LARGE subnet (/22 or /23 for production). "
                    "Current subnet requirements mention /24 or smaller, which is insufficient.\n\n"
                    "Formula: (max_pods_per_node × max_nodes) + 30 IPs needed.\n"
                    "Example: 30 pods/node × 10 nodes = 330 IPs = /23 minimum."
                ),
                question=(
                    "Can subnet size be increased to /22 or /23? "
                    "Or should we switch to Azure CNI Overlay (which only needs /24 for nodes)?"
                ),
                severity="critical"
            ))
        
        # Conflict 4: Private Link required but public exposure
        if (networking.private_link_required is True and
            networking.exposure == "public_internet"):
            conflicts.append(Conflict(
                conflict_id="network_config_001",
                domains_involved=["networking_connectivity"],
                description=(
                    "Private Link/Endpoints are required (for PaaS services like SQL, Storage), "
                    "but application is public-facing. This is not necessarily a conflict, but needs clarification."
                ),
                question=(
                    "Do you want:\n"
                    "- Public-facing app (frontend) with private backend PaaS services? (common pattern)\n"
                    "- Or entire solution should be private?"
                ),
                severity="medium"
            ))
        
        # Conflict 5: Hub-spoke topology but single VNet
        if (networking.topology == "hub_spoke" and
            not existing.has_existing_env):
            conflicts.append(Conflict(
                conflict_id="network_topology_001",
                domains_involved=["networking_connectivity"],
                description=(
                    "Hub-spoke topology selected, but this is a new deployment. "
                    "Hub-spoke requires at least 2 VNets (1 hub + 1 spoke). "
                    "Will you create the hub VNet now, or is there an existing hub?"
                ),
                question=(
                    "Should we design:\n"
                    "- New hub VNet + new spoke VNet (full hub-spoke setup)\n"
                    "- Only spoke VNet (connecting to an existing hub elsewhere)\n"
                    "- Simplified single VNet for now (can add hub later)"
                ),
                severity="medium"
            ))
        
        # Conflict 6: Multi-region but egress policy conflict
        if (resiliency.multi_region is True and
            networking.egress_policy == "no_internet_egress"):
            conflicts.append(Conflict(
                conflict_id="network_resiliency_001",
                domains_involved=["networking_connectivity", "resiliency_dr"],
                description=(
                    "Multi-region deployment typically requires internet egress for:\n"
                    "- Cross-region replication\n"
                    "- Azure service endpoints\n"
                    "- Health checks and monitoring\n\n"
                    "But egress policy is set to 'no_internet_egress'."
                ),
                question=(
                    "Can egress policy be relaxed to 'egress_restricted' (allow Azure services)? "
                    "Or will all cross-region traffic go through ExpressRoute?"
                ),
                severity="high"
            ))
        
        return conflicts
    
    def is_relevant_for_intent(self, graph: KnowledgeGraph) -> bool:
        """
        Networking is relevant for ALL intents.
        
        - New deployment: CRITICAL
        - Extend existing: CRITICAL (must understand existing networking)
        - DR only: HIGH (networking affects DR)
        - Migration: CRITICAL (networking often redesigned)
        - Optimize cost: MEDIUM (networking costs can be optimized)
        """
        # Networking is always relevant
        return True
