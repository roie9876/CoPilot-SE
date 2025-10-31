# Open Questions & Decisions Pending

**Project:** Co-Pilot for Solution Engineers  
**Version:** 2.0 (Multi-Cloud POC)  
**Last Updated:** October 31, 2025

---

## Purpose

This document tracks open questions for the **10-user multi-cloud POC**. Many original questions have been resolved through the pivot to a simplified POC approach (online-only data, no RAG, 4 agents, 8-10 weeks).

---

## Resolved Questions (POC Decisions Made)

### ✅ RESOLVED: RAG vs. Online-Only Data Strategy
**Decision:** Online-only for POC (no RAG, no vector store, no document upload)  
**Rationale:** Faster development, always-current data, sufficient for 10-user POC  
**Date:** October 31, 2025  
**Future:** May add RAG in Phase 6 (post-POC) for proprietary documents

---

### ✅ RESOLVED: Compliance Validation in POC
**Decision:** Remove Compliance Agent from POC scope  
**Rationale:** Adds complexity, not critical for architecture design validation  
**Date:** October 31, 2025  
**Future:** May add as 5th agent in Phase 7 (Enterprise Features)

---

### ✅ RESOLVED: User Scale & Target Audience
**Decision:** 10-user POC (cloud architects only), not 1000 users  
**Rationale:** Validate concept before scaling  
**Date:** October 31, 2025  
**Future:** Scale to 50-100 users in Phase 6 if POC successful

---

### ✅ RESOLVED: Authentication Strategy
**Decision:** Azure AD with RBAC (no cloud provider authentication for POC)  
**Rationale:** Cost estimates from public sources don't require AWS/GCP/OCI credentials  
**Date:** October 31, 2025  
**Future:** May add cloud provider auth in Phase 7 for precise cost estimation

---

### ✅ RESOLVED: Document Upload Feature
**Decision:** Not in POC scope  
**Rationale:** Online-only approach doesn't require document upload  
**Date:** October 31, 2025  
**Future:** Add in Phase 6 when implementing RAG for proprietary content

---

### ✅ RESOLVED: Knowledge Base Refresh Frequency
**Decision:** Real-time online search (no pre-indexed knowledge base)  
**Rationale:** Online-only approach always fetches current data  
**Date:** October 31, 2025  
**Impact:** No refresh costs, always current

---

### ✅ RESOLVED: Primary UI for POC
**Decision:** Web portal (primary), MCP for GitHub Copilot Chat (secondary)  
**Rationale:** Simplest for 10-user POC, Teams bot deferred to Phase 6  
**Date:** October 31, 2025  
**Future:** Add Teams bot in Phase 6 based on user feedback

---

### ✅ RESOLVED: Multi-Cloud Strategy
**Decision:** Unified agent, one cloud at a time (no hybrid/multi-cloud architectures in POC)  
**Rationale:** Simpler for POC, validates concept across all 4 clouds  
**Date:** October 31, 2025  
**Future:** Add hybrid/multi-cloud support in Phase 7

---

## Critical Questions (Block POC Development)

### Q1: Microsoft Agent Framework Version & Capabilities

**Question:** Which version of Microsoft Agent Framework should we use, and what are its current capabilities?

**Why it matters:** Master Orchestrator + 4-agent coordination is core to architecture

**Needed:**
- [ ] Confirm latest stable version
- [ ] Review official documentation
- [ ] Understand multi-agent coordination patterns
- [ ] Test with 4 agents (Requirements, Architecture, Cost, Documentation)
- [ ] Check Azure region support (Sweden Central)

**Owner:** AI/ML Engineer + Tech Lead  
**Deadline:** End of Phase 1 (Week 2)

**Action Items:**
1. Review Agent Framework documentation
2. Build proof-of-concept with 4 agents
3. Test Master Orchestrator coordination
4. Validate state management
5. Document integration patterns

---

### Q2: GPT-5 Availability Timeline

**Question:** When will GPT-5 be available in Azure OpenAI (Sweden Central)?

**Why it matters:** Architecture assumes GPT-5 with Chain-of-Thought; may need fallback

**Current Status:** Unclear availability date

**Needed:**
- [ ] Contact Azure OpenAI product team
- [ ] Get official timeline or preview access
- [ ] Assess GPT-4 Turbo as fallback
- [ ] Test GPT-4 Turbo with 5-stage CoT prompts

**Owner:** Product Manager + Tech Lead  
**Deadline:** End of Phase 1 (Week 2)

**Fallback Plan:**
- Start with GPT-4 Turbo (proven, available)
- Design for easy model swapping
- Migrate to GPT-5 when available

---

### Q3: Bing Search API Quota & Rate Limits

**Question:** What are the actual rate limits and quota for Bing Search API (S1 tier)?

**Why it matters:** Core data acquisition strategy depends on Bing Search

**Current Assumption:** S1 tier = 1000 queries/second, but actual POC needs ~10 qps

**Needed:**
- [ ] Confirm Bing Search S1 tier limits
- [ ] Test rate limiting behavior
- [ ] Validate caching reduces query volume
- [ ] Estimate actual POC query volume (10 users × 5 sessions/day × 20 queries/session = 1000 queries/day)

**Owner:** Backend Engineer  
**Deadline:** Before Phase 3 (Week 6)

**Risk:** If rate limits too low, implement aggressive caching or upgrade tier

---

## Important Questions (Affect POC Design)

### Q4: Multi-Cloud Service Mapping Accuracy

**Question:** How do we maintain accurate service equivalencies across AWS/GCP/Azure/Oracle?

**Why it matters:** Architecture Agent must map services correctly across clouds

**Current Assumption:** Manual curation + trusted community sources

**Needed:**
- [ ] Complete service mapping research (Phase 1, Week 2)
- [ ] Validate mappings with multi-cloud experts
- [ ] Create feedback mechanism for incorrect mappings
- [ ] Determine update frequency (quarterly?)

**Owner:** Tech Lead + Multi-Cloud SMEs  
**Deadline:** End of Phase 1 (Week 2)

**Options:**
1. **Manual curation:** Maintain YAML file with service mappings (fast, high accuracy)
2. **LLM-generated:** Let GPT-5 infer mappings (flexible, may have errors)
3. **Hybrid:** Curated mappings + LLM for edge cases (best of both)

**Recommendation:** Start with manual curation (Option 1), validate during POC

---

### Q5: Trusted Sources Validation Process

**Question:** How do we validate and maintain the curated list of 30+ trusted community sources?

**Why it matters:** Data quality depends on source credibility

**Current Assumption:** Manually curated list validated quarterly

**Needed:**
- [ ] Define validation criteria (accessibility, content quality, publication frequency)
- [ ] Test all sources during Phase 1 (Week 2)
- [ ] Create monitoring for broken links or paywalls
- [ ] Establish quarterly review process

**Owner:** Tech Lead + Product Manager  
**Deadline:** End of Phase 1 (Week 2)

**Validation Criteria:**
- Source accessible (not behind paywall)
- Published within last 6 months
- Aligned with official cloud provider guidance
- Community reputation (GitHub stars, subscriber count, etc.)

---

### Q6: YouTube Transcript Reliability

**Question:** How reliable are YouTube transcripts (auto-generated vs. manual)?

**Why it matters:** Determines trust level for YouTube-sourced citations

**Current Assumption:** Auto-generated transcripts acceptable, but note in citations

**Needed:**
- [ ] Test transcript quality for trusted channels (John Savill, AWS re:Invent, etc.)
- [ ] Identify channels with manual transcripts
- [ ] Determine if auto-generated transcripts should have lower credibility score
- [ ] Test extraction with 20 videos

**Owner:** AI/ML Engineer  
**Deadline:** Before Phase 3 (Week 7)

**Options:**
- Accept all transcripts with disclaimer
- Prefer manual transcripts (credibility score 1.0 vs. 0.8)
- Flag auto-generated transcripts in citations

**Recommendation:** Accept all, note "auto-generated" in citation

---

### Q7: Public Pricing Accuracy Tolerance

**Question:** What level of cost accuracy is acceptable when using public pricing sources (no cloud provider API)?

**Why it matters:** Sets expectations for Cost Agent output

**Current Assumption:** ±30% acceptable for POC

**Needed:**
- [ ] Survey pilot users: What accuracy do they need?
- [ ] Test Cost Agent estimates against actual bills
- [ ] Define disclaimer language ("Estimates based on public pricing, not actual quotes")
- [ ] Determine if ±30% is acceptable or too wide

**Owner:** Product Manager + Pilot Users  
**Deadline:** Before Phase 3 (Week 7)

**Considerations:**
- POC focus is architecture validation, not precise pricing
- Public pricing lacks discounts, commitments, enterprise agreements
- More accurate requires cloud provider authentication (deferred to Phase 7)

**Recommendation:** ±30% acceptable for POC with clear disclaimers

---

### Q8: MCP Adoption Strategy

**Question:** How do we encourage pilot users to try MCP (GitHub Copilot Chat) integration?

**Why it matters:** MCP is secondary interface, need to validate value

**Current Assumption:** Some pilot users use GitHub Copilot, will try MCP

**Needed:**
- [ ] Survey pilot users: Who uses GitHub Copilot?
- [ ] Create onboarding guide for MCP integration
- [ ] Provide demo video showing @copilot-se commands
- [ ] Track MCP usage metrics during pilot

**Owner:** Product Manager  
**Deadline:** Before Phase 4 (Week 9)

**Success Metrics:**
- ≥30% of pilot users install MCP
- ≥10% use MCP at least once per week
- Positive feedback on MCP experience

---

### Q9: Cloud-Specific Icon Sets

**Question:** Where do we source official icon sets for AWS, GCP, Azure, Oracle?

**Why it matters:** Diagram generation requires cloud-specific icons

**Needed:**
- [ ] Identify official icon repositories for each cloud
  - AWS: AWS Architecture Icons 2024
  - Azure: Azure Architecture Icons
  - GCP: Google Cloud Architecture Diagramming Tool icons
  - Oracle: OCI Architecture Icons
- [ ] Download and organize icon sets
- [ ] Test diagram generation with icons
- [ ] Ensure licensing allows redistribution

**Owner:** Documentation Agent Developer  
**Deadline:** Before Phase 4 (Week 8)

**Options:**
1. Use official icon sets (best quality, licensing check needed)
2. Use generic cloud icons (faster, less professional)
3. Text-based diagrams only (simplest, less visual appeal)

**Recommendation:** Option 1 (official icons) for professional quality

---

### Q10: Diagram Generation Approach

**Question:** Should we generate diagrams programmatically or use templates?

**Why it matters:** Affects implementation complexity and diagram quality

**Needed:**
- [ ] Research Draw.io XML generation libraries
- [ ] Test Mermaid → Draw.io conversion
- [ ] Evaluate third-party diagram APIs (Lucidchart, Diagrams.net)
- [ ] Assess GPT-5 capability to generate diagram code

**Owner:** Tech Lead + Documentation Agent Developer  
**Deadline:** Before Phase 4 (Week 8)

**Options:**
1. **Programmatic Draw.io XML:** Full control, complex, high quality
2. **Mermaid diagrams:** Simple, limited layouts, good for POC
3. **Template-based:** Fast, rigid, consistent style
4. **Third-party API:** Easy integration, cost per diagram

**Recommendation for POC:** Option 2 (Mermaid) for speed, Option 1 post-POC

---

## Nice-to-Have Questions (Post-POC)

---

## Nice-to-Have Questions (Post-POC Enhancements)

### Q11: IaC Generation (Bicep/Terraform)

**Question:** Should the Documentation Agent generate Infrastructure-as-Code skeletons?

**Why it matters:** High-value feature but adds complexity

**Current Status:** Deferred to post-POC

**Needed:**
- [ ] Survey pilot users: Would they use IaC skeletons?
- [ ] Assess complexity (Bicep for Azure/AWS CDK for AWS/Terraform for GCP/OCI)
- [ ] Determine if skeleton or full implementation

**Owner:** Product Manager  
**Deadline:** Post-POC (Phase 6)

**Recommendation:** Not in POC scope, add in Phase 6 if pilot users request

---

### Q12: Multi-Language Support

**Question:** Do we need to support languages other than English?

**Why it matters:** Affects LLM prompts, UI, citations

**Current Assumption:** English only for POC

**Needed:**
- [ ] Identify pilot user geographies (assume mostly English-speaking)
- [ ] Assess demand post-POC
- [ ] Estimate effort for localization

**Owner:** Product Manager  
**Deadline:** Post-POC (Phase 6)

**Recommendation:** English-only for POC, internationalization in Phase 6

---

### Q13: Collaboration Features

**Question:** Should multiple architects collaborate on a single architecture?

**Why it matters:** Affects session management and data model

**Current Assumption:** Single-user sessions for POC

**Needed:**
- [ ] Observe pilot user workflows
- [ ] Assess value of real-time collaboration
- [ ] Estimate implementation complexity

**Owner:** Product Manager  
**Deadline:** Post-POC (Phase 6)

**Recommendation:** Single-user for POC, collaboration in Phase 6

---

### Q14: Architecture Version History

**Question:** Should users be able to view and compare previous architecture versions?

**Why it matters:** Useful for iterative design but adds complexity

**Current Assumption:** Save history, no comparison UI for POC

**Needed:**
- [ ] Interview pilot users: Do they iterate on designs?
- [ ] Assess value of version comparison vs. simple history
- [ ] Determine if simple diff or visual comparison

**Owner:** Product Manager  
**Deadline:** Post-POC (Phase 6)

**Recommendation:** Save history in backend, add comparison UI in Phase 6

---

### Q15: Teams Bot Interface

**Question:** Should we add Microsoft Teams bot as third interface?

**Why it matters:** Many architects use Teams, conversational interface could be valuable

**Current Status:** Deferred to Phase 6

**Needed:**
- [ ] Survey pilot users: Would they use Teams bot?
- [ ] Assess implementation effort
- [ ] Determine if Teams bot is higher priority than other Phase 6 features

**Owner:** Product Manager  
**Deadline:** Post-POC (Phase 6)

**Recommendation:** If pilot users request Teams bot, prioritize in Phase 6

---

## Governance & Compliance Questions (POC Scope)

### Q16: Audit Log Retention for POC

**Question:** How long should audit logs be retained during 10-user POC?

**Why it matters:** Affects storage costs and compliance

**Current Assumption:** 90 days for POC

**Needed:**
- [ ] Check Microsoft internal compliance requirements for POC/pilot systems
- [ ] Calculate minimal storage costs

**Owner:** Compliance Team  
**Deadline:** Before Phase 1 (Week 2)

**Note:** Production (post-POC) will require longer retention (likely 2 years)

---

### Q17: Data Residency for 10 Pilot Users

**Question:** Will all 10 pilot users be based in EU, or do we need to support US/APAC?

**Why it matters:** POC infrastructure is Sweden Central only

**Current Assumption:** Select EU-based pilot users for POC

**Needed:**
- [ ] Identify pilot user locations
- [ ] Assess latency impact if non-EU users included
- [ ] Determine if acceptable for POC

**Owner:** Product Manager  
**Deadline:** Before Phase 5 (Week 10) - pilot selection

**Recommendation:** Prefer EU users for POC, test US/APAC latency if needed

---

### Q18: PII Handling in POC

**Question:** How should we handle customer names and project details during POC?

**Why it matters:** Pilot users may use real customer scenarios

**Current Assumption:** Allow customer names, but clearly mark system as POC/test

**Needed:**
- [ ] Check data handling policies for POC systems
- [ ] Determine if PII redaction required
- [ ] Add disclaimer to UI ("POC System - Do Not Use for Production")

**Owner:** Compliance Team + Product Manager  
**Deadline:** Before Phase 1 (Week 2)

**Recommendation:** Allow customer names with disclaimer, reassess for production

---

## Performance & Scalability Questions (POC Scope)

### Q19: POC Performance Targets

**Question:** What performance is acceptable for 10-user POC?

**Why it matters:** Determines optimization effort

**Current Targets:**
- Total workflow time: <10 minutes (acceptable for POC)
- Search latency: <2 seconds
- Architecture generation: <3 minutes

**Needed:**
- [ ] Validate targets with pilot users
- [ ] Measure actual performance during testing
- [ ] Identify bottlenecks if targets missed

**Owner:** Tech Lead  
**Deadline:** Phase 5 (Week 10) - testing

**Note:** Production may require stricter targets (<5 min total)

---

### Q20: Concurrent User Handling for POC

**Question:** How many concurrent users should POC infrastructure support?

**Why it matters:** Affects infrastructure sizing

**Current Assumption:** 10 total users, max 3 concurrent (morning usage spike)

**Needed:**
- [ ] Estimate pilot user usage patterns
- [ ] Test infrastructure with 3-5 concurrent requests
- [ ] Monitor during pilot for actual concurrency

**Owner:** Tech Lead + DevOps  
**Deadline:** Phase 1 (Week 2) - infrastructure setup

**Note:** Production will need auto-scaling for 100+ concurrent users

---

## Decision Log - POC Pivot

### Key Decisions Made (October 31, 2025)

| Date | Question | Decision | Rationale | Impact |
|------|----------|----------|-----------|--------|
| 2025-10-31 | **Azure-only vs. Multi-Cloud** | Multi-cloud (AWS/GCP/Azure/Oracle) | Broader market, unified agent validates across platforms | Complete architecture redesign |
| 2025-10-31 | **RAG vs. Online-Only** | Online-only (no RAG, no vector store) | Faster development, always-current data, sufficient for POC | Removed 40% of original infrastructure |
| 2025-10-31 | **User Scale** | 10-user POC (not 1000) | Validate concept before scaling | Reduced timeline from 17 weeks to 8-10 weeks |
| 2025-10-31 | **Agent Architecture** | 4 specialized agents (removed Compliance) | POC focuses on architecture design, not compliance validation | Simpler orchestration |
| 2025-10-31 | **Data Strategy** | Bing Search + trusted sources + YouTube + public pricing | No document upload, no ingestion pipeline | Eliminated knowledge base development phase |
| 2025-10-31 | **Authentication** | Azure AD only (no cloud provider auth) | Public pricing sources don't require AWS/GCP/OCI credentials | Simplified auth, ±30% cost accuracy acceptable |
| 2025-10-31 | **Primary UI** | Web portal + MCP (secondary) | Teams bot deferred to Phase 6 | Faster development |
| 2025-10-31 | **Deployment Region** | Sweden Central | GPT-5 availability, EU compliance | Single-region for POC |
| 2025-10-31 | **Multi-Cloud Strategy** | Unified agent, one cloud at a time | No hybrid/multi-cloud architectures in POC | Simpler prompts, validates concept |
| 2025-10-31 | **Timeline** | 8-10 weeks POC | Removed RAG phases, simplified scope | From 17 weeks to 10 weeks |
| 2025-10-31 | **Cost Estimation** | Public sources, ±30% accuracy | Sufficient for POC, may add cloud provider APIs post-POC | Faster implementation, clear disclaimers |
| 2025-10-31 | **MCP Integration** | Secondary interface (GitHub Copilot Chat) | Validates value, not critical for POC success | ~$20/month hosting |

---

## Next Steps

### Phase 1 (Week 1-2): Foundation & Research
- [ ] Resolve Q1: Microsoft Agent Framework version and capabilities
- [ ] Resolve Q2: GPT-5 availability (or confirm GPT-4 Turbo fallback)
- [ ] Complete Q4: Multi-cloud service mapping research
- [ ] Validate Q5: All 30+ trusted sources accessible

### Phase 3 (Week 6-7): Data Sources Integration
- [ ] Resolve Q3: Bing Search API quota and rate limits
- [ ] Answer Q6: YouTube transcript reliability (test with 20 videos)
- [ ] Validate Q7: Public pricing accuracy (±30% acceptable?)

### Phase 4 (Week 8-9): Documentation & MCP
- [ ] Resolve Q9: Cloud-specific icon sets (source and license)
- [ ] Answer Q10: Diagram generation approach (Mermaid vs. Draw.io XML)
- [ ] Implement Q8: MCP adoption strategy (onboarding guide, demo)

### Phase 5 (Week 10-11): Testing & Pilot
- [ ] Validate Q19: POC performance targets met
- [ ] Measure Q20: Actual concurrent user load
- [ ] Collect pilot user feedback on all open questions

### Post-POC (Phase 6+)
- [ ] Address "Nice-to-Have" questions (Q11-Q15) based on pilot feedback
- [ ] Re-evaluate resolved questions (Q16-Q18) for production requirements
- [ ] Decide on Phase 6 features: RAG, Teams bot, IaC generation, collaboration

---

**Document Owner:** Product Manager + Tech Lead  
**Review Frequency:** Weekly during POC development, after each phase completion  
**Version:** 2.0 (Multi-Cloud POC)
