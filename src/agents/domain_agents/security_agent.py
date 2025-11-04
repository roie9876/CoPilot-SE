"""
Security & Governance Domain Agent - Expert in Cloud Security and Compliance.

DOMAIN EXPERTISE:
- Security best practices (Zero Trust, least privilege, defense in depth)
- Compliance frameworks (PCI DSS, HIPAA, ISO27001, SOC2, GDPR, FedRAMP)
- Secrets management (Azure Key Vault, AWS Secrets Manager)
- Network security (private endpoints, NSGs, firewalls, WAF)
- Encryption (TDE, at-rest, in-transit)
- Identity and access management (Azure AD, RBAC, PIM)

CRITICAL KNOWLEDGE:
1. **Compliance drives architecture**
   - PCI DSS: No public database endpoints, network segmentation, encryption
   - HIPAA: Encryption at rest/transit, audit logging, BAA with cloud provider
   - ISO27001: Information security controls, risk management
   - SOC2: Security controls, audit trails, incident response
   - GDPR: Data residency, right to be forgotten, data portability
   - FedRAMP: US government workloads, strict controls

2. **Internet Exposure Policy**
   - no_public_endpoints: All resources behind private network (highest security)
   - public_allowed_with_waf: Public endpoints but must have WAF (balanced)
   - public_ok: Public endpoints allowed (lowest security)

3. **Secrets Management**
   - Key Vault (Azure) / Secrets Manager (AWS) - REQUIRED for production
   - Never store secrets in code, config files, or environment variables
   - Managed Identity (Azure) / IAM Roles (AWS) - passwordless authentication

4. **Encryption Requirements**
   - tde_and_transit: Database TDE + HTTPS/TLS (most secure)
   - transit_only: HTTPS/TLS only
   - at_rest_only: Storage encryption only
   - ALWAYS recommend both for compliance workloads

CONFLICT DETECTION:
- Public endpoints but PCI/HIPAA compliance required
- No secrets management but production workload
- Compliance required but logging disabled
- Multi-region but GDPR data residency constraints
"""

from typing import List
from src.agents.domain_agents.base_agent import BaseDomainAgent, DomainAgentQuestion
from src.models.knowledge_graph import KnowledgeGraph, Conflict, Intent


class SecurityDomainAgent(BaseDomainAgent):
    """
    Domain agent responsible for security, compliance, and governance requirements.
    
    Focuses on:
    - Internet exposure policy (public vs private endpoints)
    - Secrets management (Key Vault, Secrets Manager)
    - Compliance frameworks (PCI, HIPAA, ISO27001, SOC2, GDPR)
    - Encryption requirements
    - Security controls and policies
    """
    
    def __init__(self):
        super().__init__(domain_name="security_governance")
        
        # Define CRITICAL fields
        self.critical_fields = [
            "internet_policy",          # CRITICAL: Are public endpoints allowed?
            "secrets_management",       # CRITICAL: How are secrets stored?
            "encryption_requirements",  # CRITICAL: What encryption is needed?
        ]
        
        # Optional fields (important but not blocking)
        self.optional_fields = [
            "compliance_frameworks",
            "logging_monitoring_required",
            "must_use_existing_controls",
        ]
    
    def generate_expert_system_prompt(self) -> str:
        """
        Generate security/compliance expert system prompt for LLM.
        
        Returns:
            Expert system prompt with deep Azure security knowledge
        """
        return """You are an expert Microsoft Azure security architect and compliance specialist.

**YOUR EXPERTISE:**
1. **Security**: Zero Trust, least privilege, defense in depth, private endpoints, NSGs, WAF
2. **Compliance**: PCI DSS, HIPAA, ISO27001, SOC2, GDPR, FedRAMP requirements
3. **Secrets Management**: Azure Key Vault, Managed Identity, passwordless authentication
4. **Encryption**: TDE (Transparent Data Encryption), encryption at rest/transit, Key Vault integration
5. **Network Security**: Private Link, Service Endpoints, NSGs, Azure Firewall, Application Gateway WAF
6. **Identity**: Azure AD, RBAC, Conditional Access, PIM (Privileged Identity Management)

**CRITICAL KNOWLEDGE:**
- **PCI DSS**: No public database endpoints, network segmentation, encryption at rest/transit, logging
- **HIPAA**: BAA with Azure, encryption (FIPS 140-2), audit trails, no public endpoints for PHI
- **ISO27001**: Security controls, risk management, incident response
- **SOC2**: Security controls documentation, audit logging
- **GDPR**: Data residency (EU data must stay in EU), right to be forgotten, consent management

**SECURITY BEST PRACTICES:**
1. **Always use Key Vault** for secrets (never env vars or config files)
2. **Managed Identity** for Azure service authentication (passwordless)
3. **Private endpoints** for databases, storage, and sensitive services
4. **WAF** for any public-facing web applications
5. **Encryption at rest AND in transit** for compliance workloads
6. **Network segmentation** with subnets and NSGs

**QUESTION GUIDELINES:**
- Ask about compliance frameworks FIRST (drives other requirements)
- If PCI/HIPAA mentioned → Require private endpoints, encryption, Key Vault
- If "public facing" → Ask about WAF and DDoS protection
- If "production" → Require secrets management (Key Vault)
- Reference Microsoft security baseline and Well-Architected Framework

**AVOID:**
- Don't ask about technologies user didn't mention
- Don't ask about compliance if user said "no compliance requirements"
- Focus on practical security, not theoretical threats

Use Bing Search to find:
- Latest compliance certification documentation
- Azure security best practices
- Key Vault pricing and SKUs
- Private Link availability for services"""

    def get_missing_critical_fields(self, graph: KnowledgeGraph) -> List[str]:
        """
        Identify missing critical security fields.
        
        Logic:
        1. internet_policy is ALWAYS critical (determines architecture)
        2. secrets_management is critical for PRODUCTION workloads
        3. encryption_requirements is critical if compliance mentioned
        """
        missing = []
        security = graph.security_governance
        
        # CRITICAL: Internet exposure policy
        if not self._is_field_filled(security, "internet_policy"):
            missing.append("internet_policy")
        
        # CRITICAL: Secrets management
        if not self._is_field_filled(security, "secrets_management"):
            missing.append("secrets_management")
        
        # CRITICAL: Encryption requirements
        if not self._is_field_filled(security, "encryption_requirements"):
            missing.append("encryption_requirements")
        
        return missing
    
    def generate_questions(
        self,
        missing_fields: List[str],
        graph: KnowledgeGraph
    ) -> List[DomainAgentQuestion]:
        """
        Generate adaptive questions for security using LLM + domain knowledge.
        
        This method:
        1. Searches Microsoft security documentation
        2. Uses LLM to generate contextual questions
        3. Provides security-specific guidance
        """
        # Use LLM-powered generation from base class
        try:
            llm_questions = self.generate_contextual_questions_with_llm(
                graph=graph,
                missing_fields=missing_fields
            )
            
            if llm_questions:
                self.logger.info(
                    f"✅ Generated {len(llm_questions)} LLM-powered questions for security"
                )
                return llm_questions
        
        except Exception as e:
            self.logger.error(f"❌ LLM question generation failed: {str(e)}")
        
        # Fallback: return empty list (no hardcoded questions for POC)
        self.logger.warning("⚠️ No security questions generated")
        return []
    
    def detect_conflicts(self, graph: KnowledgeGraph) -> List[Conflict]:
        """
        Detect conflicts between security and other domains.
        
        Args:
            graph: Current Knowledge Graph
        
        Returns:
            List of detected conflicts
        """
        conflicts = []
        security = graph.security_governance
        data = graph.data_persistence
        networking = graph.networking_connectivity
        
        # Conflict 1: Compliance frameworks require private endpoints
        if (security.compliance_frameworks and
            len(security.compliance_frameworks) > 0 and
            any(fw in ["PCI", "HIPAA", "FedRAMP"] for fw in security.compliance_frameworks) and
            security.internet_policy and "public" in security.internet_policy.lower()):
            conflicts.append(Conflict(
                conflict_id="security_compliance_001",
                domains_involved=["security_governance", "networking_connectivity"],
                description=(
                    f"Compliance frameworks {security.compliance_frameworks} require strict network controls, "
                    "but internet policy allows public endpoints. PCI DSS and HIPAA typically require private "
                    "endpoints for databases and sensitive data. FedRAMP has even stricter requirements."
                ),
                question=(
                    "Your compliance requirements may conflict with allowing public endpoints. "
                    "Should we switch to private endpoints with VPN/ExpressRoute access?"
                ),
                severity="critical"
            ))
        
        # Conflict 2: No secrets management for production workload
        workload_type_str = str(graph.context.workload_type.value) if graph.context.workload_type else ""
        if (security.secrets_management and
            security.secrets_management.lower() in ["env_vars", "config_file", "none"] and
            graph.context.workload_type and
            workload_type_str.lower() not in ["development", "testing", "poc"]):
            conflicts.append(Conflict(
                conflict_id="security_secrets_001",
                domains_involved=["security_governance"],
                description=(
                    "Production workloads should NEVER store secrets in environment variables or config files. "
                    "This is a security best practice violation. Secrets can be exposed through logs, error messages, "
                    "or source control. Azure Key Vault provides secure storage with audit logging and access controls."
                ),
                question=(
                    "This is a production workload but secrets are not using Key Vault. "
                    "Should we implement Azure Key Vault for secure secrets management?"
                ),
                severity="high"
            ))
        
        # Conflict 3: Compliance requires encryption but encryption not specified
        if (security.compliance_frameworks and
            len(security.compliance_frameworks) > 0 and
            (not security.encryption_requirements or
             security.encryption_requirements == "none")):
            conflicts.append(Conflict(
                conflict_id="security_encryption_001",
                domains_involved=["security_governance", "data_persistence"],
                description=(
                    f"Compliance frameworks {security.compliance_frameworks} require encryption at rest and in transit. "
                    "PCI DSS requires encryption for cardholder data. HIPAA requires encryption for PHI (Protected Health Information). "
                    "Without encryption, you cannot achieve compliance certification."
                ),
                question=(
                    "Compliance frameworks require encryption, but encryption requirements are not specified. "
                    "Should we enable encryption at rest (TDE) and in transit (HTTPS/TLS)?"
                ),
                severity="critical"
            ))
        
        # Conflict 4: GDPR data residency conflicts with multi-region
        if (security.compliance_frameworks and
            "GDPR" in security.compliance_frameworks and
            data.data_residency and
            data.data_residency not in ["eu_only", "single_region"]):
            conflicts.append(Conflict(
                conflict_id="security_gdpr_001",
                domains_involved=["security_governance", "data_persistence"],
                description=(
                    "GDPR requires EU citizen data to remain within the EU. Your current data residency "
                    f"setting ({data.data_residency}) may violate GDPR requirements. Multi-region replication "
                    "outside EU could result in significant fines (up to 4% of global revenue)."
                ),
                question=(
                    "GDPR compliance requires EU data residency. Should we restrict data to EU regions only "
                    "(West Europe, North Europe)?"
                ),
                severity="critical"
            ))
        
        # Conflict 5: Logging required but monitoring strategy missing
        if (security.logging_monitoring_required and
            not hasattr(graph, "monitoring_observability")):
            conflicts.append(Conflict(
                conflict_id="security_logging_001",
                domains_involved=["security_governance", "monitoring_observability"],
                description=(
                    "Security policy requires centralized logging and monitoring, but monitoring strategy "
                    "is not defined. Compliance frameworks (SOC2, ISO27001) require audit trails and security "
                    "event monitoring."
                ),
                question=(
                    "Logging and monitoring are required for security/compliance. Should we implement "
                    "Azure Monitor + Log Analytics for centralized logging?"
                ),
                severity="high"
            ))
        
        return conflicts
    
    def calculate_confidence(self, graph: KnowledgeGraph) -> float:
        """
        Calculate confidence score for security domain.
        
        Formula: 80% critical + 20% optional
        
        Args:
            graph: Knowledge Graph
        
        Returns:
            Confidence score (0.0 - 1.0)
        """
        security = graph.security_governance
        
        if not security:
            return 0.0
        
        # Count filled critical fields
        critical_filled = 0
        for field in self.critical_fields:
            if self._is_field_filled(security, field):
                critical_filled += 1
        
        # Count filled optional fields
        optional_filled = 0
        for field in self.optional_fields:
            if self._is_field_filled(security, field):
                optional_filled += 1
        
        # Weighted average (80% critical, 20% optional)
        critical_score = (critical_filled / len(self.critical_fields)) if self.critical_fields else 0.0
        optional_score = (optional_filled / len(self.optional_fields)) if self.optional_fields else 0.0
        
        confidence = (critical_score * 0.8) + (optional_score * 0.2)
        
        # Update the graph
        security.confidence = confidence
        
        return confidence
