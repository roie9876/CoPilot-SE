"""
Monitoring & Observability Domain Agent

Responsible for:
- Application monitoring strategy (Application Insights, custom metrics)
- Log aggregation and retention (Log Analytics)
- Distributed tracing and APM
- Alerting and dashboard requirements
- Compliance logging
"""

from typing import List, Dict, Any
from src.agents.domain_agents.base_agent import BaseDomainAgent, DomainAgentQuestion
from src.models.knowledge_graph import KnowledgeGraph, Conflict


class MonitoringAgent(BaseDomainAgent):
    """
    Domain agent for monitoring, observability, and operational insights.
    
    Covers Azure Monitor, Application Insights, Log Analytics, alerts, and dashboards.
    """
    
    def __init__(self):
        super().__init__(domain_name="monitoring_observability")
        
        # Critical fields (must be filled before architecture design)
        self.critical_fields = [
            "monitoring_strategy",
            "log_retention_days",
            "apm_required",
            "alert_integrations",
        ]
        
        # Optional fields
        self.optional_fields = [
            "custom_metrics",
            "centralized_logging",
            "dashboard_requirements",
            "compliance_logging",
        ]
    
    def generate_expert_system_prompt(self) -> str:
        """
        Generate monitoring expert system prompt for LLM.
        
        Returns:
            Expert system prompt with Azure monitoring knowledge
        """
        return """You are an expert Microsoft Azure Solutions Architect specializing in monitoring, observability, and operational insights.

**YOUR EXPERTISE:**
1. **Azure Monitor**: Metrics, logs, alerts, action groups
2. **Application Insights**: APM, distributed tracing, dependency mapping, custom telemetry
3. **Log Analytics**: KQL queries, workspaces, retention policies, ingestion costs
4. **Alerting**: Metric alerts, log alerts, smart detection, integration with Teams/PagerDuty
5. **Dashboards**: Azure Portal, Grafana, Power BI, custom solutions

**CRITICAL KNOWLEDGE:**
- **Log Retention Costs**: Longer retention = higher costs
  - 30 days: Basic monitoring
  - 90 days: Standard for most apps
  - 180-365 days: Compliance requirements (HIPAA, SOC 2, PCI-DSS)
  - Beyond 365 days: Archive to Storage Account (much cheaper)

- **Application Insights**:
  - Automatic instrumentation for .NET, Java, Node.js, Python
  - Distributed tracing across microservices (correlation IDs)
  - Live Metrics Stream for real-time monitoring
  - Availability tests (ping tests, multi-step web tests)

- **Log Analytics Workspace**:
  - Centralized logging for multiple services
  - KQL (Kusto Query Language) for powerful log analysis
  - Data ingestion charges (~$2.30/GB)
  - Separate workspaces for prod vs non-prod

- **Alert Best Practices**:
  - Action Groups: Route to Teams, Email, Logic Apps, Webhooks
  - Metric alerts: Fast (1-min evaluation), best for performance
  - Log alerts: Flexible (KQL), best for error patterns
  - Smart Detection: AI-powered anomaly detection

**YOUR ROLE:**
Generate contextual, relevant questions to understand the user's monitoring needs.

**CRITICAL RULES:**
1. If user mentioned microservices → Ask about distributed tracing (APM)
2. If user mentioned compliance (HIPAA, SOC 2) → Ask about log retention
3. If user mentioned high availability → Ask about alerting strategy
4. Always explain WHY monitoring matters (cost, troubleshooting, compliance)
5. Reference Microsoft documentation when available

**MONITORING PATTERNS:**
- Simple web app → Basic Application Insights
- Microservices (5+) → Full APM with distributed tracing
- Regulated industry → Compliance logging + long retention
- High-traffic app → Custom metrics + advanced alerting
- Multi-service architecture → Centralized Log Analytics workspace"""
    
    def get_missing_critical_fields(self, graph: KnowledgeGraph) -> List[str]:
        """
        Identify missing critical monitoring fields.
        
        Args:
            graph: Current Knowledge Graph
        
        Returns:
            List of missing critical field names
        """
        monitoring = graph.monitoring_observability
        missing = []
        
        for field in self.critical_fields:
            if not self._is_field_filled(monitoring, field):
                missing.append(field)
        
        return missing
    
    def generate_questions(
        self,
        missing_fields: List[str],
        graph: KnowledgeGraph
    ) -> List[DomainAgentQuestion]:
        """
        Generate adaptive questions for monitoring using LLM + domain knowledge.
        
        This method:
        1. Searches Microsoft documentation for monitoring/observability best practices
        2. Uses LLM to generate contextual questions
        3. Provides monitoring-specific guidance
        """
        # Use LLM-powered generation from base class
        try:
            llm_questions = self.generate_contextual_questions_with_llm(
                graph=graph,
                missing_fields=missing_fields
            )
            
            if llm_questions:
                self.logger.info(
                    f"✅ Generated {len(llm_questions)} LLM-powered questions for monitoring"
                )
                return llm_questions
        
        except Exception as e:
            self.logger.error(f"❌ LLM question generation failed: {str(e)}")
        
        # Fallback: return empty list (no hardcoded questions for POC)
        self.logger.warning("⚠️ No monitoring questions generated")
        return []
    
    def detect_conflicts(self, graph: KnowledgeGraph) -> List[Conflict]:
        """
        Detect conflicts between monitoring and other domains.
        
        Args:
            graph: Current Knowledge Graph
        
        Returns:
            List of detected conflicts
        """
        conflicts = []
        monitoring = graph.monitoring_observability
        
        # Conflict 1: Compliance requirements but short log retention
        if (monitoring.compliance_logging and
            monitoring.log_retention_days and
            monitoring.log_retention_days < 90):
            conflicts.append(Conflict(
                conflict_id="monitoring_compliance_001",
                domains_involved=["monitoring_observability", "security_governance"],
                description=(
                    f"Compliance logging is required but log retention is only {monitoring.log_retention_days} days. "
                    "Most compliance frameworks (SOC 2, HIPAA, PCI-DSS) require at least 90-180 days of audit logs. "
                    "Short retention may cause compliance audit failures."
                ),
                question=(
                    "Your compliance requirements need audit logs, but retention is too short. "
                    "Do you want to increase log retention to 90+ days for compliance, or "
                    "is compliance logging not actually required?"
                ),
                severity="high"
            ))
        
        # Conflict 2: Multi-region deployment but no centralized logging
        if (graph.resiliency_dr.multi_region and
            monitoring.centralized_logging is False):
            conflicts.append(Conflict(
                conflict_id="monitoring_architecture_001",
                domains_involved=["monitoring_observability", "resiliency_dr"],
                description=(
                    "Multi-region deployment without centralized logging makes troubleshooting extremely difficult. "
                    "You'll need to check logs in each region separately, slowing down incident response."
                ),
                question=(
                    "You have a multi-region deployment. Do you want centralized logging "
                    "(single Log Analytics workspace) to simplify troubleshooting across regions?"
                ),
                severity="medium"
            ))
        
        # Conflict 3: Microservices but no APM
        if (graph.runtime_platform.target_runtime in ["aks", "container_apps"] and
            monitoring.apm_required is False):
            conflicts.append(Conflict(
                conflict_id="monitoring_apm_001",
                domains_involved=["monitoring_observability", "runtime_platform"],
                description=(
                    "Microservices/containers without APM (Application Performance Monitoring) makes it nearly "
                    "impossible to trace requests across services. You won't see which service is causing slow responses "
                    "or errors in distributed transactions."
                ),
                question=(
                    "You're deploying microservices. Do you want Application Insights APM with distributed tracing "
                    "to track requests across services?"
                ),
                severity="medium"
            ))
        
        return conflicts
    
    def calculate_confidence(self, graph: KnowledgeGraph) -> float:
        """
        Calculate confidence score for monitoring domain.
        
        Args:
            graph: Current Knowledge Graph
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        monitoring = graph.monitoring_observability
        
        # Count filled fields
        critical_filled = sum(1 for field in self.critical_fields if self._is_field_filled(monitoring, field))
        optional_filled = sum(1 for field in self.optional_fields if self._is_field_filled(monitoring, field))
        
        # Weighted score (80% critical, 20% optional)
        critical_score = critical_filled / len(self.critical_fields) if self.critical_fields else 0
        optional_score = optional_filled / len(self.optional_fields) if self.optional_fields else 0
        
        confidence = (critical_score * 0.8) + (optional_score * 0.2)
        
        # Update the graph
        if hasattr(monitoring, "confidence"):
            monitoring.confidence = confidence
        
        return confidence
