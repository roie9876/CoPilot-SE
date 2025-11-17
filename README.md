# Co-Pilot for SE 🚀

**An AI-powered assistant that helps cloud architects design and document Azure architectures — in minutes.**

[![Status](https://img.shields.io/badge/status-POC%20development-blue)](./docs/00-project-overview.md)
[![Phase](https://img.shields.io/badge/phase-Phase%201%20foundation-orange)](./docs/07-implementation-roadmap.md)
[![Version](https://img.shields.io/badge/version-2.0%20multi--cloud%20POC-green)](./docs/README.md)
[![Timeline](https://img.shields.io/badge/timeline-8--10%20weeks-purple)](./docs/07-implementation-roadmap.md)

---

## 🎯 Vision (POC)

**"From customer intent → Azure architecture design with costs and documentation — in <10 minutes."**

Co-Pilot SE transforms the cloud architect workflow by automating:
- **Adaptive requirements gathering** via Knowledge Graph Wizard with 7 domain agents
- **Azure architecture design** with justifications based on Well-Architected Framework
- **Cost estimation** from Azure pricing sources (±30% accuracy)
- **Professional HLD generation** with diagrams and citations

**Current Status:** ✅ **Production Ready** - Full end-to-end workflow working (Nov 2025)  
**POC Scope:** 10-user pilot, 8-10 weeks, online-only data (no RAG), simplified infrastructure (~$839/month)

---

## ✨ Key Features (POC)

### 🌐 **Azure Architecture Design**
Design architectures for **Microsoft Azure** based on:
- **Azure Well-Architected Framework** - Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency
- **Cloud Adoption Framework** - Migration, modernization, and governance best practices
- **Azure Architecture Center** - Reference architectures and design patterns

**Azure-focused** for the POC with deep expertise in Azure services and best practices.

### 🔍 **Knowledge Graph Wizard (NEW)**
Adaptive requirements gathering via interactive wizard:
- **7 Domain Agents**: Identity, Runtime, Networking, Data, Resiliency, Security, Monitoring
- **LLM-Powered Questions**: Each agent generates 2-4 contextual questions using GPT-5 + Bing Search
- **Smart Question Flow**: Prioritizes critical gaps, then low-confidence domains
- **Conflict Detection**: Automatically identifies contradicting requirements (e.g., PCI compliance + public endpoints)
- **Progress Tracking**: Real-time confidence scores per domain (80% threshold)
- **Example Scenarios**: Pre-built templates for common architectures

### 🏗️ **Architecture Design with Justifications**
Proposes Azure solutions with:
- Azure service selection based on requirements
- Design justifications citing Azure best practices
- Alternative analysis ("Why this service vs. alternatives?")
- Citations from **Azure documentation** and trusted community sources

### 💰 **Cost Estimation from Public Sources**
Generates estimates with:
- **Public pricing calculators** (no cloud provider authentication)
- ±30% accuracy (acceptable for POC)
- Compute, storage, networking, support breakdowns
- Clear disclaimers about estimate limitations

### 📄 **Professional HLD Generation**
Exports ready-to-use:
- High-Level Design documents (Markdown)
- Architecture diagrams (Draw.io, Mermaid, images)
- Cost breakdown tables
- Cited references (official docs + trusted community sources)

### 🔌 **GitHub Copilot Chat Integration (MCP)**
Use Co-Pilot SE from VS Code:
```
@copilot-se design an Azure serverless API for image processing
@copilot-se estimate costs for Azure App Service with 3 instances
@copilot-se generate documentation for the Azure architecture
```

**Note:** Compliance validation deferred to Phase 7 (post-POC)

---

## 📸 Example Screenshots

Here are examples of what Co-Pilot SE generates:

### High-Level Design Document
Professional HLD with architecture overview, requirements, and compliance considerations:

![HLD Document](./docs/screenshots/image%20(1).png)

### Cost Estimation
Detailed cost breakdown by Azure service with multiple usage scenarios:

![Cost Estimate](./docs/screenshots/image%20(2).png)

### Logical Architecture Diagram
Auto-generated architecture diagrams showing Azure services and data flow:

![Logical Diagram](./docs/screenshots/image%20(3).png)

### Requirements Gathering Progress
Real-time tracking of requirements gathering across 7 domains with confidence scores:

![Requirements Gathering](./docs/screenshots/image%20(4).png)

### Architecture Wizard
The interactive wizard guides you through requirements gathering with pre-built templates for common scenarios:

![Architecture Wizard](./docs/screenshots/image%20(6).png)

---

## 🏛️ Architecture (POC)

### Multi-Agent System (11 Agents)

Co-Pilot SE uses **11 specialized AI agents** coordinated by two orchestrators:

```
┌───────────────────────────────────────────────────────────────────┐
│              Master Orchestrator (Stage 1-4)                       │
│          (Microsoft Agent Framework + GPT-5)                       │
│     Coordinates architecture/cost/documentation workflow           │
└──────────────────────────┬────────────────────────────────────────┘
                           │
          ┌────────────────┼──────────────┬──────────────────┐
          │                │              │                  │
  ┌───────▼────────┐ ┌────▼─────────┐ ┌─▼──────┐ ┌─────────▼─────────┐
  │  Requirements  │ │    Azure     │ │  Cost  │ │   Documentation   │
  │     Agent      │ │ Architecture │ │ Agent  │ │       Agent       │
  │  (Stage 1)     │ │   Agent      │ │(Stage 3│ │     (Stage 4)     │
  └────────┬───────┘ │  (Stage 2)   │ └────────┘ └───────────────────┘
           │         └──────────────┘
           │
           │ Delegates to Knowledge Graph Wizard
           │
┌──────────▼──────────────────────────────────────────────────────────┐
│         Knowledge Graph Orchestrator (Requirements Stage)            │
│           Adaptive requirements gathering via 7 domain agents        │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
    ┌──────────────────────┼────────────────────────┐
    │      │      │      │      │      │      │     │
┌───▼──┐ ┌─▼──┐ ┌─▼───┐ ┌▼───┐ ┌▼─────┐ ┌──▼───┐ ┌▼────────┐
│Identity│Runtime│Network│Data│Resiliency│Security│Monitoring│
│ Agent  │Agent │Agent  │Agent│  Agent   │ Agent  │  Agent   │
│        │      │       │     │          │        │          │
└────────┘ └────┘ └─────┘ └───┘ └────────┘ └──────┘ └─────────┘
```

**Key Components:**
- **Master Orchestrator**: 4-stage workflow (Requirements → Architecture → Cost → Documentation)
- **Knowledge Graph Orchestrator**: Adaptive requirements gathering with 7 domain agents
- **7 Domain Agents**: Identity, Runtime, Networking, Data, Resiliency, Security, Monitoring
  - Each agent generates contextual questions via LLM + Bing Search
  - Detects domain-specific conflicts
  - Calculates confidence scores (80% critical fields + 20% optional)
- **Architecture Agent**: Azure architecture design with Well-Architected Framework
- **Cost Agent**: Public pricing research and estimation
- **Documentation Agent**: HLD generation with diagrams and citations

**Note:** Compliance Agent removed from POC (may add in Phase 7)

### Technology Stack (POC)

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Cloud Platform** | Microsoft Azure | Azure-only for POC |
| **LLM** | Azure OpenAI GPT-5 (or GPT-4 Turbo fallback) | 5-stage Chain-of-Thought |
| **Orchestration** | Microsoft Agent Framework | 11-agent coordination (7 domain + 4 workflow) |
| **Data Strategy** | **Online-only** (no RAG, no vector store) | Always-current data, faster development |
| **Data Sources** | Bing Search S1 + Azure Docs + Community | Azure-focused sources, ~$9/month |
| **Authentication** | Azure AD with RBAC | No cloud provider auth for POC |
| **Deployment Region** | Sweden Central | Single region for 10-user POC |
| **Interfaces** | Web Portal (primary) + MCP (secondary) | Teams bot deferred to Phase 6 |
| **Infrastructure Cost** | ~$839/month | $9 Bing + $20 MCP + $810 Azure |

---

## 📚 Documentation (v2.0 - Multi-Cloud POC)

Comprehensive design documentation for the **10-user multi-cloud POC** is available in the [`/docs`](./docs/) folder:

| Document | Purpose |
|----------|---------|
| [📋 Project Overview](./docs/00-project-overview.md) | Azure POC vision, Azure-focused sources |
| [🏛️ Architecture Decisions](./docs/01-architecture-decisions.md) | 11 ADRs (Azure-only, online-only, POC scope) |
| [🔧 System Architecture](./docs/02-system-architecture.md) | Simplified 7-component architecture, ~$839/month |
| [🤖 Agent Specifications](./docs/03-agent-specifications.md) | Master Orchestrator + 11 agent specs with full prompts |
| [🌐 Data Sources Strategy](./docs/04-data-sources-strategy.md) | **Online-only:** Bing Search, Azure docs, trusted sources |
| [🔌 MCP Integration Spec](./docs/05-mcp-integration-spec.md) | MCP server for GitHub Copilot Chat integration |
| [🗺️ Implementation Roadmap](./docs/07-implementation-roadmap.md) | **8-10 week POC** timeline (5 phases, no RAG work) |
| [❓ Open Questions](./docs/08-open-questions.md) | 8 resolved + 20 new POC questions |

**Start here:** [Documentation README](./docs/README.md)

---

## 🚀 Getting Started (POC)

### Prerequisites

- **Azure subscription** with access to:
  - Azure OpenAI (GPT-5 or GPT-4 Turbo fallback)
  - Sweden Central region
- **API Keys:**
  - Bing Search API (S1 tier)
  - YouTube Data API
- **Tools:**
  - Microsoft Agent Framework (latest stable)
  - Python 3.11+
  - Node.js 20 LTS (for MCP server)

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/copilot-se.git
cd copilot-se

# Set up Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up MCP server (Node.js)
cd mcp-server
npm install
cd ..

# Configure environment
cp .env.example .env
# Edit .env with:
#   - Azure OpenAI endpoint + key
#   - Bing Search API key
#   - YouTube Data API key
#   - Azure AD credentials

# Run tests
pytest tests/
npm test --prefix mcp-server
```

**Full setup guide:** [Implementation Roadmap - Phase 1](./docs/07-implementation-roadmap.md#phase-1-foundation--multi-cloud-research)

**Note:** No RAG infrastructure needed (no vector store, no document ingestion)

---

## 📈 Project Status (POC)

### Current Phase: **Planning Complete → Phase 1 Starting** ✅

**Completed (Version 2.0 Pivot):**
- ✅ Multi-cloud POC vision documented
- ✅ All major decisions made (11 ADRs)
- ✅ Simplified architecture designed (7 components)
- ✅ Agent specifications written (Master + 4 agents)
- ✅ Online-only data strategy defined (no RAG)
- ✅ MCP integration spec created
- ✅ 8-10 week POC roadmap created
- ✅ Trusted sources curated (30+ sources across 4 clouds)

**Next Phase: Foundation & Multi-Cloud Research (Week 1-2)**
- 🔲 Provision simplified Azure infrastructure (no RAG components)
- 🔲 Complete multi-cloud service mapping (AWS/GCP/Azure/Oracle)
- 🔲 Validate all 30+ trusted sources accessible
- 🔲 Set up development environment
- 🔲 Team onboarding

### POC Timeline (8-10 Weeks)

| Phase | Duration | Status |
|-------|----------|--------|
| **Phase 1: Foundation & Multi-Cloud Research** | 2 weeks | 🟡 Next |
| **Phase 2: Core Agents Development** | 3 weeks | ⚪ Planned |
| **Phase 3: Data Sources Integration** | 2 weeks | ⚪ Planned |
| **Phase 4: Documentation & MCP** | 2 weeks | ⚪ Planned |
| **Phase 5: Testing & Pilot** | 1-2 weeks | ⚪ Planned |

**Total POC Duration:** 10-11 weeks (includes 1 week buffer)

### Post-POC Roadmap (If Successful)
- **Phase 6: Scale & Enhance** (8 weeks) - 50-100 users, add RAG, Teams bot
- **Phase 7: Enterprise Features** (8 weeks) - Compliance, hybrid/multi-cloud, advanced cost optimization

See: [Implementation Roadmap](./docs/07-implementation-roadmap.md)

---

### POC Success Metrics (10 Users)

| Metric | Target |
|--------|--------|
| **Azure architecture quality** | Generate production-ready Azure architectures aligned with Well-Architected Framework |
| **Total workflow time** | <10 minutes from requirements to HLD |
| **Cost estimation accuracy** | ±30% (Azure pricing, acceptable for POC) |
| **User satisfaction** | ≥70% positive feedback |
| **Average rating** | ≥4.0/5 stars |
| **Real project usage intent** | ≥7 of 10 users would use for real projects |
| **MCP adoption** | ≥30% of users try GitHub Copilot Chat integration |
| **Citation quality** | ≥60% Azure official docs in HLDs |

**Post-POC Targets (Phase 6+):**
- Scale to 50-100 users
- Improve cost accuracy to ±20% (add cloud provider APIs)
- Add compliance validation (reintroduce Compliance Agent)
- Achieve ≥4.5/5 satisfaction for production

---

## 🛠️ Project Structure (POC)

```
copilot-se/
├── docs/                           # Comprehensive POC documentation (v2.0)
│   ├── README.md                  # Documentation index
│   ├── 00-project-overview.md     # Multi-cloud POC vision + trusted sources
│   ├── 01-architecture-decisions.md  # 11 ADRs
│   ├── 02-system-architecture.md  # 7-component simplified architecture
│   ├── 03-agent-specifications.md # Master + 4 agents
│   ├── 04-data-sources-strategy.md  # Online-only (no RAG)
│   ├── 05-mcp-integration-spec.md # MCP server spec
│   ├── 07-implementation-roadmap.md  # 8-10 week POC timeline
│   └── 08-open-questions.md       # Resolved + new POC questions
│
├── src/                           # Source code (to be created in Phase 2-4)
│   ├── agents/                   # 4 AI agent implementations
│   ├── orchestrator/             # Master orchestrator
│   ├── data_sources/             # Bing Search, YouTube API integration
│   ├── api/                      # Azure Functions API
│   └── web/                      # Web portal frontend
│
├── mcp-server/                    # MCP server for GitHub Copilot (Phase 4)
│   ├── src/
│   ├── package.json
│   └── README.md
│
├── infrastructure/                # Simplified Azure IaC (Phase 1)
│   ├── bicep/                    # No RAG infrastructure
│   └── README.md
│
├── tests/                         # Test suite (Phase 2-5)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .github/                       # CI/CD workflows
│   └── workflows/
│
├── requirements.txt               # Python dependencies (to be created)
├── README.md                     # This file
└── .env.example                  # Environment template (to be created)
```

---

## 🤝 Contributing

### Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Develop and test**
   - Write unit tests for new code
   - Update documentation if needed
   - Run linting: `black . && flake8`

3. **Create Pull Request**
   - Describe changes
   - Link to related issues
   - Request review

### Code Standards
- **Python:** PEP 8 (use `black` formatter)
- **TypeScript:** ESLint + Prettier
- **Commits:** Conventional Commits format
- **Tests:** pytest (Python), Jest (TypeScript)

---

## 👥 Team (POC)

### Core Team (8 people)
- **Tech Lead / Architect:** [Name] - Overall architecture, multi-cloud strategy
- **Product Manager:** [Name] - Requirements, pilot management, user research
- **AI/ML Engineers (2):** [Names] - Agent development, prompts, LLM integration
- **Backend Engineers (2):** [Names] - Azure Functions, API, Bing Search integration
- **Frontend Engineer:** [Name] - Web portal, MCP server
- **DevOps Engineer:** [Name] - Simplified infrastructure, CI/CD

### Pilot Users (10 cloud architects)
- 10 users: Azure cloud architects with varying experience levels
- Mix of enterprise and ISV backgrounds
- Different industry verticals (healthcare, finance, retail, etc.)

### Stakeholders
- **Cloud Architect Community:** Target users and advisors
- **Azure SMEs:** Domain experts for Azure best practices validation
- **Compliance Team:** Governance (post-POC Phase 7)

---

## 📞 Contact & Support

### Communication
- **Teams Channel:** [Co-Pilot SE Development]
- **Email:** copilot-se-team@microsoft.com
- **GitHub Issues:** For bugs and feature requests

### Meetings
- **Daily Standup:** 9:00 AM CET (Teams)
- **Sprint Planning:** Every 2 weeks (Mondays)
- **Demo Days:** Monthly (last Friday)

---

## 📜 License

**MIT License**

Copyright (c) 2025 CoPilot-SE Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## 🙏 Acknowledgments

- **Microsoft Agent Framework Team:** Orchestration platform for multi-agent coordination
- **Azure OpenAI Team:** GPT-5 access and support
- **Cloud Architect Community:** POC requirements and trusted sources validation
- **Trusted Community Sources:** 30+ curated sources across AWS/GCP/Azure/Oracle

---

## 📖 Learn More - Azure Best Practices

### Azure Documentation
- [Azure Cloud Adoption Framework](https://learn.microsoft.com/azure/cloud-adoption-framework/)
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)
- [Azure Architecture Center](https://learn.microsoft.com/azure/architecture/)
- [Azure Security Best Practices](https://learn.microsoft.com/azure/security/fundamentals/best-practices-and-patterns)
- [Azure Cost Management](https://learn.microsoft.com/azure/cost-management-billing/)

### Community Resources
- [John Savill's Azure Master Class](https://www.youtube.com/@NTFAQGuy)
- [Azure Updates](https://azure.microsoft.com/updates/)
- [Azure Blog](https://azure.microsoft.com/blog/)

### Tools & Frameworks
- [Microsoft Agent Framework](https://learn.microsoft.com/azure/ai-services/agents/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Bing Search API](https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/)

---

**Built with ❤️ by the Co-Pilot SE Team**

*Empowering cloud architects to design better Azure architectures, faster.*

**Version 2.0 - Azure POC | 10 Users | 8-10 Weeks**
