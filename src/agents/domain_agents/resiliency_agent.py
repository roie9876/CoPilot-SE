"""
Resiliency Domain Agent - Expert in High Availability and Disaster Recovery.

DOMAIN EXPERTISE:
- Multi-region architecture patterns (active-active, active-passive)
- RTO (Recovery Time Objective) and RPO (Recovery Point Objective)
- Failover strategies (DNS-based, global load balancer, manual runbooks)
- Data replication (geo-replication, zone-redundancy)
- Cross-region networking and latency considerations

CRITICAL KNOWLEDGE:
1. **Multi-region without RTO/RPO is meaningless**
   - RTO = How quickly must service restore after regional failure?
   - RPO = How much data loss is acceptable?
   - Example: RTO=15min, RPO=5min means "restore in 15min, lose max 5min of data"

2. **Active-Active vs Active-Passive**
   - Active-Active: Both regions serve traffic simultaneously
     * Requires: Cross-region data replication, global load balancer
     * Cost: 2x compute resources running always
     * Complexity: Data consistency challenges
   - Active-Passive: Standby region activated only during failure
     * Requires: Automated failover or manual runbook
     * Cost: Lower (standby can be scaled down)
     * Simplicity: Easier data consistency

3. **Data Replication Constraints**
   - RPO=0 (zero data loss) requires synchronous replication
   - Synchronous replication across regions = HIGH LATENCY
   - Async replication = possible data loss (RPO > 0)
   - Data residency laws may prevent cross-region replication

4. **Failover Methods**
   - DNS failover: Slow (TTL = 60-300 seconds typically)
   - Global Load Balancer (Front Door, Traffic Manager): Fast (seconds)
   - Manual runbook: Slowest but most control

CONFLICT DETECTION:
- Multi-region=true but RPO/RTO not specified
- Active-active but data can't replicate cross-region
- RTO=5min but manual failover (impossible)
- Multi-region but data residency says "eu_only"
"""

from typing import List
from src.agents.domain_agents.base_agent import BaseDomainAgent, DomainAgentQuestion
from src.models.knowledge_graph import KnowledgeGraph, Conflict, Intent


class ResiliencyDomainAgent(BaseDomainAgent):
    """
    Domain agent responsible for HA/DR requirements.
    
    Focuses on:
    - Multi-region deployment requirements
    - RTO (Recovery Time Objective)
    - RPO (Recovery Point Objective)
    - Failover strategies
    - Data replication feasibility
    """
    
    def __init__(self):
        super().__init__(domain_name="resiliency_dr")
        
        # Define CRITICAL fields
        self.critical_fields = [
            "multi_region",          # CRITICAL: Is multi-region required?
            "rto_minutes",          # CRITICAL: How fast must we recover?
            "rpo_minutes",          # CRITICAL: How much data loss acceptable?
            "ha_model",             # CRITICAL: Active-active vs active-passive
        ]
        
        # Optional fields
        self.optional_fields = [
            "failover_method",
            # Note: Data residency restrictions are checked via data_persistence.data_residency
        ]
    
    def get_missing_critical_fields(self, graph: KnowledgeGraph) -> List[str]:
        """
        Identify missing critical resiliency fields.
        
        Logic:
        1. multi_region is ALWAYS critical (fundamental architectural decision)
        2. IF multi_region=true, THEN rto_minutes and rpo_minutes are CRITICAL
        3. IF multi_region=true, THEN ha_model is CRITICAL
        4. IF intent=DR_ONLY, ALL resiliency fields are CRITICAL
        """
        missing = []
        resiliency = graph.resiliency_dr
        intent = graph.context.intent
        
        # CRITICAL: Is multi-region required?
        if not self._is_field_filled(resiliency, "multi_region"):
            # For DR-only intent, multi-region is obviously true
            if intent != Intent.DR_ONLY:
                missing.append("multi_region")
        
        # If multi-region=true OR intent=DR_ONLY, need RTO/RPO
        is_multi_region = resiliency.multi_region or intent == Intent.DR_ONLY
        
        if is_multi_region:
            # CRITICAL: RTO (how fast must we recover?)
            if not self._is_field_filled(resiliency, "rto_minutes"):
                missing.append("rto_minutes")
            
            # CRITICAL: RPO (how much data loss acceptable?)
            if not self._is_field_filled(resiliency, "rpo_minutes"):
                missing.append("rpo_minutes")
            
            # CRITICAL: Active-active or active-passive?
            if not self._is_field_filled(resiliency, "ha_model"):
                missing.append("ha_model")
        
        return missing
    
    def generate_questions(
        self,
        missing_fields: List[str],
        graph: KnowledgeGraph
    ) -> List[DomainAgentQuestion]:
        """
        Generate resiliency-related questions for missing fields.
        
        Questions adapt to:
        - User's intent (new deployment vs DR-only)
        - Workload criticality
        - Regulatory constraints
        """
        questions = []
        resiliency = graph.resiliency_dr
        intent = graph.context.intent
        
        # Question 1: Business impact of regional failure
        if "multi_region" in missing_fields:
            if intent == Intent.DR_ONLY:
                # Skip - obviously multi-region if DR-only
                pass
            else:
                question_text = (
                    "What is the **business impact** if the entire Azure region becomes unavailable "
                    "(datacenter failure, natural disaster)?"
                )
                options = [
                    "Critical - Cannot afford ANY regional downtime (requires multi-region active-active)",
                    "High - Need recovery within 1 hour (requires multi-region with automated failover)",
                    "Medium - Can tolerate few hours downtime (single region with good backup strategy)",
                    "Low - Can restore from backup within 24 hours (single region sufficient)"
                ]
                rationale = (
                    "Your answer determines disaster recovery architecture:\n\n"
                    "• **Critical impact** → Multi-region active-active (both regions always serving traffic)\n"
                    "• **High impact** → Multi-region active-passive (automated failover to secondary)\n"
                    "• **Medium impact** → Single region with zone-redundancy + comprehensive backups\n"
                    "• **Low impact** → Single region, geo-redundant backups, manual recovery\n\n"
                    "Multi-region doubles compute costs but protects against regional failures."
                )
                
                questions.append({
                    "question": question_text,
                    "field": "multi_region",
                    "type": "choice",
                    "options": options,
                    "critical": True,
                    "rationale": rationale,
                    "domain": self.domain_name
                })
        
        # Question 2: RTO (Recovery Time Objective)
        if "rto_minutes" in missing_fields:
            question_text = (
                "**RTO (Recovery Time Objective)**: If an entire Azure region fails, "
                "how quickly **must** your application be restored and operational?"
            )
            
            questions.append({
                "question": question_text,
                "field": "rto_minutes",
                "type": "choice",
                "options": [
                    "< 5 minutes (requires active-active, very expensive)",
                    "5-15 minutes (requires automated failover)",
                    "15-60 minutes (automated failover with some manual steps)",
                    "1-4 hours (semi-automated runbook)",
                    "> 4 hours (manual recovery acceptable)"
                ],
                "critical": True,
                "rationale": (
                    "RTO determines your HA architecture:\n"
                    "- < 5 min: Requires active-active (both regions serve traffic always)\n"
                    "- 5-15 min: Active-passive with automated failover (Front Door health probes)\n"
                    "- 15-60 min: Warm standby with some manual intervention\n"
                    "- > 1 hour: Cold standby or manual restoration\n\n"
                    "Lower RTO = higher cost (more resources running, more automation)"
                ),
                "domain": self.domain_name,
                "extra_info": {
                    "impacts": ["ha_model", "cost", "automation_complexity"]
                }
            })
        
        # Question 3: RPO (Recovery Point Objective)
        if "rpo_minutes" in missing_fields:
            question_text = (
                "**RPO (Recovery Point Objective)**: In a regional failure, "
                "how much **data loss** is acceptable?"
            )
            
            questions.append({
                "question": question_text,
                "field": "rpo_minutes",
                "type": "choice",
                "options": [
                    "Zero (no data loss acceptable) - requires synchronous replication",
                    "< 5 minutes - requires near-real-time async replication",
                    "5-15 minutes - requires frequent async replication",
                    "15-60 minutes - periodic replication acceptable",
                    "> 1 hour - daily backups may suffice"
                ],
                "critical": True,
                "rationale": (
                    "RPO determines data replication strategy:\n"
                    "- RPO=0: Synchronous replication (high latency, expensive, complex)\n"
                    "  * Azure SQL: Zone-redundant or active geo-replication\n"
                    "  * Cosmos DB: Multi-region writes with strong consistency\n"
                    "- RPO < 5min: Async replication with continuous data sync\n"
                    "- RPO > 15min: Periodic snapshots or log shipping\n\n"
                    "Lower RPO = higher cost and complexity. "
                    "RPO=0 across regions may not be feasible due to latency."
                ),
                "domain": self.domain_name,
                "extra_info": {
                    "impacts": ["data_replication", "cost", "latency"]
                }
            })
        
        # Question 4: HA Model (Active-Active vs Active-Passive)
        if "ha_model" in missing_fields:
            # Infer recommendation based on RTO if available
            if resiliency.rto_minutes and resiliency.rto_minutes < 5:
                recommendation = " (Based on your RTO < 5 min, **active-active is required**)"
            elif resiliency.rto_minutes and resiliency.rto_minutes < 15:
                recommendation = " (Based on your RTO, **active-passive with automated failover** is recommended)"
            else:
                recommendation = ""
            
            question_text = (
                f"Which **High Availability model** do you prefer?{recommendation}"
            )
            
            questions.append({
                "question": question_text,
                "field": "ha_model",
                "type": "choice",
                "options": [
                    "Active-Active - Both regions serve traffic simultaneously (highest availability, highest cost)",
                    "Active-Passive - Primary region serves traffic, standby for failover (lower cost)",
                    "Single Region - No multi-region HA (simplest, lowest cost)"
                ],
                "critical": True,
                "rationale": (
                    "**Active-Active**:\n"
                    "✅ Zero downtime during regional failure (seamless failover)\n"
                    "✅ Load distributed across regions\n"
                    "❌ 2x compute cost (both regions always running)\n"
                    "❌ Data consistency challenges (conflict resolution)\n"
                    "❌ Requires global load balancer (Front Door, Traffic Manager)\n\n"
                    "**Active-Passive**:\n"
                    "✅ Lower cost (standby can be scaled down)\n"
                    "✅ Simpler data consistency (single active region)\n"
                    "❌ Failover takes time (5-15 minutes typical)\n"
                    "❌ Standby resources may be cold (slower failover)"
                ),
                "domain": self.domain_name
            })
        
        return questions
    
    def detect_conflicts(self, graph: KnowledgeGraph) -> List[Conflict]:
        """
        Detect resiliency-related conflicts with other domains.
        
        Common conflicts:
        1. Multi-region but RTO/RPO not specified
        2. Active-active but data can't replicate cross-region
        3. RPO=0 but async replication only
        4. RTO=5min but manual failover
        5. Multi-region but data residency prohibits replication
        """
        conflicts = []
        resiliency = graph.resiliency_dr
        data = graph.data_persistence
        networking = graph.networking_connectivity
        
        # Conflict 1: Multi-region without RTO/RPO
        if (resiliency.multi_region is True and
            (resiliency.rto_minutes is None or resiliency.rpo_minutes is None)):  # Fixed: use 'is None' instead of 'not' to handle 0 values
            conflicts.append(Conflict(
                conflict_id="resiliency_incomplete_001",
                domains_involved=["resiliency_dr"],
                description=(
                    "Multi-region deployment specified, but RTO (Recovery Time Objective) "
                    "and RPO (Recovery Point Objective) are not defined. "
                    "Multi-region without RTO/RPO targets is meaningless."
                ),
                question=(
                    "What are your RTO and RPO requirements? "
                    "RTO = How quickly must service restore? RPO = How much data loss is acceptable?"
                ),
                severity="critical"
            ))
        
        # Conflict 2: Active-active with data residency restrictions
        # Check if data residency restrictions conflict with multi-region active-active
        if (resiliency.ha_model == "active_active" and
            data.data_residency and data.data_residency != "global_ok"):
            conflicts.append(Conflict(
                conflict_id="resiliency_data_001",
                domains_involved=["resiliency_dr", "data_persistence"],
                description=(
                    f"Active-active HA model requires data replication across regions, "
                    f"but data residency is restricted to: {data.data_residency}. "
                    "This may limit or prevent cross-region replication."
                ),
                question=(
                    "Can you relax data residency requirements to allow multi-region replication? "
                    "Or should we use active-passive within a single compliant region?"
                ),
                severity="high"
            ))
        
        # Conflict 3: RPO=0 but async replication
        if (resiliency.rpo_minutes == 0 and
            data.primary_db_engine and "cosmos" not in data.primary_db_engine.lower()):
            conflicts.append(Conflict(
                conflict_id="resiliency_data_002",
                domains_involved=["resiliency_dr", "data_persistence"],
                description=(
                    "RPO=0 (zero data loss) requires synchronous replication across regions. "
                    "This is extremely expensive and may not be feasible depending on distance "
                    "between regions (latency > 10ms makes synchronous replication impractical)."
                ),
                question=(
                    "Are you aware that RPO=0 requires synchronous cross-region replication? "
                    "This adds significant latency and cost. Can you accept RPO=1-5 minutes instead?"
                ),
                severity="high"
            ))
        
        # Conflict 4: Fast RTO but manual failover
        if (resiliency.rto_minutes and resiliency.rto_minutes < 15 and
            resiliency.failover_method and "manual" in resiliency.failover_method.lower()):
            conflicts.append(Conflict(
                conflict_id="resiliency_automation_001",
                domains_involved=["resiliency_dr"],
                description=(
                    f"RTO target is {resiliency.rto_minutes} minutes (fast recovery required), "
                    "but failover method is manual. Manual failover cannot achieve RTO < 15 minutes "
                    "(requires human intervention, verification, DNS updates, etc.)."
                ),
                question=(
                    "To achieve your RTO target, automated failover is required. "
                    "Should we design for automated failover using Front Door or Traffic Manager health probes?"
                ),
                severity="high"  # Changed from critical - Architecture Agent can infer automated failover from RTO
            ))
        
        # Conflict 5: Multi-region but data residency conflicts
        if (resiliency.multi_region is True and
            data.data_residency and "_only" in data.data_residency.lower() and
            len(networking.regions_in_scope) > 1):
            conflicts.append(Conflict(
                conflict_id="resiliency_data_003",
                domains_involved=["resiliency_dr", "data_persistence", "networking_connectivity"],
                description=(
                    f"Multi-region deployment planned across {networking.regions_in_scope}, "
                    f"but data residency requirement is '{data.data_residency}'. "
                    "Architecture will ensure all regions comply with data residency (e.g., multiple US regions)."
                ),
                question=(
                    "Should we use multiple regions within the same geography (e.g., East US + West US) "
                    "to satisfy both multi-region HA and data residency requirements?"
                ),
                severity="high"  # Changed from critical - can be solved with regional pairing
            ))
        
        # Conflict 6: Multi-region but only one region specified
        if (resiliency.multi_region is True and
            len(networking.regions_in_scope) < 2):
            conflicts.append(Conflict(
                conflict_id="resiliency_network_001",
                domains_involved=["resiliency_dr", "networking_connectivity"],
                description=(
                    "Multi-region HA specified, but only one region (or no regions) defined in networking. "
                    "Multi-region requires at least 2 Azure regions. Architecture agent will suggest paired region."
                ),
                question=(
                    "Which Azure regions should be used for multi-region deployment? "
                    "Example: West Europe + North Europe, or East US + West US"
                ),
                severity="high"  # Changed from critical - arch agent can suggest paired region
            ))
        
        return conflicts
    
    def is_relevant_for_intent(self, graph: KnowledgeGraph) -> bool:
        """
        Resiliency relevance depends heavily on intent.
        
        - New deployment: MEDIUM (optional unless business-critical)
        - Extend existing: LOW (focus on extension, not HA redesign)
        - DR only: CRITICAL (this is the entire focus!)
        - Migration: MEDIUM (good time to add HA)
        - Optimize cost: LOW (HA is expensive, conflicts with cost optimization)
        """
        intent = graph.context.intent
        
        # CRITICAL for DR-only intent
        if intent == Intent.DR_ONLY:
            return True
        
        # Low relevance for cost optimization (HA increases cost)
        if intent == Intent.OPTIMIZE_COST:
            return False
        
        # Medium relevance for everything else
        return True
