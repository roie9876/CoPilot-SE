# Co-Pilot for SE - Project Overview

**Project Name:** Co-Pilot for Solution Engineers  
**Version:** 2.0 (Multi-Cloud POC)  
**Date:** October 31, 2025  
**Status:** Design & Planning Phase

---

## Executive Summary

Co-Pilot for SE is an AI-powered intelligent assistant designed to augment cloud architects (Solution Engineers, Cloud Solution Architects, Technical Architects, Pre-Sales Engineers) by transforming raw customer inputs into complete, multi-cloud solution designs — with explanations, cost guidance, and exportable deliverables — in minutes.

### Problem Statement

Cloud architects across all major cloud platforms spend significant time on:
- Collecting fragmented requirements from emails, Teams calls, RFPs
- Mapping requirements to cloud reference architectures (AWS, GCP, Azure, Oracle Cloud)
- Researching best practices from official docs and trusted community sources
- Validating architecture designs and estimating costs
- Creating HLDs, diagrams, PowerPoint decks, and technical documentation

Each engagement can take **days of manual work** and is prone to inconsistency and errors as cloud service catalogs rapidly evolve.

### Vision

**"From customer intent → cost-aware, well-architected multi-cloud solution design — in minutes."**

### Mission

Enable cloud architects to design, validate, and document cloud architectures across AWS, GCP, Azure, and Oracle Cloud faster, consistently, and effectively — leveraging real-time access to official documentation, trusted community sources, and public cloud knowledge.

---

## Key Outcomes (POC Phase)

- **70% reduction** in time from meeting to first draft architecture
- **80% reduction** in time from architecture to deliverable deck
- **≤±30% deviation** in cost estimation (using public pricing sources)
- **≥4.0/5** user satisfaction score
- **≥70%** positive feedback from POC users (10 architects)
- **Successful validation** of multi-cloud architecture generation across AWS, GCP, Azure, and Oracle Cloud

---

## Primary User Personas

### 👨‍💻 Cloud Architect (All Roles)
Includes: Solution Engineers (SE), Cloud Solution Architects (CSA), Technical Architects (SA), Pre-Sales Engineers (PS), and similar roles

**Responsibilities:**
- Designs cloud solutions for enterprise, public-sector, or commercial customers
- Works across multiple cloud platforms (AWS, GCP, Azure, Oracle Cloud)
- Needs to generate diagrams, design docs, and cost estimates quickly
- Must select appropriate cloud platform and services based on customer requirements and industry vertical

**Key Needs:**
- Fast access to current cloud best practices
- Multi-cloud service comparisons and recommendations
- Accurate cost estimation without manual research
- Professional deliverables (HLD, diagrams, presentations)

---

## Core Capabilities

1. **Requirement Extraction**: Auto-extract requirements from conversational input
2. **Multi-Cloud Architecture Generation**: Propose solutions for AWS, GCP, Azure, or Oracle Cloud with justifications
3. **Cloud Platform Selection**: Recommend appropriate cloud platform based on customer requirements and industry vertical
4. **Cost Estimation**: Provide cost estimates using public pricing sources and calculators
5. **Deliverable Generation**: Export HLDs, diagrams (draw.io/PPT/image), presentations
6. **Source Traceability**: Every recommendation cites online documentation sources
7. **Real-Time Knowledge**: Access current cloud documentation, trusted community sources (blogs, YouTube), and public pricing

---

## Technology Stack (Confirmed Decisions)

| Component | Technology |
|-----------|-----------|
| **LLM** | Azure OpenAI GPT-5 with Chain-of-Thought |
| **Orchestration** | Microsoft Agent Framework |
| **AI Strategy** | Online-only retrieval + Prompt Engineering (no RAG, no custom fine-tuning) |
| **Data Sources** | Bing Search + Public cloud documentation + Trusted community sources |
| **Knowledge Base** | None (online-only, no persistent storage) |
| **Vector Store** | None (POC phase) |
| **Authentication** | Azure AD with RBAC |
| **Region** | Sweden Central |
| **Interfaces** | Teams app + Web portal + Office add-ins + REST API + MCP (Model Context Protocol) |
| **Integrations** | Bing Search API, Public cloud documentation, YouTube Data API (transcripts), Public pricing calculators |
| **Cloud Platforms** | AWS, Google Cloud Platform (GCP), Microsoft Azure, Oracle Cloud Infrastructure (OCI) |

---

## Key Architectural Decisions

### Decision 1: Multi-Cloud Strategy ✅
**Chosen:** Unified Multi-Cloud Agent (single agent handles all cloud platforms)

**Scope:**
- Support AWS, Google Cloud Platform (GCP), Microsoft Azure, Oracle Cloud Infrastructure (OCI)
- One cloud architecture at a time (no hybrid/multi-cloud designs)
- No cloud migration scenarios (POC phase)
- Architect selects target cloud + industry vertical (e.g., "AWS, Public Sector")

**Rationale:** Simpler implementation, easier maintenance, matches most real-world engagements

---

### Decision 2: Multi-Agent Architecture ✅
**Chosen:** Specialized Agent System (4 agents coordinated by Master Orchestrator)

**Agents:**
1. Requirements Extraction Agent
2. Multi-Cloud Architecture Design Agent (AWS/GCP/Azure/Oracle)
3. Cost Estimation Agent
4. Documentation Generation Agent

**Removed:** Compliance Validation Agent (out of scope for POC)

**Rationale:** Focused scope for POC, specialization where it matters most

---

### Decision 3: Data Source Strategy ✅
**Chosen:** Online-Only (no RAG, no document upload, no persistent knowledge base)

**Data Sources:**
- **Bing Search API** (primary real-time search)
- **Official cloud documentation** (AWS docs, Azure docs, GCP docs, Oracle docs)
- **Trusted community sources** (curated list per cloud provider)
- **YouTube transcripts** (for community expert content like John Savill's videos)
- **Public pricing calculators** (no cloud provider authentication required)

**Rationale:** Simplicity for POC, always current, no storage/indexing overhead

---

### Decision 4: Chain-of-Thought Implementation ✅
**Chosen:** Option C - Hybrid (Structured outer loop, free-form reasoning within each step)

**Flow:** Understand → Research → Design → Estimate → Document

**Rationale:** Balance of structure and flexibility; provides traceability while keeping responses natural

---

### Decision 5: Diagram Output Formats ✅
**Chosen:** Multi-format support
- Draw.io XML (primary)
- PowerPoint
- Image (PNG/SVG)

**Rationale:** Flexibility for different architect workflows and customer preferences

---

### Decision 6: Cost Estimation Detail ✅
**Chosen:** Simplified cost estimation using public sources

**Includes:**
- Compute costs (instance type estimates)
- Storage costs (approximate)
- Bandwidth costs (estimated)
- Low/medium/high usage bands
- Regional variations (where available publicly)

**Sources:** Public pricing calculators, Bing Search for pricing pages, curated pricing guides

**Rationale:** No cloud provider authentication needed, reasonable accuracy for initial estimates

---

### Decision 7: MCP Integration ✅
**Chosen:** Expose Co-Pilot functionality via Model Context Protocol (MCP)

**Primary Use Cases:**
- Integration with GitHub Copilot Chat
- Integration with other MCP-compatible tools
- Enable external tools to invoke Co-Pilot capabilities

**Interface Priority:** UI-first, MCP as secondary interface

**Rationale:** Extends Co-Pilot reach beyond standalone UI, enables workflow integration

---

## Trusted Community Sources (Per Cloud Provider)

### Microsoft Azure

1. **John Savill's Technical Training (YouTube)**  
   Long-form, deeply technical Azure content (networking, identity, governance, security, landing zones). Considered "Azure master class" level and updated frequently with new Azure capabilities.
   - https://www.youtube.com/@NTFAQGuy
   - https://www.youtube.com/channel/UCpIn7ox7j7bH_OFj7tYouOQ

2. **John Savill (Blog / SavillTech)**  
   Blog-style explanations of Azure architecture, operations, identity, hybrid, and AI with practical configuration guidance.
   - https://savilltech.com/

3. **Thomas Maurer (Blog)**  
   Cloud Advocate / Architect content focused on Azure infrastructure, Azure Arc, hybrid, governance, migration, and enterprise landing zone thinking. Hands-on implementation guidance, not marketing.
   - https://www.thomasmaurer.ch

4. **Aidan Finn (Blog)**  
   Long-running Azure IaaS / networking / security / cost optimization blog from an Azure MVP. Strong for production realities (limits, gotchas, HA).
   - https://www.aidanfinn.com

5. **Build5Nines (Chris Pietschmann)**  
   Independent Azure-focused site covering Azure services, certifications, IaC usage, and cloud patterns from a practitioner/MVP point of view.
   - https://build5nines.com

6. **Azure Friday (Video Series)**  
   Short sessions with Microsoft engineers and PMs demoing new Azure features, architectures, and patterns. Good for "what just shipped / how to use it in real life."
   - https://azure.microsoft.com/en-us/resources/videos/azure-friday
   - https://www.youtube.com/playlist?list=PLLasX02E8BPCuB3McX2bQ1HjZB1TjvC5-

7. **Microsoft Learn – Azure**  
   Official Microsoft learning platform with step-by-step labs, interactive modules, and scenario-driven walkthroughs for Azure services. Authoritative and kept current.
   - https://learn.microsoft.com/azure
   - https://learn.microsoft.com/training/azure/

8. **Azure Architecture Center**  
   Microsoft's canonical library of reference architectures, solution blueprints, design patterns, and "choose this vs that" tradeoff guidance for Azure workloads (scalability, DR, security).
   - https://learn.microsoft.com/azure/architecture/

9. **Adam Marczak – Azure for Everyone (YouTube + blog)**  
   Highly structured visual explanations and walkthroughs (App Service, networking, Key Vault, APIM, etc.), tuned for clarity and reproducibility, popular with architects ramping fast.
   - https://www.youtube.com/@Azure4Everyone
   - https://marczak.io

---

### Amazon Web Services (AWS)

1. **AWS News Blog (Official)**  
   Primary source for AWS feature announcements, service launches, and roadmap clarity from AWS engineering/PM teams. The "what actually exists today" feed.
   - https://aws.amazon.com/blogs/aws/

2. **AWS Architecture Blog (Official)**  
   Deep dives into reference architectures, resilience patterns, scalability models, and cost-aware design on AWS. Critical for "how do people actually build X on AWS."
   - https://aws.amazon.com/blogs/architecture/

3. **Werner Vogels – All Things Distributed**  
   Blog of AWS CTO Werner Vogels. Focuses on distributed systems philosophy, durability, scaling, and fault isolation — why AWS is built the way it is and how to design for that mindset.
   - https://www.allthingsdistributed.com/

4. **AWS Well-Architected Framework**  
   Canonical AWS guidance across pillars (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability). Used by AWS SA teams in the field.
   - https://aws.amazon.com/architecture/well-architected/

5. **re:Invent Session Library / YouTube**  
   Full technical talks and breakout sessions from AWS re:Invent (architecture patterns at scale, war stories, service deep dives). High-signal content from PMs and principal engineers.
   - https://www.youtube.com/@AWSEvents
   - https://reinvent.awsevents.com/learn/reinvent-videos/

6. **cloudonaut (Andreas & Michael Wittig)**  
   Independent AWS consultancy/blog from long-time AWS experts (AWS Community Heroes). Practical cost, security, networking, IaC, multi-account, and landing zone tactics — very production-oriented.
   - https://cloudonaut.io/
   - https://www.youtube.com/@cloudonaut
   - Podcast: Available on Spotify and other directories

7. **Last Week in AWS (Corey Quinn)**  
   Weekly AWS news & analysis newsletter/blog by an AWS Community Hero. Curates important changes, pricing gotchas, deprecations, and "this matters / this is noise."
   - https://www.lastweekinaws.com/

8. **widdix GitHub Repos (by the Wittig brothers)**  
   Open source CloudFormation/IaC templates, multi-account setups, and operational best practices. Used by many AWS practitioners as starting points for production infrastructure.
   - https://github.com/widdix
   - https://widdix.net/

---

### Google Cloud Platform (GCP)

1. **Google Cloud Blog (Official)**  
   Central announcement channel for new GCP services, features, and platform capabilities. First place Google posts GA/Preview updates.
   - https://cloud.google.com/blog

2. **Google Cloud Architecture Center**  
   Google's official collection of reference architectures, design patterns, DR plans, data platform blueprints, networking patterns, and cost/perf tradeoffs across GCP.
   - https://cloud.google.com/architecture

3. **Google Cloud YouTube / Google Cloud Tech**  
   Official GCP YouTube channels with deep dives on GKE, networking, security, data platforms, AI/ML on Vertex. Very good for "how do I actually deploy this pattern."
   - https://www.youtube.com/@googlecloudtech
   - https://www.youtube.com/@googlecloudplatform

4. **Google Cloud Next Session Library**  
   Recorded sessions from Google Cloud Next (Google's re:Invent equivalent). Sessions feature PMs, SREs, and large reference customers explaining architectures and lessons learned.
   - https://cloud.withgoogle.com/next/sessions
   - https://www.youtube.com/playlist?list=PLIivdWyY5sqKxYgLtzzEdV6-hwxKF1uHm

5. **Kubernetes Documentation (for GKE)**  
   Official Kubernetes docs are critical because GKE is managed Kubernetes. Best practices for scaling, networking, security policies, and multi-tenancy in GKE.
   - https://kubernetes.io/docs/

6. **Google Cloud Platform Podcast**  
   Weekly/regular podcast produced by Google engineers and advocates, covering new features, platform patterns, customer architectures, and internal best practices.
   - https://cloud.google.com/podcast
   - https://www.youtube.com/playlist?list=PLIivdWyY5sqI_uoJ-fI85oURVBRm1u9zk

7. **Medium – Google Cloud Community / Google Cloud Tech Writers**  
   Curated technical articles by Google Developer Advocates and recognized community experts. Useful for implementation stories and opinionated guidance often ahead of formal docs.
   - https://medium.com/google-cloud
   - https://medium.com/@googlecloud-tech

---

### Oracle Cloud Infrastructure (OCI)

1. **Oracle Cloud Infrastructure (OCI) Docs (Official)**  
   Canonical service documentation for OCI compute, networking, IAM, storage, database, security. Authoritative description of how each service works and how to configure it.
   - https://docs.oracle.com/en-us/iaas/

2. **Oracle Architecture Center**  
   Oracle's official catalog of reference architectures and prescriptive deployment patterns for OCI (network segmentation, security zoning, HA/DR layouts, DB patterns, multicloud interconnect).
   - https://docs.oracle.com/en/solutions/
   - https://www.oracle.com/cloud/architecture/

3. **Oracle A-Team Chronicles (Oracle A-Team Blog)**  
   Deep technical blog written by Oracle's internal "A-Team," described as senior solution architects and engineers who work on strategic/complex customer problems. Posts cover security hardening, networking patterns, tenancy design, and automation at scale.
   - https://www.ateam-oracle.com/
   - https://blogs.oracle.com/ateam/

4. **Oracle Cloud Infrastructure Blog (Official)**  
   Oracle's main OCI blog covering new features, security guidance, multicloud patterns, cost optimization, etc.
   - https://blogs.oracle.com/cloud-infrastructure

5. **Oracle Cloud Customer Connect**  
   Oracle's official peer/community forum for OCI customers and partners. Architects and Oracle engineers actively answer operational questions. Valuable for operational reality and edge cases.
   - https://community.oracle.com/customerconnect/

6. **Oracle ACE Community Blogs**  
   Oracle ACE / ACE Pro / ACE Director members are vetted technical experts recognized by Oracle for deep product expertise. Blogs frequently include advanced OCI reference patterns, identity federation approaches, and multi-cloud integration guidance.
   - https://ace.oracle.com/
   - Example ACE author feed: https://blogs.oracle.com/ateam/authors/

---

**Status:** Curated and validated list for POC implementation

---

## Scale & Scope

### POC Phase
- **Target Users:** 10 cloud architects (pilot group)
- **Cloud Platforms:** AWS, GCP, Azure, Oracle Cloud Infrastructure
- **Architecture Scope:** Single cloud per design (no hybrid/multi-cloud)
- **Geographic Coverage:** Global (any segment)
- **Deployment Region:** Sweden Central (primary)
- **Deployment Model:** Multi-interface (Teams + Web + Office + API + MCP)
- **Data Model:** Online-only (no persistent storage, session-based)

### Future Phases (Post-POC)
- Scale to hundreds/thousands of architects
- Add document upload and RAG capabilities
- Support hybrid/multi-cloud architectures
- Add compliance validation features

---

## Governance & Safety

### Principles
- **No hallucination tolerance**: Ground all responses in online documentation sources
- **Mandatory citations**: Every recommendation includes source URLs and references
- **Human review required**: All outputs marked as "Draft - Requires Human Review"
- **No training on user data**: Customer info never used for model training
- **Session-based data**: No persistent storage of customer requirements or designs (POC phase)

### Compliance
- GDPR compliance
- Export control compliance
- Tenant isolation (operates within Azure tenant boundary)
- No authentication to external cloud providers (uses public sources only)

---

## Next Steps (POC Phase)

1. ✅ Complete architecture decision records (see `01-architecture-decisions.md`)
2. ✅ Design detailed agent specifications (see `03-agent-specifications.md`)
3. ✅ Design data sources strategy (see `04-data-sources-strategy.md`)
4. ✅ Design MCP integration (see `05-mcp-integration-spec.md`)
5. 🔲 Research cloud provider public APIs and pricing sources
6. 🔲 Curate trusted community sources list per cloud platform
7. 🔲 Provision simplified Azure infrastructure (Sweden Central)
8. 🔲 Implement Master Orchestrator Agent
9. 🔲 Build and test Multi-Cloud Architecture Agent
10. 🔲 Integrate Bing Search API
11. 🔲 Create Web portal interface
12. 🔲 Implement MCP server for GitHub Copilot Chat integration
13. 🔲 Test end-to-end POC with 10 architects

---

## Document Index

| Document | Purpose |
|----------|---------|
| `00-project-overview.md` | This document - Executive summary & vision |
| `01-architecture-decisions.md` | Formal ADRs (Architecture Decision Records) |
| `02-system-architecture.md` | High-level system design & component diagrams |
| `03-agent-specifications.md` | Detailed agent specs & system prompts |
| `04-data-sources-strategy.md` | Online data sources, trusted community sources, pricing strategy |
| `05-mcp-integration-spec.md` | MCP server design & GitHub Copilot Chat integration |
| `07-implementation-roadmap.md` | Phases, timeline, milestones (POC-focused) |
| `08-open-questions.md` | Decisions still pending |

---

**Last Updated:** October 31, 2025  
**Document Owner:** Solution Engineering Team
