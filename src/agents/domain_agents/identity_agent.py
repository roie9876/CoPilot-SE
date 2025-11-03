"""
Identity Domain Agent - Expert in Azure AD (Entra ID) and authentication.

DOMAIN EXPERTISE:
- Azure AD (Entra ID) tenant architecture
- Internal vs external authentication (B2C, B2B, employees)
- MFA policies and Conditional Access
- Identity-driven security (Zero Trust)
- Licensing implications (Azure AD Free vs Premium P1/P2)

CRITICAL KNOWLEDGE:
1. Existing tenant vs new tenant changes EVERYTHING
   - Enterprise orgs cannot create new tenants freely
   - Existing tenant = inherit governance, RBAC, policies
   
2. Internal vs external users = different auth models
   - Internal employees: Azure AD integrated authentication
   - External partners: B2B guest access
   - External customers: Azure AD B2C (separate tenant!)
   - Public users: Consider Azure AD B2C or 3rd party (Auth0)
   
3. MFA policy impacts security AND cost
   - MFA required = Azure AD Premium P1 minimum
   - Compliance frameworks (PCI, HIPAA) typically require MFA
   
4. Identity is the new perimeter (Zero Trust)
   - Network security alone is insufficient
   - Identity-based access control is mandatory

CONFLICT DETECTION:
- Public-facing app but only internal employees can auth → Contradiction
- High compliance requirements but no MFA → Security risk
- External customers but no B2C tenant → Missing infrastructure
"""

from typing import List
from src.agents.domain_agents.base_agent import BaseDomainAgent, DomainAgentQuestion
from src.models.knowledge_graph import KnowledgeGraph, Conflict, Intent


class IdentityDomainAgent(BaseDomainAgent):
    """
    Domain agent responsible for identity and access management requirements.
    
    Focuses on:
    - Azure AD (Entra ID) tenant strategy
    - Authentication model (internal/external/B2C/B2B)
    - MFA and Conditional Access policies
    - Identity-related compliance
    """
    
    def __init__(self):
        super().__init__(domain_name="identity_access")
        
        # Define CRITICAL fields (must know before design)
        self.critical_fields = [
            "existing_tenant",    # CRITICAL: Cannot create new tenant if enterprise
            "auth_users",         # CRITICAL: Determines auth architecture
            "mfa_policy",         # CRITICAL: Security baseline + cost
        ]
        
        # Optional fields (nice to have, improve design)
        self.optional_fields = [
            "tenant_description",
            "federation_or_b2b",
            "compliance_identity_constraints",
        ]
    
    def get_missing_critical_fields(self, graph: KnowledgeGraph) -> List[str]:
        """
        Identify missing critical identity fields.
        
        Logic:
        1. existing_tenant is ALWAYS critical
        2. auth_users is ALWAYS critical (determines auth model)
        3. mfa_policy is critical UNLESS intent is "optimize_cost"
        """
        missing = []
        identity = graph.identity_access
        
        # CRITICAL: Do you have existing tenant?
        if not self._is_field_filled(identity, "existing_tenant"):
            missing.append("existing_tenant")
        
        # CRITICAL: Who authenticates?
        if not self._is_field_filled(identity, "auth_users"):
            missing.append("auth_users")
        
        # CRITICAL: MFA policy (unless just optimizing cost)
        if (not self._is_field_filled(identity, "mfa_policy") and
            graph.context.intent != Intent.OPTIMIZE_COST):
            missing.append("mfa_policy")
        
        return missing
    
    def generate_questions(
        self,
        missing_fields: List[str],
        graph: KnowledgeGraph
    ) -> List[DomainAgentQuestion]:
        """
        Generate identity-related questions for missing fields.
        
        Questions are context-aware:
        - Greenfield: Ask about new tenant creation
        - Brownfield: Ask about existing tenant constraints
        - Public app: Focus on external auth
        - Internal app: Focus on employee auth
        """
        questions = []
        identity = graph.identity_access
        
        # Question 1: Existing tenant?
        if "existing_tenant" in missing_fields:
            if graph.existing_environment.has_existing_env:
                question_text = (
                    "Do you have an existing Azure AD (Entra ID) tenant that you **must reuse** "
                    "for this deployment?"
                )
                rationale = (
                    "Since you're working with existing infrastructure, it's likely you must use "
                    "an existing corporate tenant. This impacts governance, RBAC, and identity strategy."
                )
            else:
                question_text = (
                    "Do you have an existing Azure AD (Entra ID) tenant, or should we create a new one?"
                )
                rationale = (
                    "Using an existing tenant means inheriting existing governance, policies, and RBAC. "
                    "Creating a new tenant gives full control but requires more setup."
                )
            
            questions.append({
                "question": question_text,
                "field": "existing_tenant",
                "type": "boolean",
                "options": ["Yes, use existing tenant", "No, create new tenant"],
                "critical": True,
                "rationale": rationale,
                "domain": self.domain_name
            })
        
        # Question 2: Who authenticates?
        if "auth_users" in missing_fields:
            is_public = (graph.networking_connectivity.exposure == "public_internet")
            
            if is_public:
                question_text = (
                    "Who will **authenticate** to this application? "
                    "(This determines your authentication architecture)"
                )
                options = [
                    "Internal employees only (Corporate Azure AD)",
                    "External business partners (B2B guest access)",
                    "External customers/consumers (Azure AD B2C required)",
                    "Public users - no authentication required",
                    "Mix of internal employees and external users"
                ]
            else:
                question_text = (
                    "Who will access this internal application?"
                )
                options = [
                    "Internal employees only",
                    "Internal employees + external partners (B2B)",
                    "Service-to-service only (managed identities)"
                ]
            
            questions.append({
                "question": question_text,
                "field": "auth_users",
                "type": "choice",
                "options": options,
                "critical": True,
                "rationale": (
                    "Internal employees vs external users require fundamentally different authentication models. "
                    "Azure AD B2C is a separate tenant for consumer authentication. "
                    "This choice is expensive to change later."
                ),
                "domain": self.domain_name
            })
        
        # Question 3: MFA policy?
        if "mfa_policy" in missing_fields:
            has_compliance = len(graph.security_governance.compliance_frameworks) > 0
            
            if has_compliance:
                question_text = (
                    f"Your application requires {', '.join(graph.security_governance.compliance_frameworks)} compliance. "
                    "Is **Multi-Factor Authentication (MFA)** mandatory for all users?"
                )
                rationale = (
                    f"Most compliance frameworks ({', '.join(graph.security_governance.compliance_frameworks)}) "
                    "require MFA. Enforcing MFA requires Azure AD Premium P1 licensing."
                )
            else:
                question_text = (
                    "Should **Multi-Factor Authentication (MFA)** be required for users?"
                )
                rationale = (
                    "MFA is a security best practice and required by many compliance frameworks. "
                    "However, it requires Azure AD Premium P1 ($6/user/month) and affects user experience."
                )
            
            questions.append({
                "question": question_text,
                "field": "mfa_policy",
                "type": "choice",
                "options": [
                    "Required for all users (recommended)",
                    "Optional (users can enable)",
                    "Not required (not recommended)"
                ],
                "critical": True,
                "rationale": rationale,
                "domain": self.domain_name
            })
        
        return questions
    
    def detect_conflicts(self, graph: KnowledgeGraph) -> List[Conflict]:
        """
        Detect identity-related conflicts with other domains.
        
        Common conflicts:
        1. Public app but only internal employees can auth
        2. High compliance but no MFA
        3. External customers but no B2C tenant mentioned
        4. Private app but B2C authentication (doesn't make sense)
        """
        conflicts = []
        identity = graph.identity_access
        networking = graph.networking_connectivity
        security = graph.security_governance
        
        # Conflict 1: Public app + internal employees only
        if (networking.exposure == "public_internet" and
            identity.auth_users and "internal" in identity.auth_users.lower() and
            "external" not in identity.auth_users.lower()):
            conflicts.append(Conflict(
                conflict_id="identity_network_001",
                domains_involved=["identity_access", "networking_connectivity"],
                description=(
                    "Application is exposed to the public internet, but only internal employees "
                    "can authenticate. This seems contradictory."
                ),
                question=(
                    "Should external users (partners or customers) also be able to access this application? "
                    "Or should the application be internal-only (not public-facing)?"
                ),
                severity="high"
            ))
        
        # Conflict 2: Compliance requires MFA but MFA not required
        if (len(security.compliance_frameworks) > 0 and
            identity.mfa_policy and "not_required" in identity.mfa_policy.lower()):
            conflicts.append(Conflict(
                conflict_id="identity_security_001",
                domains_involved=["identity_access", "security_governance"],
                description=(
                    f"Compliance frameworks ({', '.join(security.compliance_frameworks)}) typically "
                    f"require MFA, but MFA policy is set to '{identity.mfa_policy}'."
                ),
                question=(
                    "Should MFA be enforced to meet compliance requirements? "
                    "Note: This requires Azure AD Premium P1 licensing."
                ),
                severity="critical"
            ))
        
        # Conflict 3: External customers but might need B2C
        if (identity.auth_users and "customer" in identity.auth_users.lower() and
            not identity.existing_tenant):
            conflicts.append(Conflict(
                conflict_id="identity_b2c_001",
                domains_involved=["identity_access"],
                description=(
                    "External customers typically require Azure AD B2C (a separate consumer identity tenant). "
                    "This is different from your corporate Azure AD."
                ),
                question=(
                    "Are you planning to use Azure AD B2C for customer authentication, "
                    "or integrate with a 3rd party identity provider (Auth0, Okta, etc.)?"
                ),
                severity="high"
            ))
        
        # Conflict 4: Private app but external customers
        if (networking.exposure == "private_only" and
            identity.auth_users and "customer" in identity.auth_users.lower()):
            conflicts.append(Conflict(
                conflict_id="identity_network_002",
                domains_involved=["identity_access", "networking_connectivity"],
                description=(
                    "Application is private-only (no public access), but authentication is for "
                    "external customers. Customers typically cannot access private networks."
                ),
                question=(
                    "Should the application be public-facing to allow customer access? "
                    "Or are these B2B partners with VPN/private connectivity?"
                ),
                severity="high"
            ))
        
        return conflicts
    
    def is_relevant_for_intent(self, graph: KnowledgeGraph) -> bool:
        """
        Identity is relevant for ALL intents except pure cost optimization.
        
        - New deployment: CRITICAL (need tenant strategy)
        - Extend existing: CRITICAL (must understand existing identity)
        - DR only: MEDIUM (identity failover less critical)
        - Migration: CRITICAL (identity migration is complex)
        - Optimize cost: LOW (focus elsewhere)
        """
        intent = graph.context.intent
        
        # Identity is less relevant for cost optimization
        if intent == Intent.OPTIMIZE_COST:
            return False
        
        # Highly relevant for everything else
        return True
