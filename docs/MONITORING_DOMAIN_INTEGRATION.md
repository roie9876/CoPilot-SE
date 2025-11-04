# Monitoring Domain Integration - Complete

**Date**: January 2025  
**Status**: ✅ **COMPLETE** (Backend + Frontend)

---

## Overview

Added **Monitoring & Observability** as the 7th domain in the Knowledge Graph system. This domain covers Azure Monitor, Application Insights, Log Analytics, alerting, APM, centralized logging, and compliance logging requirements.

---

## Backend Changes

### 1. Knowledge Graph Model (`src/models/knowledge_graph.py`)

**Lines 455-508**: Created `MonitoringObservability` class:
```python
class MonitoringObservability(BaseModel):
    """Monitoring, observability, and alerting configuration."""
    
    # Critical fields (80% weight)
    monitoring_strategy: Optional[str] = None  # full_observability | basic_monitoring | custom_only
    log_retention_days: Optional[int] = None   # 30, 90, 180, 365
    apm_required: Optional[bool] = None        # Application Performance Monitoring
    alert_integrations: Optional[str] = None   # teams | email | pagerduty | servicenow
    
    # Optional fields (20% weight)
    custom_metrics: Optional[str] = None
    centralized_logging: Optional[bool] = None
    dashboard_requirements: Optional[str] = None
    compliance_logging: Optional[bool] = None
    
    confidence: float = 0.0
```

**Line 634**: Added to `KnowledgeGraph` class:
```python
monitoring_observability: MonitoringObservability = Field(default_factory=MonitoringObservability)
```

### 2. Monitoring Agent (`src/agents/domain_agents/monitoring_agent.py`)

**NEW FILE**: Complete domain agent implementation:

**Expert System Prompt**:
- Azure Monitor, Application Insights, Log Analytics expertise
- KQL query language knowledge
- Alerting best practices (Azure Monitor Alerts, Action Groups)
- Distributed tracing for microservices
- Cost optimization (hot/cold storage, sampling)

**Critical Fields** (4):
1. `monitoring_strategy` (full_observability | basic_monitoring | custom_only)
2. `log_retention_days` (30, 90, 180, 365)
3. `apm_required` (bool) - Essential for microservices
4. `alert_integrations` (teams, email, pagerduty, servicenow)

**Optional Fields** (4):
1. `custom_metrics` - Business-specific metrics
2. `centralized_logging` - Multi-region/multi-app logging
3. `dashboard_requirements` - Custom dashboards (Grafana, Azure Dashboards)
4. `compliance_logging` - HIPAA/PCI-DSS/SOC2 audit trails

**Conflicts Detected** (3):
1. **Compliance vs Short Retention**: If `compliance_logging=True` but `log_retention_days < 365` → CRITICAL
2. **Multi-region vs No Centralized Logging**: If multi-region but `centralized_logging=False` → HIGH
3. **Microservices vs No APM**: If microservices but `apm_required=False` → HIGH

### 3. Orchestrator Integration (`src/orchestrator/knowledge_graph_orchestrator.py`)

**Line 33**: Import `MonitoringAgent`
**Line 63**: Added to domain agents dict:
```python
"monitoring_observability": MonitoringAgent()
```

**Lines 67-117**: Added to ALL 6 intent-based domain orders:
- **NEW_DEPLOYMENT**: ..., security, **monitoring** (at end)
- **EXTEND_EXISTING**: ..., security, **monitoring** (at end)
- **DR_ONLY**: ..., security, **monitoring** (at end)
- **MIGRATION**: ..., security, **monitoring** (at end)
- **OPTIMIZE_COST**: ..., security, **monitoring** (at end)
- **OPTIMIZE_SECURITY**: security (first), ..., **monitoring** (after resiliency)

### 4. Master Orchestrator (`src/orchestrator/master_orchestrator.py`)

**Updated 5 domain_confidence dictionaries** to include monitoring:

1. **Lines 318-326**: `_execute_requirements_stage()` - ready path (kgStart)
2. **Lines 355-363**: `_execute_requirements_stage()` - needs_clarification path (kgStart)
3. **Lines 431-439**: `process_kg_answers()` - ready path (kgAnswer when done)
4. **Lines 451-461**: `process_kg_answers()` - no questions path (kgAnswer when complete)
5. **Lines 475-483**: `process_kg_answers()` - needs_clarification path (main kgAnswer response)

All now return:
```python
"monitoring": kg.monitoring_observability.confidence
```

### 5. API Server (`api/server.py`)

**Lines 699-708**: Updated `/api/kg/status` endpoint:
```python
"domain_confidence": {
    "identity": kg.identity_access.confidence,
    ...,
    "security": kg.security_governance.confidence,
    "monitoring": kg.monitoring_observability.confidence  # NEW
}
```

**Lines 595-611, 650-665**: Added debug logging for domain_confidence in both endpoints.

---

## Frontend Changes

### 1. TypeScript Types (`frontend/src/types-kg.ts`)

**DomainConfidence Interface** (line 19):
```typescript
export interface DomainConfidence {
  identity: number;
  runtime: number;
  networking: number;
  data: number;
  resiliency: number;
  security: number;
  monitoring: number;  // NEW
}
```

**DOMAIN_NAMES Constant** (line 145):
```typescript
export const DOMAIN_NAMES = {
  ...,
  monitoring: 'Monitoring & Observability',  // NEW
};
```

**DOMAIN_COLORS Constant** (line 151):
```typescript
export const DOMAIN_COLORS: Record<string, string> = {
  ...,
  monitoring: '#06B6D4',  // cyan-500  // NEW
};
```

### 2. UI Components

**DomainProgressBar** (`frontend/src/components/DomainProgressBar.tsx`):

**Lines 16-24**: Updated domain array:
```typescript
const domains = [
  'identity',
  'runtime',
  'networking',
  'data',
  'resiliency',
  'security',
  'monitoring',  // NEW
] as const;
```

**Line 65**: Updated `isActive` check to include `monitoring_observability`:
```typescript
const isActive = currentDomain === `${domain}_access` || 
                 currentDomain === `${domain}_platform` || 
                 currentDomain === `${domain}_connectivity` || 
                 currentDomain === `${domain}_persistence` || 
                 currentDomain === `${domain}_dr` || 
                 currentDomain === `${domain}_governance` ||
                 currentDomain === `${domain}_observability`;  // NEW
```

**KGWizard** (`frontend/src/components/KGWizard.tsx`):

**Lines 46-53**: Added monitoring to initial state:
```typescript
const [domainConfidence, setDomainConfidence] = useState<KGStartResponse['domain_confidence']>({
  identity: 0,
  runtime: 0,
  networking: 0,
  data: 0,
  resiliency: 0,
  security: 0,
  monitoring: 0,  // NEW
});
```

**Lines 191-198**: Added monitoring to reset handler:
```typescript
setDomainConfidence({
  identity: 0,
  ...,
  monitoring: 0,  // NEW
});
```

---

## Testing Checklist

- [x] Backend: Model compiles with all fields
- [x] Backend: Agent imports and initializes
- [x] Backend: Orchestrator includes monitoring in domain orders (all 6 intents)
- [x] Backend: All domain_confidence dicts return monitoring (5 locations)
- [x] Backend: API endpoint returns monitoring in response
- [x] Frontend: TypeScript compilation succeeds
- [x] Frontend: DomainConfidence interface includes monitoring
- [x] Frontend: UI constants include monitoring name + color (cyan)
- [x] Frontend: DomainProgressBar displays monitoring progress
- [x] Frontend: KGWizard initializes monitoring at 0%

### Runtime Testing Needed:

1. **Start New Wizard Session**:
   - Enter "Build microservices app with 5 services on Azure AKS"
   - Verify 7 domains appear in progress bar (identity → monitoring)
   - Verify monitoring domain shows cyan color (#06B6D4)

2. **Monitoring Questions**:
   - After answering 6 domains, verify monitoring questions appear
   - Expected questions (for microservices):
     - "What monitoring strategy?" → full_observability (for microservices)
     - "Log retention?" → 90 or 365 days
     - "APM required?" → Yes (critical for microservices)
     - "Alert integrations?" → teams | pagerduty

3. **Conflict Detection**:
   - Test compliance + short retention → Should trigger CRITICAL conflict
   - Test microservices + no APM → Should trigger HIGH conflict
   - Test multi-region + no centralized logging → Should trigger HIGH conflict

4. **UI Progress Updates**:
   - Verify monitoring confidence starts at 0%
   - After answering 2 critical fields → ~40%
   - After answering 4 critical fields → ~80% ("Complete")
   - Verify "Ready for Design" appears after all 7 domains ≥ 80%

---

## Example Monitoring Questions

**Scenario**: Microservices on AKS with 10K users

**Generated Questions**:
```json
[
  {
    "question": "What monitoring strategy best fits your microservices architecture?",
    "field": "monitoring_strategy",
    "options": [
      "full_observability - Application Insights + Azure Monitor + Log Analytics (recommended for microservices)",
      "basic_monitoring - Azure Monitor only (basic health checks)",
      "custom_only - Custom metrics and alerts only"
    ],
    "importance": "critical"
  },
  {
    "question": "What log retention period is required?",
    "field": "log_retention_days",
    "options": ["30", "90", "180", "365"],
    "importance": "critical"
  },
  {
    "question": "Is Application Performance Monitoring (APM) required? (Essential for distributed tracing in microservices)",
    "field": "apm_required",
    "options": ["true", "false"],
    "importance": "critical"
  },
  {
    "question": "What alert notification channels do you need?",
    "field": "alert_integrations",
    "options": [
      "teams - Microsoft Teams",
      "email - Email notifications",
      "pagerduty - PagerDuty integration",
      "servicenow - ServiceNow ITSM"
    ],
    "importance": "critical"
  }
]
```

---

## Architecture Decisions

### Why Monitoring is 7th (Last) Domain?

1. **Dependencies**: Monitoring needs context from all other domains:
   - **Identity**: Monitoring Azure AD signin logs
   - **Runtime**: Monitoring VM/container health, app logs
   - **Networking**: Monitoring NSG flow logs, firewall rules
   - **Data**: Monitoring database performance, backup jobs
   - **Resiliency**: Monitoring failover events, replication lag
   - **Security**: Monitoring security alerts, compliance logs

2. **Cross-Domain Integration**: Monitoring observability spans all domains, so it's asked last to have full context.

### Why Cyan Color (#06B6D4)?

- **Distinct**: Not used by other domains (blue, green, purple, amber, red, pink)
- **Visibility**: High contrast on white background
- **Association**: Cyan commonly represents monitoring/observability tools (Prometheus, Grafana, New Relic)

---

## Files Modified

### Backend (Python)
1. `src/models/knowledge_graph.py` - Added MonitoringObservability model
2. `src/agents/domain_agents/monitoring_agent.py` - NEW FILE (complete agent)
3. `src/orchestrator/knowledge_graph_orchestrator.py` - Added to domain agents + orders
4. `src/orchestrator/master_orchestrator.py` - Updated 5 domain_confidence dicts
5. `api/server.py` - Updated /api/kg/status endpoint

### Frontend (TypeScript/React)
1. `frontend/src/types-kg.ts` - DomainConfidence, DOMAIN_NAMES, DOMAIN_COLORS
2. `frontend/src/components/DomainProgressBar.tsx` - domains array, isActive check
3. `frontend/src/components/KGWizard.tsx` - Initial state, reset handler

---

## Next Steps

1. **Runtime Testing**: Run full wizard with monitoring questions
2. **Verify Conflicts**: Test 3 monitoring-related conflicts
3. **Architecture Integration**: Ensure architecture agent uses monitoring requirements in HLD
4. **Cost Agent**: Include monitoring costs (Application Insights ingestion, Log Analytics storage)
5. **Documentation**: Update user-facing docs to explain monitoring domain

---

## Known Issues / Edge Cases

1. **APM for Serverless**: Azure Functions has built-in Application Insights - agent should detect this
2. **Log Analytics Costs**: 5GB/month free tier - agent should recommend based on data volume
3. **Multi-region Centralized Logging**: Requires Log Analytics Workspace per region or central hub
4. **Compliance Retention**: Some regulations require 7+ years - 365 days may not be enough

---

**Status**: ✅ Ready for testing
**Estimated Testing Time**: 15 minutes (full wizard + conflict scenarios)
