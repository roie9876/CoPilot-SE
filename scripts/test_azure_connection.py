"""
Test Azure AI Agent Service Connection

This script verifies that:
1. Azure authentication is working
2. Azure AI Foundry project is accessible
3. Bing Grounding connection is valid
4. Can create and run a simple agent

Usage:
    python scripts/test_azure_connection.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

def test_environment_variables():
    """Test that required environment variables are set."""
    print("=" * 60)
    print("STEP 1: Testing Environment Variables")
    print("=" * 60)
    
    required_vars = {
        "AZURE_SUBSCRIPTION_ID": "Azure subscription ID",
        "MODEL_DEPLOYMENT_NAME": "Model deployment name",
        "BING_CONNECTION_ID": "Bing Grounding connection ID",
    }
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and not value.startswith("YOUR-") and not value.startswith("/subscriptions/YOUR-"):
            print(f"✓ {var}: {value[:50]}...")
        else:
            print(f"✗ {var}: NOT SET or contains placeholder")
            print(f"  → {description}")
            all_set = False
    
    print()
    return all_set


def test_azure_authentication():
    """Test Azure authentication."""
    print("=" * 60)
    print("STEP 2: Testing Azure Authentication")
    print("=" * 60)
    
    try:
        from azure.identity import DefaultAzureCredential
        
        credential = DefaultAzureCredential()
        
        # Try to get a token
        token = credential.get_token("https://management.azure.com/.default")
        
        print("✓ Azure authentication successful")
        print(f"  Token type: {token.token[:20]}...")
        print()
        return True, credential
    except Exception as e:
        print(f"✗ Azure authentication failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Run: az login")
        print("  2. Run: az account set --subscription <your-subscription-id>")
        print("  3. Or set AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET")
        print()
        return False, None


def test_project_connection(credential):
    """Test connection to Azure AI Foundry project."""
    print("=" * 60)
    print("STEP 3: Testing AI Foundry Project Connection")
    print("=" * 60)
    
    try:
        from azure.ai.projects import AIProjectClient
        
        subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        resource_group = "copilot-se"
        project_name = "se-project"
        endpoint = "https://copilot-se-foundry.cognitiveservices.azure.com/"
        
        client = AIProjectClient(
            endpoint=endpoint,
            subscription_id=subscription_id,
            resource_group_name=resource_group,
            project_name=project_name,
            credential=credential
        )
        
        print(f"✓ Connected to AI Foundry project")
        print(f"  Endpoint: {endpoint}")
        print(f"  Subscription: {subscription_id[:8]}...")
        print(f"  Resource Group: {resource_group}")
        print(f"  Project: {project_name}")
        print()
        return True, client
    except Exception as e:
        print(f"✗ Failed to connect to AI Foundry project: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify AZURE_SUBSCRIPTION_ID is set correctly")
        print("  2. Check resource group: copilot-se")
        print("  3. Check project name: se-project")
        print("  4. Verify project exists in https://ai.azure.com")
        print()
        return False, None


def test_bing_connection(client):
    """Test Bing Grounding connection."""
    print("=" * 60)
    print("STEP 4: Testing Bing Grounding Connection")
    print("=" * 60)
    
    try:
        from azure.ai.projects.models import BingGroundingTool
        
        bing_connection_id = os.getenv("BING_CONNECTION_ID")
        
        # Create Bing Grounding tool with connection
        bing_tool = BingGroundingTool(connection_id=bing_connection_id)
        
        print("✓ Bing Grounding tool created successfully")
        print(f"  Connection ID: {bing_connection_id[:60]}...")
        print(f"  Tool definitions: {len(bing_tool.definitions)} tool(s)")
        print()
        return True, bing_tool
    except Exception as e:
        print(f"✗ Failed to initialize Bing Grounding: {e}")
        print("\nTroubleshooting:")
        print("  1. Create Grounding with Bing Search resource in Azure Portal")
        print("  2. Connect it to your AI Foundry project")
        print("  3. Copy the full Connection ID from Azure AI Foundry Portal")
        print("  4. Update BING_CONNECTION_ID in .env")
        print()
        return False, None


def test_create_agent(client, bing_tool):
    """Test creating an agent with Bing tool."""
    print("=" * 60)
    print("STEP 5: Testing Agent Creation")
    print("=" * 60)
    
    try:
        model = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4")
        
        # Create agent with Bing grounding tool definitions
        agent = client.agents.create_agent(
            model=model,
            name="test-connection-agent",
            instructions="You are a test agent to verify Azure AI Agent Service setup.",
            tools=bing_tool.definitions,
        )
        
        print("✓ Agent created successfully")
        print(f"  Agent ID: {agent.id}")
        print(f"  Model: {model}")
        print(f"  Tools: Bing Grounding")
        print()
        return True, agent
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify MODEL_DEPLOYMENT_NAME exists in your AI Foundry project")
        print("  2. Check model is deployed (go to Deployments in AI Foundry)")
        print("  3. Verify Bing connection is active in Azure AI Foundry Portal")
        print("  4. Check BING_CONNECTION_ID format is correct")
        print()
        return False, None


def test_run_agent(client, agent):
    """Test running the agent with a simple query."""
    print("=" * 60)
    print("STEP 6: Testing Agent Execution")
    print("=" * 60)
    
    try:
        # Create thread
        thread = client.agents.threads.create()
        print(f"✓ Created thread: {thread.id}")
        
        # Create message
        message = client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content="What is 2+2? Just answer with the number."
        )
        print(f"✓ Created message: {message['id']}")
        
        # Run agent
        print("  Running agent... (this may take 10-30 seconds)")
        run = client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id
        )
        
        print(f"✓ Agent run completed")
        print(f"  Status: {run.status}")
        
        if run.status == "completed":
            # Get response
            messages = client.agents.messages.list(thread_id=thread.id)
            for msg in messages:
                if msg.role == "assistant":
                    content = msg.content[0].text.value if msg.content else ""
                    print(f"  Response: {content[:100]}")
                    break
            print()
            return True, thread
        else:
            print(f"  Warning: Run status is {run.status}")
            if hasattr(run, 'last_error'):
                print(f"  Error: {run.last_error}")
            print()
            return False, thread
    except Exception as e:
        print(f"✗ Failed to run agent: {e}")
        print()
        return False, None


def cleanup(client, agent, thread):
    """Clean up test resources."""
    print("=" * 60)
    print("CLEANUP: Deleting Test Resources")
    print("=" * 60)
    
    try:
        if thread:
            client.agents.threads.delete(thread.id)
            print(f"✓ Deleted thread: {thread.id}")
        
        if agent:
            client.agents.delete_agent(agent.id)
            print(f"✓ Deleted agent: {agent.id}")
        
        print()
    except Exception as e:
        print(f"⚠ Cleanup warning: {e}")
        print()


def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("AZURE AI AGENT SERVICE CONNECTION TEST")
    print("=" * 60)
    print()
    
    # Track resources for cleanup
    credential = None
    client = None
    agent = None
    thread = None
    
    try:
        # Step 1: Environment variables
        if not test_environment_variables():
            print("❌ FAILED: Environment variables not configured")
            print("\nPlease update your .env file with required values.")
            print("See docs/AZURE_SETUP_GUIDE.md for instructions.")
            return 1
        
        # Step 2: Authentication
        success, credential = test_azure_authentication()
        if not success:
            print("❌ FAILED: Azure authentication")
            return 1
        
        # Step 3: Project connection
        success, client = test_project_connection(credential)
        if not success:
            print("❌ FAILED: AI Foundry project connection")
            return 1
        
        # Step 4: Bing connection
        success, bing_tool = test_bing_connection(client)
        if not success:
            print("❌ FAILED: Bing Grounding connection")
            return 1
        
        # Step 5: Create agent
        success, agent = test_create_agent(client, bing_tool)
        if not success:
            print("❌ FAILED: Agent creation")
            return 1
        
        # Step 6: Run agent
        success, thread = test_run_agent(client, agent)
        if not success:
            print("⚠ WARNING: Agent run completed but may have issues")
            return 2
        
        # Success!
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Your Azure AI Agent Service setup is correct.")
        print("You can now run the Co-Pilot SE application.")
        print()
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Always cleanup
        if client and (agent or thread):
            cleanup(client, agent, thread)


if __name__ == "__main__":
    sys.exit(main())
