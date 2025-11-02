#!/usr/bin/env python3
"""
Test Agent Framework SDK integration.

This script validates the Agent Framework SDK setup including:
1. Client initialization
2. Simple agent creation (no tools)
3. Agent with Bing Grounding tool
4. Agent execution
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.services.agent_framework_client import AgentFrameworkClient


def test_environment_variables():
    """Test 1: Verify environment variables."""
    print("=" * 60)
    print("TEST 1: Environment Variables")
    print("=" * 60)
    
    required_vars = {
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "MODEL_DEPLOYMENT_NAME": os.getenv("MODEL_DEPLOYMENT_NAME"),
        "BING_CONNECTION_ID": os.getenv("BING_CONNECTION_ID"),
    }
    
    all_set = True
    for var, value in required_vars.items():
        if value:
            print(f"✓ {var}: {value[:50]}...")
        else:
            print(f"✗ {var}: NOT SET")
            all_set = False
    
    print()
    return all_set


def test_client_initialization():
    """Test 2: Initialize Agent Framework client."""
    print("=" * 60)
    print("TEST 2: Agent Framework Client Initialization")
    print("=" * 60)
    
    try:
        client = AgentFrameworkClient()
        print("✓ Client initialized successfully")
        print(f"  OpenAI Endpoint: {client.openai_endpoint}")
        print(f"  Model: {client.model_deployment}")
        print(f"  Bing Connection: {'Configured' if client.bing_connection_id else 'Not configured'}")
        print()
        return True, client
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        print()
        return False, None


def test_simple_agent():
    """Test 3: Create agent without tools."""
    print("=" * 60)
    print("TEST 3: Simple Agent (No Tools)")
    print("=" * 60)
    
    try:
        client = AgentFrameworkClient()
        agent = client.create_agent(
            name="test-agent",
            instructions="You are a helpful test agent.",
            enable_bing=False
        )
        print("✓ Agent created successfully")
        print(f"  Agent name: {agent.name}")
        print(f"  Model: {agent.model if hasattr(agent, 'model') else 'N/A'}")
        print(f"  Tools: {len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0}")
        print()
        return True, agent
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False, None


def test_bing_agent():
    """Test 4: Create agent with Bing tool."""
    print("=" * 60)
    print("TEST 4: Agent with Bing Grounding")
    print("=" * 60)
    
    try:
        client = AgentFrameworkClient()
        agent = client.create_agent(
            name="bing-agent",
            instructions="You are a test agent with web search capabilities.",
            enable_bing=True
        )
        print("✓ Agent with Bing created successfully")
        print(f"  Agent name: {agent.name}")
        print(f"  Model: {agent.model if hasattr(agent, 'model') else 'N/A'}")
        print(f"  Tools: {len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0}")
        print()
        return True, agent
    except Exception as e:
        print(f"✗ Failed to create agent with Bing: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False, None


async def test_agent_execution():
    """Test 5: Execute simple agent query."""
    print("=" * 60)
    print("TEST 5: Agent Execution")
    print("=" * 60)
    
    try:
        client = AgentFrameworkClient()
        agent = client.create_agent(
            name="test-agent",
            instructions="You are a helpful assistant. Keep responses very brief.",
            enable_bing=False
        )
        
        print("Executing agent with query: 'Say hello in one word'")
        
        # Execute agent
        result = await agent.run("Say hello in one word")
        
        # Extract response
        if hasattr(result, 'messages') and result.messages:
            response_text = result.messages[-1].text if hasattr(result.messages[-1], 'text') else str(result.messages[-1])
        else:
            response_text = str(result)
        
        print("✓ Agent executed successfully")
        print(f"  Response: {response_text[:100]}")
        print()
        return True
    except Exception as e:
        print(f"✗ Failed to execute agent: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def test_bing_agent_execution():
    """Test 6: Execute agent with Bing search."""
    print("=" * 60)
    print("TEST 6: Agent Execution with Bing")
    print("=" * 60)
    
    try:
        client = AgentFrameworkClient()
        agent = client.create_agent(
            name="bing-search-agent",
            instructions="You are a helpful assistant with web search. Answer questions using current information from the web.",
            enable_bing=True
        )
        
        print("Executing agent with query: 'What is the current date?'")
        
        # Execute agent
        result = await agent.run("What is the current date? Be very brief.")
        
        # Extract response
        if hasattr(result, 'messages') and result.messages:
            response_text = result.messages[-1].text if hasattr(result.messages[-1], 'text') else str(result.messages[-1])
        else:
            response_text = str(result)
        
        print("✓ Agent with Bing executed successfully")
        print(f"  Response: {response_text[:150]}")
        
        # Check for citations
        if hasattr(result, 'messages') and result.messages:
            last_msg = result.messages[-1]
            if hasattr(last_msg, 'annotations') and last_msg.annotations:
                print(f"  Citations: {len(last_msg.annotations)} found")
        
        print()
        return True
    except Exception as e:
        print(f"✗ Failed to execute agent with Bing: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("=" * 60)
    print("AGENT FRAMEWORK SDK TEST SUITE")
    print("=" * 60)
    print()
    
    # Test 1: Environment variables
    success1 = test_environment_variables()
    
    # Test 2: Client initialization
    success2, client = test_client_initialization()
    
    # Test 3: Simple agent
    success3, agent = test_simple_agent()
    
    # Test 4: Bing agent
    success4, bing_agent = test_bing_agent()
    
    # Test 5: Agent execution (async)
    success5 = asyncio.run(test_agent_execution())
    
    # Test 6: Bing agent execution (async)
    success6 = asyncio.run(test_bing_agent_execution())
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    tests = [
        ("Environment Variables", success1),
        ("Client Initialization", success2),
        ("Simple Agent Creation", success3),
        ("Bing Agent Creation", success4),
        ("Agent Execution", success5),
        ("Bing Agent Execution", success6),
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Agent Framework SDK is ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
    
    print()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
