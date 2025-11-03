"""
Data Persistence Domain Agent - Expert in databases, storage, and data management.

DOMAIN EXPERTISE:
- Azure SQL Database (Single DB, Elastic Pool, Managed Instance)
- PostgreSQL and MySQL (Flexible Server)
- Cosmos DB (NoSQL, globally distributed)
- Blob Storage, File Storage, Table Storage
- Backup strategies and retention
- Data residency and sovereignty
- PII and sensitive data handling

CRITICAL KNOWLEDGE:
1. **SQL Database collation is IRREVERSIBLE after creation**
   - Choose collation carefully (case-sensitive vs insensitive)
   - Cannot change collation without recreating database
   - Default: SQL_Latin1_General_CP1_CI_AS (case-insensitive)

2. **Cosmos DB partition key is hard to change**
   - Partition key determines distribution and performance
   - Wrong partition key = hot partitions, poor performance
   - Can migrate data to new container but expensive

3. **Hyperscale tier in Azure SQL cannot be downgraded**
   - Once Hyperscale, always Hyperscale
   - Can't downgrade to Standard/Premium
   - Choose carefully

4. **Data residency may block multi-region replication**
   - GDPR: EU data must stay in EU
   - HIPAA: US patient data restrictions
   - Sovereign clouds: China, US Gov
   - Conflicts with multi-region HA requirements

5. **Managed PaaS vs Self-hosted trade-offs**
   - Managed: Less ops overhead, automatic backups, patching
   - Self-hosted (VM): More control, specific versions, custom config
   - Managed is recommended unless specific requirements

CONFLICT DETECTION:
- Multi-region HA but data residency says "eu_only"
- RPO=0 but database doesn't support sync replication
- PII data but no encryption requirements
- Backup expectation "none" but HIPAA compliance
"""

from typing import List
from src.agents.domain_agents.base_agent import BaseDomainAgent, DomainAgentQuestion
from src.models.knowledge_graph import KnowledgeGraph, Conflict, Intent


class DataDomainAgent(BaseDomainAgent):
    """
    Domain agent responsible for data persistence and storage requirements.
    
    Focuses on:
    - Database engine selection
    - Managed PaaS vs self-hosted
    - Backup and recovery
    - Data residency and compliance
    - PII and sensitive data handling
    """
    
    def __init__(self):
        super().__init__(domain_name="data_persistence")
        
        # Define CRITICAL fields
        self.critical_fields = [
            "primary_db_engine",        # CRITICAL: Which database?
            "managed_vs_self_hosted",   # CRITICAL: PaaS or VM?
            "data_residency",           # CRITICAL if multi-region
            "pii_sensitivity",          # CRITICAL if compliance
        ]
        
        # Optional fields
        self.optional_fields = [
            "statefulness",
            "backup_expectation",
        ]
    
    def get_missing_critical_fields(self, graph: KnowledgeGraph) -> List[str]:
        """
        Identify missing critical data persistence fields.
        
        Logic:
        1. primary_db_engine is ALWAYS critical (unless stateless)
        2. managed_vs_self_hosted is critical UNLESS engine chosen implies it
        3. data_residency is critical IF multi-region
        4. pii_sensitivity is critical IF compliance frameworks present
        """
        missing = []
        data = graph.data_persistence
        resiliency = graph.resiliency_dr
        security = graph.security_governance
        workload = graph.context.workload_type
        
        # CRITICAL: Which database? (unless stateless workload)
        if (not self._is_field_filled(data, "primary_db_engine") and
            str(workload) not in ["IOT", "BATCH_JOB"]):
            missing.append("primary_db_engine")
        
        # CRITICAL: Managed or self-hosted? (if database chosen)
        if (self._is_field_filled(data, "primary_db_engine") and
            not self._is_field_filled(data, "managed_vs_self_hosted")):
            missing.append("managed_vs_self_hosted")
        
        # CRITICAL: Data residency if multi-region
        if (resiliency.multi_region is True and
            not self._is_field_filled(data, "data_residency")):
            missing.append("data_residency")
        
        # CRITICAL: PII sensitivity if compliance
        if (len(security.compliance_frameworks) > 0 and
            data.pii_sensitivity is None):
            missing.append("pii_sensitivity")
        
        return missing
    
    def generate_questions(
        self,
        missing_fields: List[str],
        graph: KnowledgeGraph
    ) -> List[DomainAgentQuestion]:
        """
        Generate data persistence questions for missing fields.
        
        Questions adapt to:
        - Workload type (e-commerce vs analytics)
        - Compliance requirements
        - Multi-region needs
        """
        questions = []
        data = graph.data_persistence
        workload = graph.context.workload_type
        security = graph.security_governance
        
        # Question 1: Data model and requirements (leads to database choice)
        if "primary_db_engine" in missing_fields:
            question_text = (
                "What type of **data model** does your application need? "
                "(This helps us recommend the right database)"
            )
            options = [
                "Structured relational data with complex queries (tables, joins, foreign keys)",
                "Document-based data (JSON documents, flexible schema)",
                "Key-value pairs (simple lookups, caching)",
                "Time-series data (logs, metrics, IoT telemetry)",
                "File storage (images, videos, documents)",
                "Graph relationships (social networks, recommendations)"
            ]
            rationale = (
                "Your data model determines the optimal database:\n\n"
                "• **Structured relational** → Azure SQL or PostgreSQL (ACID, joins, transactions)\n"
                "• **Document/JSON** → Cosmos DB (flexible schema, horizontal scale)\n"
                "• **Key-value** → Redis Cache (in-memory, ultra-fast)\n"
                "• **Time-series** → Azure Data Explorer or Time Series Insights\n"
                "• **File storage** → Blob Storage (cost-effective, CDN-ready)\n"
                "• **Graph** → Cosmos DB Gremlin API\n\n"
                "We'll recommend the most suitable database based on your data model."
            )
            
            questions.append({
                "question": question_text,
                "field": "primary_db_engine",
                "type": "choice",
                "options": options,
                "critical": True,
                "rationale": rationale,
                "domain": self.domain_name
            })
        
        # Question 2: Scale and performance requirements
        if "scale_requirements" in missing_fields:
            question_text = (
                "What are your **database scale and performance** requirements?"
            )
            options = [
                "Small/Medium - Up to 1TB data, < 1000 concurrent connections",
                "Large - 1-10TB data, thousands of concurrent connections",
                "Very Large - > 10TB data, global distribution needed",
                "Low latency critical - Sub-10ms read latency required",
                "High write throughput - Thousands of writes/second"
            ]
            rationale = (
                "Scale requirements determine database tier and features:\n\n"
                "• **Small/Medium** → Standard managed database tiers\n"
                "• **Large** → Premium tiers, read replicas, sharding\n"
                "• **Very Large** → Cosmos DB (global distribution, elastic scale)\n"
                "• **Low latency** → Premium/Hyperscale tiers, in-memory caching\n"
                "• **High write throughput** → Partitioning, write-optimized tiers\n\n"
                "This helps us size the database and choose the right tier."
            )
            
            questions.append({
                "question": question_text,
                "field": "scale_requirements",
                "type": "choice",
                "options": options,
                "critical": True,
                "rationale": rationale,
                "domain": self.domain_name
            })
        
        # Question 3: Managed PaaS or self-hosted?
        if "managed_vs_self_hosted" in missing_fields:
            question_text = (
                "Do you have **specific version or configuration requirements** that "
                "prevent using a managed database service?"
            )
            
            questions.append({
                "question": question_text,
                "field": "managed_vs_self_hosted",
                "type": "choice",
                "options": [
                    "No - Use latest managed service (recommended, less operational overhead)",
                    "Yes - Need specific version or custom configuration (requires self-managed on VMs)"
                ],
                "critical": True,
                "rationale": (
                    "**Managed PaaS (recommended)**:\n"
                    "✅ Automatic backups and point-in-time restore\n"
                    "✅ Automatic patching and updates\n"
                    "✅ Built-in HA (zone-redundancy, geo-replication)\n"
                    "✅ Less ops overhead\n"
                    "❌ Less control over versions and configuration\n\n"
                    "**Self-hosted on VMs**:\n"
                    "✅ Full control (any version, custom config)\n"
                    "✅ Can run legacy versions\n"
                    "❌ You manage backups, patching, HA\n"
                    "❌ Higher ops overhead"
                ),
                "domain": self.domain_name
            })
        
        # Question 3: Data residency
        if "data_residency" in missing_fields:
            if len(security.compliance_frameworks) > 0:
                question_text = (
                    f"Your application has {', '.join(security.compliance_frameworks)} compliance. "
                    "Are there **data residency** requirements (data must stay in specific regions)?"
                )
            else:
                question_text = (
                    "Are there **data residency or sovereignty** requirements? "
                    "(e.g., EU data must stay in EU, US only, etc.)"
                )
            
            questions.append({
                "question": question_text,
                "field": "data_residency",
                "type": "choice",
                "options": [
                    "EU only - Data must stay in Europe (GDPR)",
                    "US only - Data must stay in United States",
                    "Specific country only (e.g., Germany, France)",
                    "Global OK - Data can be replicated worldwide",
                    "Not specified / No restrictions"
                ],
                "critical": True,
                "rationale": (
                    "Data residency affects:\n"
                    "- Multi-region replication (may not be allowed)\n"
                    "- DR strategy (failover to same-region only)\n"
                    "- Backup storage location\n"
                    "- Compliance (GDPR, HIPAA, sovereign clouds)\n\n"
                    "Example: GDPR requires EU customer data stays in EU."
                ),
                "domain": self.domain_name,
                "extra_info": {
                    "impacts": ["multi_region_feasibility", "backup_location", "dr_strategy"]
                }
            })
        
        # Question 4: PII sensitivity
        if "pii_sensitivity" in missing_fields:
            if security.compliance_frameworks:
                question_text = (
                    f"Does your application handle **PII (Personally Identifiable Information)** "
                    f"or sensitive data? (This affects {', '.join(security.compliance_frameworks)} compliance)"
                )
            else:
                question_text = (
                    "Does your application store **PII (Personally Identifiable Information)** "
                    "or sensitive data? (e.g., names, emails, SSN, credit cards)"
                )
            
            questions.append({
                "question": question_text,
                "field": "pii_sensitivity",
                "type": "boolean",
                "options": ["Yes, handles PII or sensitive data", "No PII or sensitive data"],
                "critical": True,
                "rationale": (
                    "If PII/sensitive data is present, you need:\n"
                    "✅ Encryption at rest (TDE for databases)\n"
                    "✅ Encryption in transit (TLS/SSL)\n"
                    "✅ Data masking or tokenization\n"
                    "✅ Access controls and RBAC\n"
                    "✅ Audit logging\n"
                    "✅ Backup encryption\n\n"
                    "Compliance frameworks (GDPR, HIPAA, PCI-DSS) require these controls."
                ),
                "domain": self.domain_name
            })
        
        return questions
    
    def detect_conflicts(self, graph: KnowledgeGraph) -> List[Conflict]:
        """
        Detect data persistence conflicts with other domains.
        
        Common conflicts:
        1. Multi-region but data residency prohibits replication
        2. RPO=0 but database doesn't support sync replication
        3. PII data but no encryption requirements
        4. Backup expectation "none" but compliance requires backups
        5. Cosmos DB but strong ACID consistency needed
        """
        conflicts = []
        data = graph.data_persistence
        resiliency = graph.resiliency_dr
        security = graph.security_governance
        
        # Conflict 1: Multi-region but data residency conflict
        if (resiliency.multi_region is True and
            data.data_residency and "_only" in data.data_residency.lower()):
            conflicts.append(Conflict(
                conflict_id="data_resiliency_001",
                domains_involved=["data_persistence", "resiliency_dr"],
                description=(
                    f"Multi-region deployment is required for HA, but data residency is '{data.data_residency}'. "
                    "This may prevent cross-region data replication."
                ),
                question=(
                    "Can data be replicated to another region within the same geography? "
                    "For example, EU-only data can replicate within Europe (West Europe ↔ North Europe). "
                    "Or should multi-region HA use active-passive with regional data silos?"
                ),
                severity="critical"
            ))
        
        # Conflict 2: RPO=0 but async replication only
        if (resiliency.rpo_minutes == 0 and
            data.primary_db_engine and
            data.primary_db_engine.lower() not in ["cosmos", "cosmosdb"]):
            conflicts.append(Conflict(
                conflict_id="data_resiliency_002",
                domains_involved=["data_persistence", "resiliency_dr"],
                description=(
                    f"RPO=0 (zero data loss) specified, but {data.primary_db_engine} may not support "
                    "synchronous cross-region replication cost-effectively. "
                    "Synchronous replication across regions adds significant latency."
                ),
                question=(
                    "Are you aware that RPO=0 requires synchronous replication? "
                    "This adds write latency (typically 10-50ms per transaction). "
                    "Can you accept RPO=1-5 minutes with async replication instead?"
                ),
                severity="high"
            ))
        
        # Conflict 3: PII but no encryption requirements
        if (data.pii_sensitivity is True and
            not security.encryption_requirements):
            conflicts.append(Conflict(
                conflict_id="data_security_001",
                domains_involved=["data_persistence", "security_governance"],
                description=(
                    "Application handles PII/sensitive data, but encryption requirements are not specified. "
                    "PII requires encryption at rest and in transit."
                ),
                question=(
                    "Should we enable:\n"
                    "- Transparent Data Encryption (TDE) for database encryption at rest?\n"
                    "- TLS/SSL for encryption in transit?\n"
                    "- Azure Key Vault for key management?"
                ),
                severity="critical"
            ))
        
        # Conflict 4: Compliance but no backup strategy
        if (len(security.compliance_frameworks) > 0 and
            data.backup_expectation and "none" in data.backup_expectation.lower()):
            conflicts.append(Conflict(
                conflict_id="data_compliance_001",
                domains_involved=["data_persistence", "security_governance"],
                description=(
                    f"Compliance frameworks ({', '.join(security.compliance_frameworks)}) typically require "
                    "backup and recovery capabilities, but backup expectation is set to 'none'."
                ),
                question=(
                    "Should we enable automated backups with point-in-time restore? "
                    "Most compliance frameworks require backup retention (7-90 days typical)."
                ),
                severity="critical"
            ))
        
        # Conflict 5: Cosmos DB but strong consistency + ACID needed
        if (data.primary_db_engine and "cosmos" in data.primary_db_engine.lower() and
            data.statefulness == "strongly_consistent_tx"):
            conflicts.append(Conflict(
                conflict_id="data_consistency_001",
                domains_involved=["data_persistence"],
                description=(
                    "Cosmos DB selected, but 'strongly_consistent_tx' (ACID transactions) specified. "
                    "Cosmos DB is eventually consistent by default. "
                    "Strong consistency in Cosmos DB adds latency and limits global distribution benefits."
                ),
                question=(
                    "Do you truly need ACID transactions (like SQL)? "
                    "If yes, consider Azure SQL or PostgreSQL instead. "
                    "If eventual consistency is acceptable, Cosmos DB is great for global scale."
                ),
                severity="high"
            ))
        
        # Conflict 6: Self-hosted but managed features expected
        if (data.managed_vs_self_hosted == "self_hosted" and
            data.backup_expectation == "point_in_time_restore"):
            conflicts.append(Conflict(
                conflict_id="data_hosting_001",
                domains_involved=["data_persistence"],
                description=(
                    "Database is self-hosted (on VMs), but point-in-time restore is expected. "
                    "Point-in-time restore is a managed PaaS feature. "
                    "For self-hosted, you need to configure log shipping or custom backup solution."
                ),
                question=(
                    "Should we use managed PaaS (automatic point-in-time restore)? "
                    "Or are you prepared to implement custom backup/restore for VMs?"
                ),
                severity="medium"
            ))
        
        return conflicts
    
    def is_relevant_for_intent(self, graph: KnowledgeGraph) -> bool:
        """
        Data persistence relevance depends on intent and workload.
        
        - New deployment: CRITICAL (for stateful workloads)
        - Extend existing: MEDIUM (may reuse existing databases)
        - DR only: CRITICAL (data replication is core of DR)
        - Migration: CRITICAL (data migration is complex)
        - Optimize cost: MEDIUM (database tiers can be optimized)
        """
        intent = graph.context.intent
        workload = graph.context.workload_type
        
        # Less relevant for stateless workloads
        if workload and str(workload) in ["IOT", "BATCH_JOB"]:
            return False
        
        # Critical for DR-only
        if intent == Intent.DR_ONLY:
            return True
        
        # Highly relevant for most other scenarios
        return True
