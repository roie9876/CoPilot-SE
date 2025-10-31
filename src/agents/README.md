# Agents Module

This directory will contain the 4 AI agent implementations for Co-Pilot SE:

1. **Requirements Agent** - Extract and structure requirements from user input
2. **Multi-Cloud Architecture Agent** - Design architectures for AWS/GCP/Azure/Oracle
3. **Cost Agent** - Estimate costs from public pricing sources
4. **Documentation Agent** - Generate HLDs and diagrams

## Structure (To be implemented in Phase 2)

```
agents/
├── __init__.py
├── base_agent.py              # Base class for all agents
├── requirements_agent.py      # Requirements extraction
├── architecture_agent.py      # Multi-cloud architecture design
├── cost_agent.py              # Cost estimation
└── documentation_agent.py     # HLD and diagram generation
```

See [Agent Specifications](../../docs/03-agent-specifications.md) for detailed requirements.
