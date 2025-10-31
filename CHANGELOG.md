# Changelog

All notable changes to Co-Pilot SE will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for Phase 1 (Week 1-2)
- Azure infrastructure provisioning (simplified, no RAG)
- Multi-cloud service mapping research
- Trusted sources validation

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
