"""
Example usage of Co-Pilot SE - Multi-Cloud Architecture Assistant

This script demonstrates how to use the MasterOrchestrator to generate
a complete cloud architecture design from natural language requirements.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import MasterOrchestrator
from src.models.schemas import OrchestratorOutput


def setup_logging():
    """Configure logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("copilot_se_example.log"),
        ],
    )


async def example_1_azure_ecommerce():
    """Example 1: Azure e-commerce platform."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Azure E-Commerce Platform")
    print("=" * 80 + "\n")
    
    user_input = """
    Design an e-commerce platform on Azure for a retail company.
    
    Requirements:
    - Support 50,000 concurrent users
    - Product catalog with search functionality
    - Shopping cart and checkout
    - Payment processing integration
    - Order tracking and notifications
    - Admin dashboard for inventory management
    
    Non-functional requirements:
    - 99.9% uptime SLA
    - Fast page load times (<2 seconds)
    - PCI DSS compliant for payment data
    - Auto-scaling based on traffic
    - Budget: $5,000-10,000/month
    """
    
    orchestrator = MasterOrchestrator(max_retries=2)
    
    try:
        print("🚀 Starting workflow...\n")
        result: OrchestratorOutput = await orchestrator.orchestrate(user_input)
        
        print("\n✅ Workflow completed successfully!\n")
        print(f"📋 Requirements Confidence: {result.requirements['confidence_score']:.0%}")
        print(f"🏗️  Services Selected: {len(result.architecture['services'])}")
        print(f"💰 Estimated Cost Range: ${result.costs['total_monthly_cost_low']:,.0f} - ${result.costs['total_monthly_cost_high']:,.0f}/month")
        print(f"⏱️  Total Duration: {result.workflow_metadata.total_duration_seconds:.2f}s")
        print(f"📚 Citations: {len(result.citations)}")
        
        # Save HLD document
        output_file = "example1_azure_ecommerce_hld.md"
        with open(output_file, "w") as f:
            f.write(result.documentation['content'])
        print(f"\n📄 HLD document saved to: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        raise


async def example_2_azure_api_backend():
    """Example 2: Azure serverless API backend."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Azure Serverless API Backend")
    print("=" * 80 + "\n")
    
    user_input = """
    I need a serverless REST API on Azure for a mobile app backend.
    
    Features:
    - User authentication and authorization
    - CRUD operations for user data
    - File upload and storage
    - Push notifications
    - Analytics and logging
    
    Constraints:
    - Serverless architecture (no VMs)
    - Cost-effective for startup (low initial traffic)
    - Must scale automatically as user base grows
    - Prefer managed services
    """
    
    orchestrator = MasterOrchestrator(max_retries=2)
    
    try:
        print("🚀 Starting workflow...\n")
        result: OrchestratorOutput = await orchestrator.orchestrate(user_input)
        
        print("\n✅ Workflow completed successfully!\n")
        print(f"📋 Target Cloud: {result.requirements['target_cloud'].upper()}")
        print(f"🏗️  Architecture Pattern: Serverless")
        print(f"💰 LOW Scenario Cost: ${result.costs['total_monthly_cost_low']:,.2f}")
        print(f"💰 MEDIUM Scenario Cost: ${result.costs['total_monthly_cost_medium']:,.2f}")
        print(f"💰 HIGH Scenario Cost: ${result.costs['total_monthly_cost_high']:,.2f}")
        
        # Save HLD document
        output_file = "example2_azure_serverless_api_hld.md"
        with open(output_file, "w") as f:
            f.write(result.documentation['content'])
        print(f"\n📄 HLD document saved to: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        raise


async def example_3_multi_cloud_detection():
    """Example 3: Multi-cloud detection (AWS, GCP, Oracle)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Multi-Cloud Detection")
    print("=" * 80 + "\n")
    
    test_cases = [
        ("Build a Lambda function for image processing on AWS", "AWS"),
        ("Deploy a microservice on GKE with Cloud SQL", "GCP"),
        ("Create an Autonomous Database on Oracle Cloud", "ORACLE_CLOUD"),
        ("Set up Azure Functions with Cosmos DB", "AZURE"),
    ]
    
    orchestrator = MasterOrchestrator(max_retries=1)
    
    for user_input, expected_cloud in test_cases:
        print(f"\nTest: '{user_input[:50]}...'")
        try:
            result: OrchestratorOutput = await orchestrator.orchestrate(user_input)
            detected_cloud = result.requirements['target_cloud'].upper()
            status = "✅" if detected_cloud == expected_cloud else "❌"
            print(f"  {status} Expected: {expected_cloud}, Detected: {detected_cloud}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


async def main():
    """Run example demonstrations."""
    setup_logging()
    
    print("\n" + "=" * 80)
    print("Co-Pilot SE - Example Demonstrations")
    print("Multi-Cloud Architecture Assistant (POC v2.0)")
    print("=" * 80)
    
    # Check environment variables
    required_env_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "BING_SEARCH_API_KEY",
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\n⚠️  WARNING: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nNote: Examples will use mock data if API keys are not configured.")
        print("For full functionality, set these environment variables in .env file.\n")
    
    # Run examples
    try:
        # Example 1: Azure E-Commerce
        await example_1_azure_ecommerce()
        
        # Example 2: Azure Serverless API
        # await example_2_azure_api_backend()
        
        # Example 3: Multi-Cloud Detection
        # await example_3_multi_cloud_detection()
        
        print("\n" + "=" * 80)
        print("✅ All examples completed!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
