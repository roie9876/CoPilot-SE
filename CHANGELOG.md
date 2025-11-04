# Changelog

All notable changes to Co-Pilot SE will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.0] - 2025-11-04

### Knowledge Graph Wizard - Production Ready

#### Added
- **Complete End-to-End Workflow**: Architecture → Cost → Documentation (fully integrated)
- **Knowledge Graph Wizard**: Adaptive question flow with 6 domain agents
- **Example Scenarios**: 4 pre-built examples (Azure, AWS, GCP, Oracle) on landing page
- **Cost Estimation Display**: Three-tier cost scenarios (Low/Medium/High) with visual breakdown
- **Documentation Generation**: Full HLD markdown document with download capability
- **Domain-Specific Agents**: 
  - Identity & Access Management
  - Runtime Platform
  - Networking & Connectivity
  - Data Persistence
  - Resiliency & DR
  - Security & Governance

#### Fixed
- **Stale Conflict Resolution**: Conflicts now properly cleared when domain answers updated
- **Domain Priority Logic**: Low-confidence domains now questioned before conflicts
- **Type Conversion Bugs**: Fixed auth_users (string→int), budget (string→dict), existing_infrastructure (string→list)
- **Field Reference Errors**: Fixed external_customers → auth_users field mapping
- **Button Visibility**: Removed CSS conflicts causing white-on-white buttons
- **Missing Field Detection**: Added get_all_missing_fields() for comprehensive low-confidence questioning

#### Changed
- **Default Interface**: Knowledge Graph Wizard is now the only interface (removed legacy multi-stage flow)
- **Title**: "Knowledge Graph Architecture Wizard" → "Architecture Wizard"
- **Orchestrator Flow**: Now runs all 3 stages sequentially (Architecture, Cost, Documentation)
- **UI Layout**: Cleaner single-wizard interface with example scenarios

#### Removed
- Legacy "Multi-Stage Flow (OLD)" toggle and interface
- Global CSS button overrides interfering with Tailwind styles

## [2.0.0] - 2025-10-31

### Major Pivot - Multi-Cloud POC

#### Added
- **Multi-cloud support**: AWS, GCP, Azure, Oracle Cloud
- **Online-only data strategy**: Bing Search API integration
- **30+ trusted community sources**: Curated across all 4 clouds
- **YouTube transcript extraction**: Via YouTube Data API
- **MCP integration specification**: GitHub Copilot Chat support
- **New documentation**:
  - `04-data-sources-strategy.md` (replaces knowledge-base-design)
  - `05-mcp-integration-spec.md` (new MCP server spec)
- **8-10 week POC roadmap**: Simplified timeline

#### Changed
- **Scope**: Azure-only (1000 users) → Multi-cloud POC (10 users)
- **Agent count**: 5 agents → 4 agents (removed Compliance Agent for POC)
- **Data strategy**: RAG + vector store → Online-only
- **Architecture**: 11 components → 7 components
- **Timeline**: 17 weeks → 8-10 weeks
- **Infrastructure cost**: ~$1,500/month → ~$839/month
- **Cost accuracy target**: ±20% → ±30% (acceptable for POC)
- **Interfaces**: Teams bot + Web + Office → Web portal + MCP (Teams deferred)

#### Removed
- RAG pipeline and vector store (deferred to Phase 6 post-POC)
- Document upload capability (not in POC scope)
- Compliance Agent (deferred to Phase 7)
- Azure AI Search dependency
- Document ingestion pipeline
- Knowledge base refresh infrastructure

#### Updated Documentation
- All 9 core documentation files updated for multi-cloud POC
- Architecture Decisions: 11 ADRs now documented
- System Architecture: Simplified to 7 components
- Agent Specifications: Complete rewrites for multi-cloud support
- Implementation Roadmap: New 8-10 week POC phases
- Open Questions: 8 resolved decisions + 20 new POC questions
- Both README files: Updated for POC scope

## [1.0.0] - 2025-10-01

### Initial Azure-Only Design

#### Added
- Initial project vision and requirements
- Azure-only architecture design
- 5-agent system (including Compliance Agent)
- RAG-based knowledge base design
- 17-week implementation roadmap
- Comprehensive documentation structure

#### Documented
- Project overview
- Architecture decisions (initial ADRs)
- System architecture (11 components)
- Agent specifications (5 agents)
- Knowledge base design (RAG pipeline)
- Implementation roadmap (17 weeks, 7 phases)
- Open questions (21 questions)

---

## Version History Summary

- **v2.0.0** (2025-10-31): Multi-Cloud POC - Major pivot to simplified 10-user POC
- **v1.0.0** (2025-10-01): Initial Azure-only design with RAG and 5 agents

---

[Unreleased]: https://github.com/your-org/copilot-se/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/your-org/copilot-se/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/your-org/copilot-se/releases/tag/v1.0.0
