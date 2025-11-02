# Agent Framework SDK Migration - Status Report

**Date**: November 1, 2025  
**Status**: Phase 1 Complete - SDK Installed ✅  
**Next Phase**: Client Wrapper Implementation

---

## Executive Summary

Successfully pivoted from **Azure AI Projects SDK** (low-level service API) to **Microsoft Agent Framework SDK** (modern unified framework combining Semantic Kernel + AutoGen patterns). This represents a major architectural upgrade that will provide better abstractions, multi-agent orchestration, and future-proof the codebase.

---

## What Changed

### 1. Package Installation ✅ COMPLETE

**Removed:**
- `azure-ai-projects==1.0.0b5` (old SDK)
- `azure-ai-agents==1.0.0b5` (old SDK)
- `openai==1.6.1` (outdated)
- `httpx==0.25.2` (outdated)
- `redis==5.0.1` (outdated)

**Installed:**
```bash
# Core Framework
agent-framework==1.0.0b251028
agent-framework-core==1.0.0b251028
agent-framework-azure-ai==1.0.0b251028

# Azure Integration
azure-ai-inference==1.0.0b7
azure-ai-projects==1.1.0b4 (newer version for compatibility)
azure-ai-agents==1.2.0b5 (newer version for compatibility)
azure-identity==1.25.1 (upgraded)

# Additional Capabilities
agent-framework-a2a (Agent-to-Agent communication)
agent-framework-copilotstudio (Copilot Studio integration)
agent-framework-devui (Development UI)
agent-framework-lab (Experimental features)
agent-framework-mem0 (Memory management with mem0ai)
agent-framework-redis (Redis integration)
agent-framework-purview (Purview integration)

# Dependencies
openai==1.109.1 (upgraded from 1.6.1)
httpx==0.28.1 (upgraded from 0.25.2)
redis==6.4.0 (upgraded from 5.0.1)
mcp==1.20.0 (Model Context Protocol support)
opentelemetry-* (Full observability stack)
```

### 2. Key Framework Components Now Available

**From `agent_framework`:**
- `ChatAgent` - Modern agent implementation
- `ChatClient` - Base for Azure OpenAI integration
- `HostedWebSearchTool` - Bing Grounding tool
- `WorkflowBuilder`, `SequentialBuilder`, `ConcurrentBuilder` - Orchestration
- `ai_function` decorator - Tool creation
- `AgentThread`, `ChatMessage` - Conversation management
- Middleware support (chat, agent, function)
- OpenTelemetry integration (automatic tracing)

**From `azure.ai.inference`:**
- `ChatCompletionsClient` - Azure OpenAI integration
- Model configuration and deployment management

---

## Architecture Comparison

### Old Architecture (Azure AI Projects SDK)

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import BingGroundingTool

# Low-level service API
client = AIProjectClient(
    endpoint=endpoint,
    subscription_id=subscription_id,
    resource_group_name=resource_group,
    project_name=project,
    credential=credential
)

# Create agent with service-level calls
agent = client.agents.create_agent(
    model="gpt-4",
    name="my-agent",
    instructions="...",
    tools=bing_tool.definitions
)

# Execute with threads
thread = client.agents.create_thread()
message = client.agents.create_message(thread_id=thread.id, ...)
run = client.agents.create_run(thread_id=thread.id, agent_id=agent.id)
```

**Problems:**
- ❌ Low-level, verbose API
- ❌ Manual thread management
- ❌ No built-in orchestration patterns
- ❌ Limited middleware/extensibility
- ❌ No multi-agent coordination
- ❌ Unclear Bing tool integration

### New Architecture (Agent Framework SDK)

```python
from agent_framework import ChatAgent, HostedWebSearchTool, SequentialBuilder
from azure.ai.inference import ChatCompletionsClient
from azure.identity import DefaultAzureCredential

# High-level framework approach
chat_client = ChatCompletionsClient(
    endpoint="https://your-openai.openai.azure.com/",
    credential=DefaultAzureCredential(),
    model="gpt-4"
)

# Create agent with tools
requirements_agent = ChatAgent(
    chat_client=chat_client,
    name="requirements-agent",
    instructions="Extract requirements...",
    # No tools needed for this agent
)

architecture_agent = ChatAgent(
    chat_client=chat_client,
    name="architecture-agent",
    instructions="Design cloud architecture...",
    tools=[HostedWebSearchTool(connection_id=bing_connection_id)]
)

# Sequential workflow orchestration
workflow = SequentialBuilder() \
    .participants([requirements_agent, architecture_agent, cost_agent, doc_agent]) \
    .build()

# Execute workflow
result = await workflow.run("Design an AWS e-commerce platform")
```

**Benefits:**
- ✅ High-level, clean API
- ✅ Automatic thread/conversation management
- ✅ Built-in orchestration (Sequential, Concurrent, Switch-Case)
- ✅ Middleware pipeline (logging, auth, caching)
- ✅ Multi-agent coordination via workflows
- ✅ MCP (Model Context Protocol) support
- ✅ OpenTelemetry tracing built-in
- ✅ Semantic Kernel + AutoGen patterns

---

## Migration Path

### Phase 1: ✅ COMPLETE - SDK Installation
- [x] Install Agent Framework SDK with Azure support
- [x] Verify all dependencies installed correctly
- [x] Update requirements.txt

### Phase 2: 🔄 IN PROGRESS - Client Wrapper
- [ ] **Create new `src/services/agent_framework_client.py`**
  - Replace `AzureAgentClient` with `AgentFrameworkClient`
  - Use `ChatCompletionsClient` from `azure.ai.inference`
  - Implement `create_agent()` method using `ChatAgent`
  - Configure `HostedWebSearchTool` for Bing integration
  - Add method to create workflows

### Phase 3: Testing Infrastructure
- [ ] **Update `scripts/test_azure_connection.py`**
  - Test Azure OpenAI connection via `ChatCompletionsClient`
  - Test `ChatAgent` creation (without tools)
  - Test `ChatAgent` with `HostedWebSearchTool` (Bing)
  - Test simple agent execution
  - Verify OpenTelemetry tracing

### Phase 4: Agent Refactoring
- [ ] **Requirements Agent** (no tools needed)
  ```python
  requirements_agent = ChatAgent(
      chat_client=chat_client,
      name="requirements-agent",
      instructions=REQUIREMENTS_PROMPT,
  )
  ```

- [ ] **Architecture Agent** (needs Bing)
  ```python
  architecture_agent = ChatAgent(
      chat_client=chat_client,
      name="architecture-agent",
      instructions=ARCHITECTURE_PROMPT,
      tools=[HostedWebSearchTool(connection_id=bing_connection_id)]
  )
  ```

- [ ] **Cost Agent** (needs Bing)
- [ ] **Documentation Agent** (no tools needed)

### Phase 5: Orchestrator Refactoring
- [ ] **Replace `MasterOrchestrator` with Workflow**
  ```python
  workflow = SequentialBuilder() \
      .participants([
          requirements_agent,
          architecture_agent,
          cost_agent,
          documentation_agent
      ]) \
      .build()
  
  result = await workflow.run(user_input)
  ```

### Phase 6: Testing & Validation
- [ ] Update unit tests (mock `ChatAgent` instead of OpenAI)
- [ ] Update integration tests
- [ ] End-to-end testing
- [ ] Verify citations/annotations from Bing tool

### Phase 7: API Updates
- [ ] Update FastAPI endpoints to use new workflow
- [ ] Update React frontend if needed
- [ ] Update documentation

---

## Critical Next Steps

### IMMEDIATE (Do Next)

**1. Create Agent Framework Client Wrapper**

File: `src/services/agent_framework_client.py`

```python
"""
Agent Framework client wrapper for Co-Pilot SE.
Replaces azure_agent_client.py with modern Agent Framework SDK.
"""

from typing import Optional
from agent_framework import ChatAgent, HostedWebSearchTool
from azure.ai.inference import ChatCompletionsClient
from azure.identity import DefaultAzureCredential
import os


class AgentFrameworkClient:
    """Wrapper for Agent Framework SDK operations."""
    
    def __init__(self):
        """Initialize Agent Framework client with Azure OpenAI."""
        # Azure OpenAI configuration
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4")
        self.bing_connection_id = os.getenv("BING_CONNECTION_ID")
        
        # Create Azure OpenAI chat client
        self.credential = DefaultAzureCredential()
        self.chat_client = ChatCompletionsClient(
            endpoint=self.openai_endpoint,
            credential=self.credential,
            model=self.model_deployment
        )
    
    def create_agent(
        self,
        name: str,
        instructions: str,
        enable_bing: bool = False,
    ) -> ChatAgent:
        """
        Create a ChatAgent with specified configuration.
        
        Args:
            name: Agent name
            instructions: System prompt for the agent
            enable_bing: Whether to enable Bing Grounding for web search
            
        Returns:
            ChatAgent: Configured agent instance
        """
        tools = []
        
        if enable_bing:
            # Add Bing web search tool
            bing_tool = HostedWebSearchTool(connection_id=self.bing_connection_id)
            tools.append(bing_tool)
        
        # Create chat agent
        agent = ChatAgent(
            chat_client=self.chat_client,
            name=name,
            instructions=instructions,
            tools=tools if tools else None,
        )
        
        return agent
```

**2. Update Test Script**

File: `scripts/test_agent_framework.py` (new file)

Create a new test script to verify Agent Framework integration:

```python
#!/usr/bin/env python3
"""
Test Agent Framework SDK integration.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.services.agent_framework_client import AgentFrameworkClient


def test_client_initialization():
    """Test 1: Initialize Agent Framework client."""
    print("=" * 60)
    print("TEST 1: Agent Framework Client Initialization")
    print("=" * 60)
    
    try:
        client = AgentFrameworkClient()
        print("✓ Client initialized successfully")
        print(f"  OpenAI Endpoint: {client.openai_endpoint}")
        print(f"  Model: {client.model_deployment}")
        print()
        return True, client
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False, None


def test_simple_agent():
    """Test 2: Create agent without tools."""
    print("=" * 60)
    print("TEST 2: Simple Agent (No Tools)")
    print("=" * 60)
    
    try:
        client = AgentFrameworkClient()
        agent = client.create_agent(
            name="test-agent",
            instructions="You are a test agent.",
            enable_bing=False
        )
        print("✓ Agent created successfully")
        print(f"  Agent name: {agent.name}")
        print()
        return True, agent
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False, None


def test_bing_agent():
    """Test 3: Create agent with Bing tool."""
    print("=" * 60)
    print("TEST 3: Agent with Bing Grounding")
    print("=" * 60)
    
    try:
        client = AgentFrameworkClient()
        agent = client.create_agent(
            name="bing-agent",
            instructions="You are a test agent with web search.",
            enable_bing=True
        )
        print("✓ Agent with Bing created successfully")
        print(f"  Agent name: {agent.name}")
        print(f"  Tools: {len(agent.tools) if hasattr(agent, 'tools') else 0}")
        print()
        return True, agent
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False, None


async def test_agent_execution():
    """Test 4: Execute simple agent query."""
    print("=" * 60)
    print("TEST 4: Agent Execution")
    print("=" * 60)
    
    try:
        client = AgentFrameworkClient()
        agent = client.create_agent(
            name="test-agent",
            instructions="You are a helpful assistant.",
            enable_bing=False
        )
        
        # Execute agent
        result = await agent.run("Say hello!")
        
        print("✓ Agent executed successfully")
        print(f"  Response: {result.messages[-1].text if result.messages else 'No response'}")
        print()
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    
    print("\n")
    print("=" * 60)
    print("AGENT FRAMEWORK SDK TEST SUITE")
    print("=" * 60)
    print()
    
    # Run tests
    success1, client = test_client_initialization()
    success2, agent = test_simple_agent()
    success3, bing_agent = test_bing_agent()
    success4 = asyncio.run(test_agent_execution())
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    tests = [
        ("Client Initialization", success1),
        ("Simple Agent Creation", success2),
        ("Bing Agent Creation", success3),
        ("Agent Execution", success4),
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    print()
    
    sys.exit(0 if passed == total else 1)
```

---

## Key Concepts - Agent Framework

### 1. ChatAgent
- Primary agent implementation
- Wraps a `ChatClient` (Azure OpenAI)
- Supports tools, middleware, context providers
- Automatic conversation management

### 2. Tools
- `HostedWebSearchTool` - Bing Grounding (your use case)
- `HostedFileSearchTool` - File search
- `HostedCodeInterpreterTool` - Code execution
- `MCPStdioTool`, `MCPWebsocketTool` - MCP integration
- `@ai_function` decorator - Custom tools

### 3. Workflows
- **SequentialBuilder** - Linear pipeline (your current need)
- **ConcurrentBuilder** - Parallel execution
- **SwitchCaseBuilder** - Conditional routing
- Support checkpointing, resumption, state management

### 4. Middleware
- **Chat Middleware** - Intercept chat requests
- **Agent Middleware** - Wrap agent invocations
- **Function Middleware** - Tool call interception
- Use cases: logging, caching, auth, rate limiting

### 5. Observability
- Built-in OpenTelemetry integration
- Automatic trace/span creation
- Azure Monitor integration
- Full request/response logging

---

## Environment Variables

**Update your `.env` file:**

```bash
# Azure OpenAI (UPDATED KEY NAMES)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
MODEL_DEPLOYMENT_NAME=gpt-5
AZURE_OPENAI_API_KEY=your-key  # Fallback if DefaultAzureCredential fails

# Bing Connection (SAME)
BING_CONNECTION_ID=/subscriptions/.../connections/bing-copilot-se

# Azure Authentication (SAME)
AZURE_TENANT_ID=5aa7c6e1-452d-4ddb-b6b5-85675861b60a
AZURE_SUBSCRIPTION_ID=7aa77d2e-cbec-48b4-8518-9802543b25af
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Azure AI Foundry (MAY NOT BE NEEDED ANYMORE)
# AZURE_AI_PROJECT=https://copilot-se-foundry.services.ai.azure.com/api/projects/se-project
```

**Note**: Agent Framework uses Azure OpenAI directly, not AI Foundry project endpoint.

---

## Breaking Changes

### What No Longer Works

1. **Old Client**:
   ```python
   from src.services.azure_agent_client import AzureAgentClient  # ❌ OLD
   ```
   
   **New**:
   ```python
   from src.services.agent_framework_client import AgentFrameworkClient  # ✅ NEW
   ```

2. **Thread Management**:
   ```python
   thread = client.agents.create_thread()  # ❌ OLD - Manual
   ```
   
   **New**:
   ```python
   # ✅ NEW - Automatic via ChatAgent
   result = await agent.run("Your query")
   ```

3. **Tool Creation**:
   ```python
   from azure.ai.projects.models import BingGroundingTool  # ❌ OLD
   bing_tool = BingGroundingTool(connection_id=...)
   tools = bing_tool.definitions
   ```
   
   **New**:
   ```python
   from agent_framework import HostedWebSearchTool  # ✅ NEW
   tool = HostedWebSearchTool(connection_id=...)
   tools = [tool]  # Direct list
   ```

4. **Orchestration**:
   ```python
   # ❌ OLD - Manual sequential calls
   req_output = requirements_agent.extract_requirements(input)
   arch_output = architecture_agent.design_architecture(req_output)
   cost_output = cost_agent.estimate_costs(arch_output)
   ```
   
   **New**:
   ```python
   # ✅ NEW - Workflow builder
   workflow = SequentialBuilder().participants([
       requirements_agent, architecture_agent, cost_agent
   ]).build()
   result = await workflow.run(user_input)
   ```

---

## Migration Checklist

### Phase 2: Client Wrapper (NEXT)
- [ ] Create `src/services/agent_framework_client.py`
- [ ] Implement `AgentFrameworkClient.__init__()`
- [ ] Implement `create_agent()` method
- [ ] Test Azure OpenAI connection
- [ ] Test agent creation without tools
- [ ] Test agent creation with Bing tool
- [ ] Test simple agent execution

### Phase 3: Agent Refactoring
- [ ] Refactor Requirements Agent
- [ ] Refactor Architecture Agent (with Bing)
- [ ] Refactor Cost Agent (with Bing)
- [ ] Refactor Documentation Agent
- [ ] Update agent prompts if needed

### Phase 4: Orchestrator
- [ ] Create workflow using SequentialBuilder
- [ ] Update MasterOrchestrator to use workflow
- [ ] Make orchestrate() async
- [ ] Test end-to-end execution

### Phase 5: Testing
- [ ] Update unit tests
- [ ] Update integration tests
- [ ] Test citation extraction
- [ ] Verify Bing search results

### Phase 6: API & Frontend
- [ ] Update FastAPI endpoints
- [ ] Update React frontend (if needed)
- [ ] Update documentation
- [ ] Deploy and test

---

## Documentation References

- **Agent Framework API**: https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework
- **Azure AI Inference**: https://learn.microsoft.com/en-us/python/api/azure-ai-inference
- **ChatAgent Guide**: https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/quick-start
- **Workflows**: https://learn.microsoft.com/en-us/agent-framework/concepts/workflows

---

## Success Criteria

**Phase 2 Complete When:**
- ✅ `AgentFrameworkClient` created
- ✅ Can create `ChatAgent` without tools
- ✅ Can create `ChatAgent` with `HostedWebSearchTool`
- ✅ Simple test query executes successfully
- ✅ OpenTelemetry traces visible (optional)

**Full Migration Complete When:**
- ✅ All 4 agents refactored to use `ChatAgent`
- ✅ Orchestrator uses `SequentialBuilder` workflow
- ✅ All 35 tests passing
- ✅ Web portal functional
- ✅ Bing search citations working
- ✅ End-to-end workflow executes successfully

---

## Questions / Decisions Needed

1. **Model Deployment**: Confirm `gpt-5` is deployed in your Azure OpenAI resource
2. **Bing Connection Format**: Verify `BING_CONNECTION_ID` format is correct
3. **Error Handling**: Decide on retry strategy (Agent Framework has built-in support)
4. **Observability**: Enable Azure Monitor OpenTelemetry? (already installed)
5. **MCP Integration**: Should we enable MCP server for external integrations?

---

## Risk Assessment

**LOW RISK:**
- ✅ Agent Framework is Microsoft's official SDK
- ✅ Backward compatible with azure-ai-projects (newer version installed)
- ✅ All dependencies installed successfully
- ✅ Clear migration path

**MEDIUM RISK:**
- ⚠️ `HostedWebSearchTool` API may differ from documentation
- ⚠️ OpenTelemetry overhead (can disable if needed)
- ⚠️ Learning curve for workflow patterns

**MITIGATION:**
- Test each component incrementally
- Keep old code until migration verified
- Use test script to validate each step
- Refer to official docs and examples

---

## Summary

**What's Done:**
✅ Agent Framework SDK installed and ready
✅ Modern unified framework (Semantic Kernel + AutoGen)
✅ All dependencies resolved
✅ Migration path defined

**What's Next:**
1. Create `AgentFrameworkClient` wrapper
2. Test basic agent creation and execution
3. Refactor 4 agents to use `ChatAgent`
4. Update orchestrator with workflow pattern
5. Test end-to-end

**Estimated Effort:**
- Phase 2 (Client): 1-2 hours
- Phase 3 (Testing): 30 minutes
- Phase 4 (Agents): 2-3 hours
- Phase 5 (Orchestrator): 1-2 hours
- Phase 6 (Testing): 1-2 hours
- **Total**: 6-10 hours

---

**Ready to proceed with Phase 2?** Let me know and I'll create the `AgentFrameworkClient` wrapper!
