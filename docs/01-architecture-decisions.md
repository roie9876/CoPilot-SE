# Architecture Decision Records (ADRs)

**Project:** Co-Pilot for Solution Engineers  
**Version:** 2.0 (Multi-Cloud POC)  
**Date:** October 31, 2025

---

## Table of Contents

1. [ADR-001: Multi-Cloud Platform Strategy](#adr-001-multi-cloud-platform-strategy)
2. [ADR-002: Multi-Agent Architecture](#adr-002-multi-agent-architecture)
3. [ADR-003: Data Source Strategy](#adr-003-data-source-strategy)
4. [ADR-004: Chain-of-Thought Implementation](#adr-004-chain-of-thought-implementation)
5. [ADR-005: LLM and Orchestration Platform](#adr-005-llm-and-orchestration-platform)
6. [ADR-006: Diagram Generation Formats](#adr-006-diagram-generation-formats)
7. [ADR-007: Cost Estimation Strategy](#adr-007-cost-estimation-strategy)
8. [ADR-008: MCP Integration](#adr-008-mcp-integration)
9. [ADR-009: Deployment Region](#adr-009-deployment-region)
10. [ADR-010: User Interface Strategy](#adr-010-user-interface-strategy)
11. [ADR-011: POC Scope](#adr-011-poc-scope)

---

## ADR-001: Multi-Cloud Platform Strategy

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
We need to decide whether to build a cloud-specific system or support multiple cloud platforms (AWS, GCP, Azure, Oracle Cloud), and if multi-cloud, how to architect the agent system.

### Decision
**Chosen: Unified Multi-Cloud Agent (single agent handles all cloud platforms)**

### Options Considered

#### Option A: Cloud-Specific Agents
- Separate specialized agent for each cloud (AWS Agent, Azure Agent, GCP Agent, Oracle Agent)
- Each agent deeply specialized in one platform

**Pros:**
- Deep specialization per cloud
- Easier to optimize cloud-specific patterns
- Clear separation of concerns

**Cons:**
- 4x maintenance overhead
- Harder to keep all agents at same quality level
- More complex orchestration
- Higher infrastructure costs

#### Option B: Unified Multi-Cloud Agent ✅ SELECTED
- Single Architecture Agent handles all clouds
- Cloud platform selected by user at start of conversation
- Agent uses cloud-specific knowledge when needed

**Pros:**
- Simpler architecture and maintenance
- Single agent to optimize and improve
- Lower infrastructure costs
- Easier to ensure consistent quality across clouds
- Matches real-world usage (most projects target one cloud)

**Cons:**
- Less deep specialization per cloud
- Larger context/prompt needed
- May be slower to respond initially

### Rationale

User requirement: "one cloud at a time" - no hybrid or multi-cloud architectures needed for POC. Most real-world engagements target a single cloud platform. A unified agent with cloud selection at conversation start provides the best balance of simplicity and capability.

### Architecture Scope
- **Single cloud per design**: No hybrid/multi-cloud architectures
- **No migration scenarios**: No cloud-to-cloud migration designs
- **User selects target**: Architect specifies target cloud + industry vertical (e.g., "AWS, Public Sector")
- **Supported platforms**: AWS, Google Cloud Platform (GCP), Microsoft Azure, Oracle Cloud Infrastructure (OCI)

### Consequences

**Positive:**
- Simpler implementation and maintenance
- Faster to build and test
- Lower infrastructure costs
- Consistent quality across all clouds

**Negative:**
- May need larger prompts to cover all clouds
- Less optimization per individual cloud
- Future hybrid/multi-cloud features will require rework

### Implementation Notes
- Architect specifies target cloud at conversation start
- Agent system prompt includes patterns for all four clouds
- Use cloud-specific retrieval from online sources based on selected platform
- Track cloud selection in conversation state

---

## ADR-002: Multi-Agent Architecture

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
We need to decide between a single monolithic agent or multiple specialized agents for handling different aspects of cloud architecture design (requirements extraction, architecture design, cost estimation, documentation).

### Decision
**Chosen: Specialized Agent System (4 agents) coordinated by Master Orchestrator**

### Agent Breakdown

1. **Master Orchestrator**: Routes requests, coordinates workflow, manages conversation state
2. **Requirements Extraction Agent**: Parses conversational input, extracts technical requirements, identifies ambiguities
3. **Multi-Cloud Architecture Design Agent**: Designs solutions for AWS/GCP/Azure/Oracle based on selected cloud, recommends services, provides justifications
4. **Cost Estimation Agent**: Estimates costs using public pricing sources, provides low/med/high scenarios
5. **Documentation Generation Agent**: Creates HLD, diagrams (Draw.io/PPT/PNG), presentations

**Removed from POC:** Compliance Validation Agent (out of scope)

### Options Considered

#### Option A: Specialized Agent System ✅ SELECTED
- 4 specialized agents + orchestrator
- Each agent has focused context and capabilities

**Pros:**
- Better specialization and optimization per domain
- Can run agents in parallel for performance
- Easier to test, debug, and maintain individual agents
- Focused context reduces token usage per agent
- Easier to update specific capabilities

**Cons:**
- More complex orchestration logic
- Need to manage state between agents
- More infrastructure components

#### Option B: Single Mega-Agent
- One agent with access to all tools and knowledge
- Handles all tasks from requirements to deliverables

**Pros:**
- Simpler architecture
- Natural context maintenance
- Easier initial setup

**Cons:**
- Huge prompts, higher token costs
- Harder to optimize specific capabilities
- More prone to confusion with complex requests

### Rationale

The specialized approach allows:
- **Parallel processing**: Multiple agents can work simultaneously
- **Domain expertise**: Each agent becomes expert in its domain
- **Incremental development**: Build and test agents independently
- **Simplicity for POC**: 4 agents is manageable for 10-user pilot

### Consequences

**Positive:**
- Clear separation of concerns
- Easier maintenance and updates
- Better observability (can monitor each agent independently)
- Reasonable complexity for POC

**Negative:**
- More complex than single agent
- Need orchestration logic
- More infrastructure than monolithic approach

### Implementation Notes
- Use Microsoft Agent Framework for orchestration
- Design clear agent interfaces and contracts
- Implement agent-to-agent communication patterns
- Build comprehensive orchestrator decision logic
- Track workflow state across agent invocations

---

## ADR-003: Data Source Strategy

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
We need to decide how the system accesses cloud architecture knowledge. Options include RAG with document upload, pre-built knowledge bases, or online-only retrieval from public sources.

### Decision
**Chosen: Online-Only Retrieval (no RAG, no document upload, no persistent knowledge base)**

### Options Considered

#### Option A: RAG with Document Upload
- Users upload documents to knowledge base
- Vector embeddings and retrieval
- Persistent storage

**Pros:**
- Can include proprietary internal knowledge
- Offline capability possible
- Faster retrieval from indexed content

**Cons:**
- Complex infrastructure (vector DB, ingestion pipeline)
- Storage costs and maintenance
- Content becomes stale without updates
- PII/security concerns with uploaded docs

#### Option B: Pre-Built Knowledge Base
- Curated and maintained knowledge base
- No user uploads
- Periodic updates

**Pros:**
- Controlled quality
- No user-generated content issues
- Predictable content

**Cons:**
- Still requires RAG infrastructure
- Maintenance overhead
- May miss niche/latest information

#### Option C: Hybrid RAG + Online
- Knowledge base for common patterns
- Fall back to online search for latest info

**Pros:**
- Best of both worlds potentially

**Cons:**
- Most complex
- Highest infrastructure costs

#### Option D: Online-Only ✅ SELECTED
- Real-time web search via Bing Search API
- Access official cloud documentation online
- Curated list of trusted community sources
- YouTube transcripts for video content
- Public pricing calculators

**Pros:**
- Always current (no stale data)
- No storage/indexing infrastructure needed
- No PII/security concerns with uploaded docs
- Simpler architecture for POC
- Access to latest announcements and updates

**Cons:**
- Requires internet connectivity
- Slower than indexed retrieval
- Dependent on external sources
- Search quality depends on query formulation
- No offline support

### Data Sources

**Primary Search:**
- Bing Search API (Microsoft)

**Official Cloud Documentation:**
- AWS Documentation (docs.aws.amazon.com)
- Azure Documentation (learn.microsoft.com)
- GCP Documentation (cloud.google.com/docs)
- Oracle Cloud Documentation (docs.oracle.com/cloud)

**Trusted Community Sources:**

**Azure:**
- John Savill (YouTube channel + blog) - "The Azure Bible"
- Thomas Maurer's blog - Azure infrastructure
- Azure Friday - Microsoft video series
- Microsoft Learn - Official documentation
- Azure Architecture Center - Reference architectures

**AWS:**
- AWS Official Blog - Latest announcements
- AWS Architecture Blog - Architecture patterns
- Werner Vogels' blog - AWS CTO insights
- AWS re:Invent sessions - Conference content
- AWS Well-Architected Framework - Design principles

**GCP:**
- Google Cloud Blog - Official announcements
- GCP Architecture Center - Reference architectures
- Cloud Next sessions - Conference recordings
- Kubernetes documentation - For GKE

**Oracle:**
- Oracle Cloud Infrastructure documentation
- Oracle Architecture Center
- Oracle Cloud blogs

**Pricing Sources:**
- Public pricing calculators (no authentication)
- Pricing pages via web search
- Curated pricing guides (updated quarterly)

**YouTube Content:**
- Extract transcripts via YouTube Data API
- Reference video URLs in citations
- Use video metadata for relevance

### Rationale

User requirements:
- "everything need to be from online"
- "no proprietary internal"
- "only use public cloud documentions as relatable source"
- Simple approach, no cloud provider authentication

For POC phase, online-only provides:
- **Simplicity**: No complex RAG infrastructure
- **Currency**: Always up-to-date information
- **Lower cost**: No storage, indexing, or maintenance
- **Flexibility**: Easy to add/change sources

Future enhancement path: Add RAG capabilities post-POC if needed ("later we may add upload doc and do RAG").

### Consequences

**Positive:**
- Much simpler architecture
- No storage infrastructure needed
- Always current information
- No PII/security concerns from uploads
- Lower costs
- Faster POC delivery

**Negative:**
- Slower response times (real-time search)
- Requires internet connectivity
- Dependent on external source availability
- Search quality varies
- No offline support
- Higher latency per query

### Implementation Notes
- Integrate Bing Search API with appropriate query formulation
- Curate and maintain list of trusted sources per cloud
- Implement citation tracking for all retrieved content
- Design retry logic for search failures
- Monitor search costs and optimize queries
- Consider caching frequently accessed information (session-based)
- Research YouTube Data API for transcript extraction

---

## ADR-004: Chain-of-Thought Implementation

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
GPT-5 supports Chain-of-Thought (CoT) reasoning. We need to decide how structured vs. free-form this reasoning should be for optimal explainability and traceability.

### Decision
**Chosen: Hybrid approach - Structured outer loop with free-form reasoning within each step**

### Structured Workflow

```mermaid
graph LR
    A[Understand] --> B[Research]
    B --> C[Design]
    C --> D[Estimate]
    D --> E[Document]
```

**Stage 1: Understand**
- Parse user input and cloud selection
- Extract intent and requirements
- Identify ambiguities
- Ask clarifying questions if needed

**Stage 2: Research**
- Search Bing for relevant documentation
- Retrieve cloud-specific best practices
- Access trusted community sources
- Check pricing information
- Compile evidence with citations

**Stage 3: Design**
- Propose architecture for selected cloud
- Map services to requirements
- Justify design decisions
- Consider alternatives
- Provide cloud-specific recommendations

**Stage 4: Estimate**
- Calculate costs using public sources
- Provide low/medium/high scenarios
- Include assumptions
- Add regional variations

**Stage 5: Document**
- Generate HLD
- Create diagrams (Draw.io/PPT/PNG)
- Add citations
- Format outputs
- Prepare exports

### Options Considered

#### Option A: Free-Form CoT
- Let model reason naturally, expose thinking in UI
- No structured constraints

**Pros:** Flexible, more human-like, natural language
**Cons:** Harder to parse, less structured for debugging, inconsistent

#### Option B: Structured Reasoning Steps
- Force agent to follow predefined steps
- Each step produces structured output (JSON)

**Pros:** Predictable, easier to debug, consistent format
**Cons:** May feel mechanical, less flexible, could constrain capabilities

#### Option C: Hybrid ✅ SELECTED
- Structured outer loop: `Understand → Research → Design → Estimate → Document`
- Free-form reasoning within each step
- Best of both worlds

**Pros:** Balance of structure and flexibility, traceable workflow, natural reasoning, explainable
**Cons:** Moderate complexity, need careful stage transitions

### Rationale

The hybrid approach provides:
- **Traceability**: Clear workflow stages for auditing
- **Flexibility**: Agent can reason naturally within stages
- **User experience**: Users understand "what stage" the agent is in
- **Debugging**: Easier to identify where issues occur

### Consequences

**Positive:**
- Clear progress indication for users
- Better error handling (can retry specific stages)
- Easier to optimize individual stages
- Meets traceability requirements
- Natural conversation flow

**Negative:**
- More complex prompt engineering
- Need to manage stage transitions
- Potential for rigid behavior if not carefully designed

### Implementation Notes
- Each agent implements the 5-stage workflow (where applicable)
- Orchestrator tracks current stage
- Structured metadata output per stage
- Free-form reasoning visible to users
- Stage transitions logged for observability

---

## ADR-005: LLM and Orchestration Platform

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
We need to select the LLM and orchestration framework for the multi-agent system.

### Decision
**Chosen: Azure OpenAI GPT-5 with Microsoft Agent Framework**

### Components

**LLM:**
- **Azure OpenAI GPT-5** with Chain-of-Thought capabilities
- Reasoning capabilities for complex architecture decisions
- Long context window for comprehensive analysis
- Multi-turn conversation support

**Orchestration:**
- **Microsoft Agent Framework** (not Semantic Kernel)
- Native multi-agent orchestration
- Agent-to-agent communication patterns
- State management across agents
- Built-in observability

**AI Strategy:**
- Online-only retrieval (no RAG for POC)
- Prompt engineering (no custom fine-tuning)
- Real-time web search integration
- Citation tracking

### Rationale

**Azure OpenAI GPT-5:**
- Latest model with enhanced reasoning capabilities
- Chain-of-Thought support for explainability
- Enterprise-grade security and compliance
- Regional deployment (Sweden Central)
- Microsoft support and SLAs

**Microsoft Agent Framework:**
- Purpose-built for multi-agent systems
- Better fit than Semantic Kernel for agent orchestration
- Native state management
- Easier inter-agent communication
- Better observability and debugging

**No Custom Fine-Tuning:**
- Prompt engineering sufficient for POC
- Faster to iterate and improve
- No training data requirements
- Lower costs and maintenance

### Consequences

**Positive:**
- Enterprise-grade LLM capabilities
- Strong orchestration framework
- Fast iteration with prompt engineering
- Microsoft ecosystem alignment
- Good observability

**Negative:**
- Dependent on Azure OpenAI availability
- GPT-5 costs (manageable for 10-user POC)
- Agent Framework learning curve

### Implementation Notes
- Deploy Azure OpenAI in Sweden Central
- Configure Agent Framework for 4 specialized agents
- Implement comprehensive system prompts
- Design agent communication protocols
- Set up logging and observability

---

## ADR-006: Diagram Generation Formats

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
Architects need architecture diagrams in various formats for different audiences and tools.

### Decision
**Chosen: Multi-format support - Draw.io XML (primary), PowerPoint, PNG images**

### Supported Formats

**1. Draw.io XML (Primary)**
- Native format for draw.io/diagrams.net
- Editable by architects
- Version controllable (text-based)
- Supports all diagram elements

**2. PowerPoint (.pptx)**
- Executive presentations
- Easy to customize in Office
- Standard corporate format
- Widely supported

**3. PNG Images**
- Quick sharing and viewing
- Embed in documentation
- No special tools required
- Good for email/chat

### Rationale

Different stakeholders need different formats:
- **Architects**: Editable Draw.io for modifications
- **Executives**: PowerPoint for presentations
- **Everyone**: PNG for quick viewing

Multi-format support maximizes tool utility and adoption.

### Consequences

**Positive:**
- Flexibility for different workflows
- Higher adoption across roles
- Professional deliverables
- Easy sharing

**Negative:**
- More complex generation logic
- Need to maintain multiple generators
- File storage/management
- Quality consistency across formats

### Implementation Notes
- Generate Draw.io XML using structured templates
- Convert to PowerPoint using rendering libraries
- Export PNG using headless rendering
- Provide format selection in UI
- Ensure cloud-specific icons for AWS/GCP/Azure/Oracle

---

## ADR-007: Cost Estimation Strategy

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
Cost estimates are critical for customer proposals, but we don't want to authenticate to cloud provider APIs. We need a strategy using public sources.

### Decision
**Chosen: Simplified cost estimation using public pricing sources**

### Approach

**Data Sources:**
1. **Public pricing calculators** (AWS, Azure, GCP, Oracle - no auth required)
2. **Web search for pricing pages** via Bing Search
3. **Curated pricing guides** (maintained quarterly)
4. **Pricing documentation** from official sources

**Estimation Structure:**

```json
{
  "summary": {
    "monthly_low": 5000,
    "monthly_estimated": 8000,
    "monthly_high": 12000,
    "currency": "USD",
    "region": "us-east-1",
    "confidence": "Medium"
  },
  "breakdown": {
    "compute": {
      "description": "EC2 instances, ECS/EKS",
      "monthly_cost": 3500,
      "assumptions": "t3.large x 3, 24x7"
    },
    "storage": {
      "description": "S3, EBS",
      "monthly_cost": 500,
      "assumptions": "1TB S3, 500GB EBS"
    },
    "networking": {
      "description": "Data transfer, load balancer",
      "monthly_cost": 300,
      "assumptions": "Standard data transfer rates"
    }
  },
  "assumptions": [
    "Based on public pricing as of 2025-10-31",
    "Standard tier services",
    "No reserved instances or savings plans",
    "Estimate only - requires validation"
  ],
  "disclaimer": "This is a preliminary estimate. Consult cloud provider for accurate pricing.",
  "sources": [
    "https://aws.amazon.com/pricing/",
    "AWS Pricing Calculator (public)"
  ]
}
```

### Options Considered

#### Option A: Cloud Provider APIs with Authentication
- Use official pricing APIs
- Real-time accurate pricing

**Pros:** Most accurate
**Cons:** Requires authentication, complex setup, user rejected this approach

#### Option B: Web Scraping
- Scrape pricing pages
- Parse pricing tables

**Pros:** No authentication
**Cons:** Fragile, may violate ToS, hard to maintain

#### Option C: Public Sources + Search ✅ SELECTED
- Use Bing Search for pricing information
- Reference public calculators
- Maintain curated pricing guides
- Provide estimate ranges

**Pros:** Simple, no authentication, reasonable accuracy, always citable
**Cons:** Less accurate, manual maintenance, estimate ranges

### Rationale

User requirements:
- "the goal of the app was to be simple and not required to authenticate to any cloud provider"
- "do we have other way to get the cloud provider price?"

Public sources provide reasonable accuracy for initial estimates without authentication complexity. For POC with 10 users starting slow, this is sufficient.

### Consequences

**Positive:**
- Simple implementation
- No authentication needed
- Works across all clouds
- Always citable sources
- Lower cost oper (no API fees)

**Negative:**
- Lower accuracy (±30% deviation acceptable)
- Manual maintenance of pricing guides
- Estimate ranges instead of exact costs
- Requires quarterly updates

### Implementation Notes
- Implement Bing Search queries for pricing
- Build curated pricing guides per cloud per region
- Update pricing guides quarterly
- Provide low/medium/high scenarios
- Include clear assumptions and disclaimers
- Cite all pricing sources

---

## ADR-008: MCP Integration

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
We need to expose Co-Pilot functionality beyond the standalone UI to enable integration with other tools like GitHub Copilot Chat.

### Decision
**Chosen: Implement MCP (Model Context Protocol) server to expose Co-Pilot capabilities**

### MCP Strategy

**Primary Use Cases:**
1. **GitHub Copilot Chat integration**: Enable Copilot Chat users to invoke Co-Pilot architecture design capabilities
2. **External tool integration**: Allow MCP-compatible tools to access Co-Pilot functionality
3. **Workflow automation**: Enable scripting and automation scenarios

**Interface Priority:**
- **UI-first**: Teams/Web/Office interfaces are primary
- **MCP as secondary**: MCP exposes functionality for integration, not primary user interface

**Scope:**
- MCP server exposes Co-Pilot to external tools
- MCP NOT exposed to entire application (not replacing UI)
- Focus on key capabilities: architecture design, cost estimation, documentation generation

### Exposed MCP Tools

```typescript
{
  "tools": [
    {
      "name": "design_cloud_architecture",
      "description": "Design cloud architecture based on requirements",
      "inputSchema": {
        "type": "object",
        "properties": {
          "requirements": { "type": "string" },
          "cloud_provider": { "enum": ["aws", "gcp", "azure", "oracle"] },
          "industry_vertical": { "type": "string" }
        }
      }
    },
    {
      "name": "estimate_costs",
      "description": "Estimate costs for proposed architecture",
      "inputSchema": {
        "type": "object",
        "properties": {
          "architecture": { "type": "string" },
          "cloud_provider": { "type": "string" },
          "region": { "type": "string" }
        }
      }
    },
    {
      "name": "generate_documentation",
      "description": "Generate HLD and diagrams",
      "inputSchema": {
        "type": "object",
        "properties": {
          "architecture": { "type": "string" },
          "format": { "enum": ["drawio", "pptx", "png"] }
        }
      }
    }
  ]
}
```

### Options Considered

#### Option A: REST API Only
- Standard REST endpoints
- OpenAPI specification

**Pros:** Familiar, well-understood
**Cons:** Doesn't integrate with MCP ecosystem

#### Option B: MCP Server ✅ SELECTED
- Implement Model Context Protocol
- Native integration with GitHub Copilot Chat and other MCP clients

**Pros:** Standards-based, GitHub Copilot integration, extensible
**Cons:** Newer protocol, smaller ecosystem

#### Option C: Both REST + MCP
- Expose both interfaces

**Pros:** Maximum compatibility
**Cons:** Duplication, more maintenance

### Rationale

User requirements:
- "it can expose API or MCP"
- Primary use cases are "C and A" - external tools calling Co-Pilot + Copilot Chat workflows
- Secondary to UI

MCP provides standardized integration with GitHub Copilot Chat and other MCP-compatible tools, enabling broader reach without building custom integrations.

### Consequences

**Positive:**
- GitHub Copilot Chat integration
- Standards-based approach
- Extensible for future tools
- Broader reach beyond standalone UI

**Negative:**
- Need to learn MCP protocol
- Smaller ecosystem than REST
- Additional server component

### Implementation Notes
- Implement MCP server following protocol specification
- Expose 3 primary tools: design, estimate, generate
- Implement authentication (Azure AD)
- Document MCP integration for users
- Test with GitHub Copilot Chat
- Consider REST API in future if needed

---

## ADR-009: Deployment Region

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
We need to select the Azure region for deploying the Co-Pilot infrastructure.

### Decision
**Chosen: Sweden Central (primary deployment region)**

### Rationale

**Factors:**
- Azure OpenAI availability
- Compliance and data residency
- Latency for global users
- Service availability
- Cost considerations

**Sweden Central selected because:**
- Azure OpenAI GPT-5 availability
- GDPR compliance (EU region)
- Good latency for European and global users
- Full service support for required Azure services
- Reasonable pricing

### Consequences

**Positive:**
- GDPR compliant by default
- Strong Azure service availability
- Good global latency
- Azure OpenAI access

**Negative:**
- Higher latency for Asia-Pacific users
- May need additional regions for scale

### Implementation Notes
- Deploy all services in Sweden Central for POC
- Monitor latency for global users
- Plan multi-region if needed post-POC

---

## ADR-010: User Interface Strategy

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
Architects work across multiple tools and platforms. We need to provide flexible access to Co-Pilot capabilities.

### Decision
**Chosen: Multi-interface approach - Teams bot + Web portal + Office add-ins + REST API + MCP**

### Interfaces

**1. Microsoft Teams Bot (Primary)**
- Conversational interface
- Natural workflow integration
- Easy access where architects already work
- Team collaboration features

**2. Web Portal**
- Full-featured UI
- Dashboard and history
- Advanced configuration
- File uploads/downloads

**3. Office Add-ins**
- PowerPoint add-in for presentations
- Word add-in for documentation
- Direct integration with deliverables

**4. REST API**
- Programmatic access
- Automation scenarios
- Custom integrations

**5. MCP Server**
- GitHub Copilot Chat integration
- MCP-compatible tool access
- Secondary interface

### Rationale

Architects need flexibility:
- **Conversational**: Teams bot for quick interactions
- **Visual**: Web portal for detailed work
- **Integrated**: Office add-ins for deliverable creation
- **Programmable**: API and MCP for advanced scenarios

Multi-interface maximizes adoption and utility.

### Consequences

**Positive:**
- Meets diverse workflow needs
- Higher adoption potential
- Flexibility for different scenarios

**Negative:**
- More interfaces to build and maintain
- Consistent UX across interfaces challenging
- More testing required

### Implementation Notes
- Start with Web portal for POC
- Add Teams bot in Phase 2
- MCP server for GitHub Copilot integration
- Office add-ins and REST API as needed

---

## ADR-011: POC Scope

### Status
✅ **ACCEPTED** - October 31, 2025

### Context
We need to define the scope and scale for the proof-of-concept phase.

### Decision
**Chosen: Limited POC with 10 users, focused feature set**

### POC Scope

**Scale:**
- **10 cloud architects** (pilot group)
- **8-10 weeks** timeline
- **4 agents** + orchestrator

**Included Features:**
- Requirements extraction from conversation
- Multi-cloud architecture design (AWS/GCP/Azure/Oracle)
- Cloud platform selection
- Cost estimation (public sources)
- Documentation generation (HLD, diagrams)
- MCP integration (GitHub Copilot Chat)
- Web portal interface

**Excluded from POC:**
- Compliance validation
- Document upload / RAG
- Hybrid/multi-cloud architectures
- Cloud migration scenarios
- Teams bot interface
- Office add-ins
- Large-scale deployment (1000+ users)

### Rationale

User requirements:
- "lets start with 10 users for POC"
- "yes to start we will work slow, later we may add upload doc and do RAG"

POC focus enables:
- **Rapid validation** of core concept
- **Learning** from small user group
- **Iteration** before scaling
- **Lower risk** and investment

### Future Phases (Post-POC)

**Phase 2 - Enhanced Features:**
- Document upload and RAG capabilities
- Compliance validation
- Teams bot interface
- Expand to 50-100 users

**Phase 3 - Scale:**
- Support 1000+ architects
- Hybrid/multi-cloud architectures
- Cloud migration scenarios
- Office add-ins
- Advanced automation

### Consequences

**Positive:**
- Faster time to POC
- Lower cost and risk
- Focus on core value
- Room to learn and iterate
- Simpler infrastructure

**Negative:**
- Limited feature set initially
- Small user group (less feedback)
- Will need rework for scale
- Some requested features deferred

### Implementation Notes
- Focus Phase 0-1 on POC delivery
- Select diverse 10-architect pilot group
- Gather comprehensive feedback
- Plan Phase 2 based on POC learnings
- Document lessons learned
- Measure success metrics

### Success Criteria for POC

- ✅ Architecture generation for all 4 clouds working
- ✅ Cost estimation with reasonable accuracy (±30%)
- ✅ Documentation generation (HLD + diagrams)
- ✅ MCP integration with GitHub Copilot Chat functional
- ✅ ≥70% positive feedback from 10 architects
- ✅ ≥4.0/5 user satisfaction score
- ✅ <5 minutes to generate complete architecture

---

## Summary of Changes from Original Design

### Major Scope Changes

**Expanded:**
- Azure-only → Multi-cloud (AWS/GCP/Azure/Oracle)
- Single interface → Multi-interface (UI + API + MCP)
- Microsoft SEs only → All cloud architects (SE/CSA/SA/PS)

**Simplified:**
- RAG + document upload → Online-only (no persistent storage)
- 1000 users → 10 users (POC)
- 5 agents → 4 agents (removed Compliance)
- Complex infrastructure → Simplified (no vector DB, no storage)
- Authenticated APIs → Public sources only

**Removed:**
- Compliance validation agent
- Document upload capabilities
- Knowledge base and RAG pipeline
- Azure AI Search / Vector Store
- SQL Database, Blob Storage, Redis
- Cloud provider API authentication
- PII redaction (no document storage)
- 1000-user scale infrastructure

**Added:**
- MCP server integration
- Multi-cloud platform support
- Unified multi-cloud agent
- Online-only data retrieval strategy
- Trusted community sources curation
- YouTube transcript extraction
- Public pricing calculator integration

### Architecture Impact

**Before:**
- Complex RAG-based system
- Large infrastructure footprint
- Document ingestion pipeline
- Vector storage and retrieval
- 1000-user scale
- Azure-focused

**After:**
- Simple online retrieval system
- Minimal infrastructure (GPT-5 + App Service + Bing Search)
- No storage components
- 10-user POC scale
- Multi-cloud support
- MCP integration for extensibility

---

**Last Updated:** October 31, 2025  
**Document Owner:** Solution Engineering Team  
**Version:** 2.0 (Multi-Cloud POC)
