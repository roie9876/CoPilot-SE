# Azure AI Agent Service Migration Guide

**Status:** IN PROGRESS  
**Date:** November 1, 2025  
**Author:** GitHub Copilot  
**Version:** 1.0

---

## 🎯 Executive Summary

This document outlines the migration from **direct Bing Search API calls** to **Azure AI Agent Service** with integrated **Grounding with Bing Search** tool. This is a **required architectural change** to align with Microsoft's current Azure AI platform.

### Why This Migration is Required

1. **Bing Search API is deprecated** for direct use
2. **Azure AI Foundry** now requires integration through Agent Service
3. **Better integration** with Azure OpenAI and other AI services
4. **Automatic tool selection** - agents decide when to search
5. **Built-in citation handling** and compliance with Bing's display requirements
6. **Production-ready architecture** recommended by Microsoft

---

## 📋 Migration Overview

### Before (Current - INCORRECT)

```
User Input
    ↓
MasterOrchestrator
    ↓
Requirements Agent ──→ Direct OpenAI API calls
Architecture Agent ──→ Direct OpenAI API + Direct Bing HTTP requests ❌
Cost Agent ─────────→ Direct OpenAI API + Direct Bing HTTP requests ❌
Documentation Agent ─→ Direct OpenAI API
    ↓
OrchestratorOutput
```

**Problems:**
- Direct HTTP requests to Bing API (deprecated)
- Manual citation handling
- No automatic tool selection
- Not compliant with Azure AI Foundry architecture

### After (Target - CORRECT)

```
User Input
    ↓
MasterOrchestrator (Thread-based)
    ↓
Azure AI Agent Service (AIProjectClient)
    ├─ Requirements Agent (Azure AI Agent)
    ├─ Architecture Agent (Azure AI Agent + BingGroundingTool) ✅
    ├─ Cost Agent (Azure AI Agent + BingGroundingTool) ✅
    └─ Documentation Agent (Azure AI Agent)
    ↓
OrchestratorOutput
```

**Benefits:**
- Proper Azure AI Agent Service integration
- Automatic Bing Search through tools
- Built-in citation handling
- Compliant with Microsoft architecture
- Production-ready

---

## 🏗️ Architecture Changes

### 1. New Components

#### A. Azure AI Agent Service Client (`src/services/azure_agent_client.py`)

**Purpose:** Centralized client for creating and managing Azure AI Agents

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import BingGroundingTool

class AzureAgentClient:
    """Wrapper for Azure AI Agent Service operations."""
    
    def __init__(self):
        self.project_endpoint = os.environ["AZURE_AI_PROJECT"]
        self.credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=self.credential
        )
        
    def create_agent_with_bing(
        self,
        name: str,
        instructions: str,
        model: str,
        bing_connection_id: Optional[str] = None
    ):
        """Create an agent with Bing Grounding tool attached."""
        tools = []
        
        if bing_connection_id:
            bing_tool = BingGroundingTool(connection_id=bing_connection_id)
            tools = bing_tool.definitions
            
        return self.client.agents.create_agent(
            model=model,
            name=name,
            instructions=instructions,
            tools=tools
        )
```

#### B. Modified Agent Pattern

**Before:**
```python
class ArchitectureAgent:
    def generate_architecture(self, input: ArchitectureInput) -> ArchitectureOutput:
        # Direct OpenAI call
        response = openai_client.chat.completions.create(...)
        
        # Direct Bing search
        search_results = bing_client.search("Azure App Service pricing")
        
        return ArchitectureOutput(...)
```

**After:**
```python
class ArchitectureAgent:
    def __init__(self, azure_client: AzureAgentClient):
        self.azure_client = azure_client
        self.agent = self._create_agent()
        
    def _create_agent(self):
        return self.azure_client.create_agent_with_bing(
            name="architecture-agent",
            instructions="You are a cloud architecture expert...",
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            bing_connection_id=os.environ["BING_CONNECTION_ID"]
        )
        
    async def generate_architecture(
        self, 
        input: ArchitectureInput
    ) -> ArchitectureOutput:
        # Create thread
        thread = self.azure_client.client.agents.threads.create()
        
        # Create message
        message = self.azure_client.client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=self._build_prompt(input)
        )
        
        # Run agent (automatically uses Bing when needed)
        run = self.azure_client.client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=self.agent.id
        )
        
        # Extract results
        messages = self.azure_client.client.agents.messages.list(
            thread_id=thread.id
        )
        
        return self._parse_output(messages)
```

### 2. Removed Components

- ❌ `src/services/bing_search.py` - **DELETE** (replaced by BingGroundingTool)
- ❌ Direct HTTP requests to Bing API
- ❌ Manual citation extraction from Bing results

### 3. Modified Components

| Component | Changes Required |
|-----------|-----------------|
| **requirements.txt** | Add `azure-ai-projects`, `azure-ai-agents`; Remove `azure-cognitiveservices-search-websearch` |
| **requirements_agent.py** | Convert to Azure AI Agent (no Bing tool needed) |
| **architecture_agent.py** | Convert to Azure AI Agent + BingGroundingTool |
| **cost_agent.py** | Convert to Azure AI Agent + BingGroundingTool |
| **documentation_agent.py** | Convert to Azure AI Agent (no Bing tool needed) |
| **master_orchestrator.py** | Use thread-based execution instead of direct calls |
| **.env / .env.example** | Add `AZURE_AI_PROJECT`, `BING_CONNECTION_ID` |

---

## 🔧 Implementation Steps

### Step 1: Azure Portal Setup (PREREQUISITE)

**You must complete this BEFORE running the refactored code.**

#### 1.1 Create Grounding with Bing Search Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Create a resource**
3. Search for **"Grounding with Bing Search"**
4. Click **Create**
5. Fill in the form:
   - **Subscription:** Your Azure subscription
   - **Resource Group:** Same as your AI Foundry project (e.g., `copilot-se-rg`)
   - **Region:** Sweden Central (or same as your AI Foundry)
   - **Name:** `copilot-se-bing-grounding`
   - **Pricing Tier:** S1 (10,000 queries/month)
6. Click **Review + Create** → **Create**
7. Wait for deployment to complete

#### 1.2 Connect Bing Resource to AI Foundry Project

1. Go to [Azure AI Foundry Portal](https://ai.azure.com)
2. Navigate to your project: **copilot-se-foundry**
3. Click **Connected resources** in left sidebar
4. Click **+ Add connection**
5. Select **Grounding with Bing Search**
6. Select your newly created resource: `copilot-se-bing-grounding`
7. Name the connection: `bing-grounding-connection`
8. Click **Add connection**
9. **Copy the Connection ID** (format: `/subscriptions/.../connections/bing-grounding-connection`)

#### 1.3 Get Azure AI Project Endpoint

1. In Azure AI Foundry Portal, go to your project
2. Click **Settings** → **Project details**
3. Copy the **Project endpoint URL** (format: `https://<name>.services.ai.azure.com/api/projects/<project-id>`)

### Step 2: Update Environment Variables

Update `.env` with new variables:

```bash
# =============================================================================
# AZURE AI FOUNDRY PROJECT
# =============================================================================
AZURE_AI_PROJECT=https://copilot-se-foundry.services.ai.azure.com/api/projects/<your-project-id>

# =============================================================================
# BING GROUNDING CONNECTION
# =============================================================================
BING_CONNECTION_ID=/subscriptions/<sub-id>/resourceGroups/copilot-se-rg/providers/Microsoft.CognitiveServices/accounts/copilot-se-foundry/projects/<project-name>/connections/bing-grounding-connection

# =============================================================================
# AZURE AUTHENTICATION (Required for DefaultAzureCredential)
# =============================================================================
# Make sure you're logged in: az login
# Or set these for service principal:
# AZURE_TENANT_ID=<tenant-id>
# AZURE_CLIENT_ID=<client-id>
# AZURE_CLIENT_SECRET=<client-secret>
```

### Step 3: Update Python Dependencies

```bash
# Remove old package
pip uninstall azure-cognitiveservices-search-websearch -y

# Install Azure AI Agent Service
pip install azure-ai-projects azure-ai-agents

# Update requirements.txt
# (Done automatically by script below)
```

### Step 4: Run Migration Script

```bash
# Execute the migration
python scripts/migrate_to_azure_agent_service.py

# This script will:
# 1. Update requirements.txt
# 2. Create AzureAgentClient wrapper
# 3. Refactor all 4 agents
# 4. Update orchestrator
# 5. Update tests
```

### Step 5: Authenticate to Azure

```bash
# Login to Azure CLI (required for DefaultAzureCredential)
az login

# Set subscription (if you have multiple)
az account set --subscription <subscription-id>
```

### Step 6: Test the Migration

```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests (requires real Azure resources)
pytest tests/integration/ -v

# Test complete workflow
python -m pytest tests/e2e/test_full_workflow.py -v
```

### Step 7: Update Documentation

Update these files:
- `README.md` - Add Azure AI Agent Service setup instructions
- `QUICKSTART.md` - Update prerequisites
- `.copilot/agent-prompts.md` - Update agent architecture descriptions

---

## 📦 Dependency Changes

### requirements.txt Changes

**Remove:**
```diff
- azure-cognitiveservices-search-websearch==2.0.0
```

**Add:**
```diff
+ azure-ai-projects==1.0.0
+ azure-ai-agents==1.0.0
```

### Full Updated Dependencies

```python
# Azure AI Agent Service (NEW)
azure-ai-projects==1.0.0
azure-ai-agents==1.0.0

# Azure Core (keep existing)
azure-identity==1.15.0
azure-functions==1.18.0
azure-core==1.29.5

# OpenAI (keep existing)
openai==1.6.1
tiktoken==0.5.2
```

---

## 🔄 Code Migration Patterns

### Pattern 1: Agent Initialization

**Before:**
```python
from openai import AzureOpenAI
from ..services.bing_search import BingSearchClient

class ArchitectureAgent:
    def __init__(self):
        self.openai_client = AzureOpenAI(...)
        self.bing_client = BingSearchClient()
```

**After:**
```python
from ..services.azure_agent_client import AzureAgentClient

class ArchitectureAgent:
    def __init__(self, azure_client: AzureAgentClient):
        self.azure_client = azure_client
        self.agent = self._create_agent()
        
    def _create_agent(self):
        return self.azure_client.create_agent_with_bing(
            name="architecture-agent",
            instructions="You are a cloud architecture expert...",
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            bing_connection_id=os.environ["BING_CONNECTION_ID"]
        )
```

### Pattern 2: Agent Execution

**Before:**
```python
async def generate_architecture(self, input: ArchitectureInput):
    # Manual prompt construction
    prompt = f"Design architecture for: {input.requirements}"
    
    # Direct OpenAI call
    response = await self.openai_client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Manual Bing search
    search_results = self.bing_client.search_cloud_docs(
        query=f"{input.target_cloud} services",
        cloud_provider=input.target_cloud
    )
    
    # Manual parsing
    return ArchitectureOutput(...)
```

**After:**
```python
async def generate_architecture(self, input: ArchitectureInput):
    # Create thread for this task
    thread = self.azure_client.client.agents.threads.create()
    
    # Create user message
    prompt = self._build_prompt(input)
    message = self.azure_client.client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )
    
    # Run agent (automatically uses Bing when needed)
    run = self.azure_client.client.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=self.agent.id
    )
    
    # Check status
    if run.status == "failed":
        raise AgentException(f"Agent run failed: {run.last_error}")
        
    # Get messages (includes agent's response with citations)
    messages = self.azure_client.client.agents.messages.list(
        thread_id=thread.id
    )
    
    # Parse output (citations are automatic)
    return self._parse_agent_response(messages)
```

### Pattern 3: Citation Handling

**Before:**
```python
# Manual citation extraction
citations = []
for result in search_results:
    citations.append(Citation(
        title=result["name"],
        url=result["url"],
        source_type="bing_search",
        snippet=result.get("snippet", "")
    ))
```

**After:**
```python
# Automatic citations from agent
# Azure AI Agent Service includes citations in the response
# Access them from message annotations:
for message in messages:
    if message.role == "assistant":
        for content in message.content:
            if hasattr(content, 'annotations'):
                for annotation in content.annotations:
                    # Bing citations are automatically included
                    citations.append(Citation(
                        title=annotation.text,
                        url=annotation.url,
                        source_type="bing_grounding",
                        snippet=""
                    ))
```

---

## 🧪 Testing Strategy

### Unit Tests

**Update mocks to use Azure AI Agent Service:**

```python
# tests/unit/test_architecture_agent.py

from unittest.mock import Mock, AsyncMock, patch
import pytest

@pytest.fixture
def mock_azure_client():
    """Mock Azure AI Agent Service client."""
    client = Mock()
    client.client = Mock()
    client.client.agents = Mock()
    client.client.agents.threads = Mock()
    client.client.agents.messages = Mock()
    client.client.agents.runs = Mock()
    return client

@pytest.mark.asyncio
async def test_generate_architecture_with_bing(mock_azure_client):
    """Test architecture generation uses Bing tool."""
    # Setup mock
    mock_azure_client.create_agent_with_bing.return_value = Mock(id="agent-123")
    mock_azure_client.client.agents.threads.create.return_value = Mock(id="thread-123")
    
    # Create agent
    agent = ArchitectureAgent(mock_azure_client)
    
    # Test
    input_data = ArchitectureInput(
        requirements="E-commerce platform",
        target_cloud="aws",
        region="us-east-1"
    )
    
    result = await agent.generate_architecture(input_data)
    
    # Verify Bing tool was attached
    mock_azure_client.create_agent_with_bing.assert_called_once()
    call_kwargs = mock_azure_client.create_agent_with_bing.call_args[1]
    assert call_kwargs["bing_connection_id"] is not None
```

### Integration Tests

**Test with real Azure AI Agent Service:**

```python
# tests/integration/test_azure_agent_service.py

import pytest
import os

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("AZURE_AI_PROJECT"),
    reason="Requires AZURE_AI_PROJECT to be set"
)
async def test_real_bing_grounding():
    """Test real Bing grounding through Azure AI Agent Service."""
    from src.services.azure_agent_client import AzureAgentClient
    
    client = AzureAgentClient()
    
    # Create agent with Bing
    agent = client.create_agent_with_bing(
        name="test-agent",
        instructions="Answer questions using web search.",
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        bing_connection_id=os.environ["BING_CONNECTION_ID"]
    )
    
    # Create thread and message
    thread = client.client.agents.threads.create()
    message = client.client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content="What is the latest pricing for Azure App Service?"
    )
    
    # Run
    run = client.client.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id
    )
    
    # Verify
    assert run.status == "completed"
    
    messages = client.client.agents.messages.list(thread_id=thread.id)
    assert len(messages) > 1  # User message + agent response
    
    # Check for citations (Bing was used)
    assistant_message = next(m for m in messages if m.role == "assistant")
    assert len(assistant_message.content) > 0
    
    # Cleanup
    client.client.agents.delete_agent(agent.id)
```

---

## ⚠️ Breaking Changes

### 1. API Changes

**Old:** Synchronous function calls
```python
result = agent.generate_architecture(input_data)
```

**New:** Async/await required
```python
result = await agent.generate_architecture(input_data)
```

### 2. Constructor Changes

**Old:** Agents initialize their own clients
```python
agent = ArchitectureAgent()
```

**New:** Agents require AzureAgentClient
```python
azure_client = AzureAgentClient()
agent = ArchitectureAgent(azure_client)
```

### 3. Environment Variables

**New required variables:**
- `AZURE_AI_PROJECT` (required)
- `BING_CONNECTION_ID` (required for Architecture and Cost agents)

**Deprecated variables:**
- `BING_SEARCH_ENDPOINT` (no longer used)
- `BING_SEARCH_API_KEY` (no longer used)

### 4. Citation Format

**Old:** Manual citation objects from Bing results

**New:** Automatic citations from Azure AI Agent Service annotations

---

## 📊 Migration Checklist

### Pre-Migration (Azure Portal)

- [ ] Create Grounding with Bing Search resource in Azure Portal
- [ ] Connect Bing resource to AI Foundry project
- [ ] Copy Connection ID
- [ ] Copy Project endpoint URL
- [ ] Verify you have Owner/Contributor role in subscription

### Code Migration

- [ ] Update requirements.txt
- [ ] Install new packages: `azure-ai-projects`, `azure-ai-agents`
- [ ] Uninstall old package: `azure-cognitiveservices-search-websearch`
- [ ] Create `src/services/azure_agent_client.py`
- [ ] Refactor Requirements Agent
- [ ] Refactor Architecture Agent (+ Bing tool)
- [ ] Refactor Cost Agent (+ Bing tool)
- [ ] Refactor Documentation Agent
- [ ] Update Master Orchestrator
- [ ] Delete `src/services/bing_search.py`

### Configuration

- [ ] Update `.env` with new variables
- [ ] Update `.env.example` with documentation
- [ ] Run `az login` for authentication
- [ ] Set correct Azure subscription

### Testing

- [ ] Update unit test mocks
- [ ] Run unit tests: `pytest tests/unit/ -v`
- [ ] Update integration tests
- [ ] Run integration tests: `pytest tests/integration/ -v`
- [ ] Test E2E workflow
- [ ] Verify citations are included in responses

### Documentation

- [ ] Update README.md
- [ ] Update QUICKSTART.md
- [ ] Update agent prompts documentation
- [ ] Create Azure setup guide (this document)
- [ ] Update API documentation

---

## 🚧 Rollback Plan

If the migration fails, you can rollback:

```bash
# 1. Restore old requirements.txt
git checkout HEAD -- requirements.txt

# 2. Reinstall old dependencies
pip install -r requirements.txt

# 3. Restore old code
git checkout HEAD -- src/

# 4. Restore old .env
git checkout HEAD -- .env.example
```

**Note:** Keep `.env` changes separate from git.

---

## 📚 Additional Resources

- [Azure AI Agent Service Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/)
- [Grounding with Bing Search](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding)
- [Azure AI Projects Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme)
- [Azure AI Agents Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-agents-readme)
- [Azure AI Foundry Portal](https://ai.azure.com)

---

## 🆘 Troubleshooting

### Issue: "DefaultAzureCredential failed to retrieve a token"

**Solution:**
```bash
az login
az account set --subscription <subscription-id>
```

### Issue: "Connection ID not found"

**Solution:** Verify the connection was created in Azure AI Foundry Portal. Check the exact format:
```
/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>/connections/<connection-name>
```

### Issue: "Agent run failed: BingGroundingTool not configured"

**Solution:** Ensure the Bing Grounding resource is properly connected to your AI Foundry project.

### Issue: "Import error: No module named 'azure.ai.projects'"

**Solution:**
```bash
pip install azure-ai-projects azure-ai-agents
```

---

**Status:** READY TO IMPLEMENT  
**Estimated Time:** 2-3 hours  
**Risk Level:** MEDIUM (breaking changes, requires Azure setup)  
**Recommendation:** Proceed with migration for production readiness
