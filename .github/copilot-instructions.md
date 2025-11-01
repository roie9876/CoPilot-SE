# GitHub Copilot Instructions - Co-Pilot SE

**Project:** Co-Pilot for Solution Engineers (Multi-Cloud Architecture Assistant)  
**Version:** 2.0 (Multi-Cloud POC)  
**Date:** November 1, 2025

---

## 🎯 Project Overview

Co-Pilot SE is an AI-powered assistant that helps Solution Engineers design cloud architectures across AWS, GCP, Azure, and Oracle Cloud. It transforms raw customer requirements into complete, multi-cloud solution designs with cost estimates and documentation.

### POC Scope & Constraints

**CRITICAL**: This is a **10-user POC** (8-10 weeks) with specific limitations:
- ✅ Multi-cloud support: AWS, GCP, Azure, Oracle Cloud (one at a time)
- ✅ Online-only data: Bing Search API + trusted sources (NO RAG, NO vector database)
- ✅ 4 specialized agents + 1 orchestrator
- ✅ Web portal (React + TypeScript) + MCP integration
- ❌ NO document upload capability
- ❌ NO compliance validation agent (out of scope)
- ❌ NO knowledge base or vector store
- ❌ NO Teams bot (deferred to Phase 6)

### Key Architectural Decisions

1. **No RAG System**: Use real-time Bing Search instead of vector database
2. **Serverless**: Azure Functions (consumption plan) for all backend
3. **Simplified**: Minimal infrastructure, stateless for POC
4. **Multi-cloud**: Unified agent handles all clouds (not separate agents per cloud)
5. **MCP as Secondary**: Web portal is primary interface

---

## 🏗️ System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Web Portal   │  │ MCP Clients  │  │ Teams Bot        │  │
│  │ (React+TS)   │  │ (GitHub      │  │ (Future)         │  │
│  │              │  │  Copilot)    │  │                  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │
└─────────┼──────────────────┼─────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  ┌─────────────────────────────┐  ┌────────────────────┐   │
│  │ Azure API Management        │  │ MCP Server         │   │
│  │ (Gateway, Rate Limiting)    │  │ (Node.js 20 LTS)   │   │
│  └─────────────┬───────────────┘  └─────────┬──────────┘   │
└────────────────┼──────────────────────────────┼──────────────┘
                 │                              │
                 ▼                              │
┌─────────────────────────────────────────────────────────────┐
│              Master Orchestrator (Python 3.11)               │
│         (Microsoft Agent Framework on Azure Functions)       │
│                                                              │
│  Stage 1 → Stage 2 → Stage 3 → Stage 4                      │
│    ↓         ↓         ↓         ↓                           │
│  ┌─────┐  ┌──────┐  ┌─────┐  ┌──────────┐                  │
│  │Req  │  │Arch  │  │Cost │  │Doc       │                  │
│  │Agent│  │Agent │  │Agent│  │Agent     │                  │
│  └─────┘  └──────┘  └─────┘  └──────────┘                  │
│     │         │         │          │                        │
│     └─────────┴─────────┴──────────┘                        │
│                    ▼                                         │
│         ┌──────────────────────┐                            │
│         │  Azure OpenAI GPT-5  │                            │
│         └──────────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              External Data Sources (Online)                  │
│  ┌─────────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐  │
│  │ Bing Search │  │ Official │  │YouTube │  │ Pricing  │  │
│  │ API         │  │ Cloud    │  │ Trans- │  │ Calcu-   │  │
│  │             │  │ Docs     │  │ cripts │  │ lators   │  │
│  └─────────────┘  └──────────┘  └────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Agent Workflow (Sequential)

1. **Requirements Agent**: Parse input → Extract requirements → Detect cloud platform
2. **Architecture Agent**: Design multi-cloud solution → Select services → Best practices
3. **Cost Agent**: Research pricing → Calculate costs → Generate scenarios
4. **Documentation Agent**: Create HLD → Generate diagrams → Format deliverables

**Each agent outputs to the next in a linear pipeline managed by the Orchestrator.**

---

## 💻 Technology Stack

### Backend
- **Language**: Python 3.11+
- **Runtime**: Azure Functions (Consumption Plan)
- **Orchestration**: Microsoft Agent Framework
- **LLM**: Azure OpenAI GPT-5 (Sweden Central)
- **Search**: Bing Search API (S1 tier, 10K queries/month)
- **API Gateway**: Azure API Management (Consumption)

### Frontend
- **Framework**: React 18+
- **Language**: TypeScript 5+
- **Hosting**: Azure App Service (B1 Basic)
- **Build Tool**: Vite or Create React App

### MCP Server (Secondary Interface)
- **Runtime**: Node.js 20 LTS
- **Language**: TypeScript
- **Protocol**: Model Context Protocol (MCP) SDK
- **Hosting**: Azure Functions (Node.js runtime)

### Data & Security
- **Authentication**: Azure AD (SSO, MFA, RBAC)
- **Secrets**: Azure Key Vault
- **Monitoring**: Application Insights + Log Analytics
- **CI/CD**: GitHub Actions

---

## 📝 Coding Standards

### Python (Backend & Agents)

**REQUIRED:**
- Python 3.11+ syntax
- PEP 8 compliant
- Black formatter (line length: 88)
- Type hints for ALL functions
- Docstrings (Google style)
- Pydantic models for data validation

**Example:**
```python
from typing import Optional
from pydantic import BaseModel, Field

class RequirementsInput(BaseModel):
    """Input schema for Requirements Agent."""
    user_input: str = Field(..., description="Raw user request")
    context: Optional[dict] = Field(None, description="Conversation context")

def extract_requirements(input_data: RequirementsInput) -> dict:
    """
    Extract structured requirements from natural language input.
    
    Args:
        input_data: User input and context
        
    Returns:
        Dictionary with extracted requirements, cloud platform, and constraints
        
    Raises:
        ValueError: If input is empty or invalid
    """
    if not input_data.user_input.strip():
        raise ValueError("Input cannot be empty")
    
    # Implementation...
    return {"requirements": [], "target_cloud": "aws"}
```

### TypeScript (Frontend & MCP)

**REQUIRED:**
- TypeScript 5+ with strict mode
- ESLint + Prettier
- Explicit return types
- Interface definitions for all data structures
- camelCase for variables, PascalCase for classes/interfaces

**Example:**
```typescript
interface ArchitectureRequest {
  requirements: string;
  targetCloud: 'aws' | 'gcp' | 'azure' | 'oracle';
  region?: string;
}

interface ArchitectureResponse {
  components: Component[];
  diagram: string;
  citations: Citation[];
}

async function generateArchitecture(
  request: ArchitectureRequest
): Promise<ArchitectureResponse> {
  // Implementation...
}
```

### Error Handling

**Always include proper error handling:**
```python
from typing import Union
from pydantic import ValidationError

def safe_agent_call(agent_fn, *args) -> Union[dict, None]:
    """Wrap agent calls with error handling and retries."""
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            result = agent_fn(*args)
            return result
        except ValidationError as e:
            print(f"Validation error: {e}")
            raise  # Don't retry validation errors
        except Exception as e:
            if attempt < max_retries:
                print(f"Retry {attempt + 1}/{max_retries} after error: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Failed after {max_retries} retries: {e}")
                return None
```

---

## 🧪 Testing Standards

### Unit Tests (Required for All Agents)

```python
# tests/unit/test_requirements_agent.py
import pytest
from src.agents.requirements_agent import RequirementsAgent

def test_detect_aws_from_explicit_mention():
    agent = RequirementsAgent()
    result = agent.detect_cloud("Build an AWS Lambda function")
    assert result == "aws"

def test_detect_azure_from_service_name():
    agent = RequirementsAgent()
    result = agent.detect_cloud("Need App Service for web hosting")
    assert result == "azure"

@pytest.mark.parametrize("input_text,expected_cloud", [
    ("EC2 instances", "aws"),
    ("Compute Engine VMs", "gcp"),
    ("Virtual Machines", "azure"),
])
def test_cloud_detection_parametrized(input_text, expected_cloud):
    agent = RequirementsAgent()
    assert agent.detect_cloud(input_text) == expected_cloud
```

### Integration Tests

```python
# tests/integration/test_orchestrator.py
import pytest

@pytest.mark.integration
async def test_full_workflow():
    """Test complete workflow from input to documentation."""
    orchestrator = MasterOrchestrator()
    
    result = await orchestrator.orchestrate(
        "Design an AWS e-commerce platform with 10k users"
    )
    
    assert result["status"] == "success"
    assert "requirements" in result
    assert "architecture" in result
    assert "costs" in result
    assert len(result["citations"]) > 0
```

### Test Coverage Target
- **Minimum**: 80% coverage for new code
- **Run**: `pytest --cov=src --cov-report=html`

---

## 🔑 Environment Variables

**Reference `.env.example` for complete list. Key variables:**

```bash
# Azure OpenAI (REQUIRED)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Bing Search API (REQUIRED)
BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com/v7.0/search
BING_SEARCH_API_KEY=your-bing-key
BING_SEARCH_TIER=S1

# YouTube Data API (OPTIONAL)
YOUTUBE_API_KEY=your-youtube-key

# Azure AD (REQUIRED for auth)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Feature Flags
ENABLE_MCP_INTEGRATION=true
ENABLE_RAG=false  # Always false for POC
ENABLE_COMPLIANCE_AGENT=false  # Out of scope for POC
```

---

## 📦 Project Structure

```
CoPilot-SE/
├── src/
│   ├── __init__.py
│   ├── agents/                    # 4 specialized agents
│   │   ├── __init__.py
│   │   ├── base_agent.py         # Base class for all agents
│   │   ├── requirements_agent.py  # Agent 1: Requirements extraction
│   │   ├── architecture_agent.py  # Agent 2: Multi-cloud architecture
│   │   ├── cost_agent.py          # Agent 3: Cost estimation
│   │   └── documentation_agent.py # Agent 4: Doc generation
│   ├── orchestrator/              # Master orchestrator
│   │   ├── __init__.py
│   │   └── master_orchestrator.py
│   ├── services/                  # External services
│   │   ├── bing_search.py
│   │   ├── youtube_api.py
│   │   └── openai_client.py
│   └── utils/                     # Shared utilities
│       ├── validators.py
│       └── formatters.py
├── mcp-server/                    # MCP integration (Node.js)
│   ├── src/
│   │   ├── index.ts              # MCP server entry point
│   │   ├── tools/                # MCP tool definitions
│   │   └── handlers/             # Request handlers
│   ├── package.json
│   └── tsconfig.json
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                          # Complete documentation (9 files)
├── infrastructure/                # IaC (Bicep/Terraform)
└── config/                        # YAML configs (Phase 2)
```

---

## ⚠️ Critical Constraints for Code Generation

1. **NO RAG/Vector Database**: Never generate code for embeddings, vector stores, or similarity search
2. **Online-Only Data**: Always use Bing Search API or direct HTTP requests to official docs
3. **Single Cloud at a Time**: Architecture agent handles ONE cloud per request (not multi-cloud hybrid)
4. **Stateless**: No persistent storage of customer data (use in-memory state only)
5. **4 Agents Only**: Don't create compliance, security, or other agents
6. **Azure Functions**: All backend code should be compatible with Azure Functions Python 3.11
7. **Cost Accuracy**: ±30% acceptable for POC (no cloud provider authentication)

---

## 🔗 Key Documentation References

- **Agent Specifications**: See `.copilot/agent-prompts.md` for full system prompts
- **API Schemas**: See `.copilot/api-schemas.md` for input/output contracts
- **Workflow Logic**: See `.copilot/orchestration-workflow.md` for stage-by-stage execution
- **Full Docs**: See `docs/README.md` for complete documentation index

---

## 🚀 Common Development Tasks

### Creating a New Agent Function
```python
from pydantic import BaseModel
from typing import Optional

class AgentInput(BaseModel):
    # Define input schema

class AgentOutput(BaseModel):
    # Define output schema

def agent_function(input_data: AgentInput) -> AgentOutput:
    """Agent function with proper types and error handling."""
    # Implementation
```

### Adding a New Bing Search Query
```python
from src.services.bing_search import BingSearchClient

client = BingSearchClient()
results = client.search(
    query="Azure App Service pricing calculator",
    count=10,
    market="en-US"
)
```

### Adding a New MCP Tool
```typescript
// mcp-server/src/tools/new-tool.ts
import { Tool } from '@modelcontextprotocol/sdk';

export const newTool: Tool = {
  name: 'tool_name',
  description: 'What this tool does',
  inputSchema: {
    type: 'object',
    properties: {
      // Define input
    },
  },
};
```

---

**Last Updated**: November 1, 2025  
**For Questions**: See `docs/08-open-questions.md` or create a GitHub issue
