#!/usr/bin/env python3
"""
Test script for Knowledge Graph Orchestrator

Tests the intent extraction and orchestration flow.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import IntentExtractor, KnowledgeGraphOrchestrator


def test_intent_extraction():
    """Test intent extraction from user input."""
    print("\n" + "=" * 80)
    print("TEST 1: Intent Extraction")
    print("=" * 80)

    extractor = IntentExtractor()

    test_cases = [
        "Build an e-commerce platform on Azure with AKS for 10,000 users",
        "We need disaster recovery for our SQL database in West Europe",
        "Migrate our on-premises .NET app to Azure App Service",
        "Set up a data analytics platform with Azure Synapse",
    ]

    for user_input in test_cases:
        print(f"\nInput: {user_input}")
        try:
            context = extractor.extract(user_input)
            print(f"  Intent: {context.intent.value}")
            print(f"  Cloud: {context.cloud_provider.value}")
            print(f"  Workload: {context.workload_type.value}")
            print(f"  Description: {context.business_description[:100]}...")
        except Exception as e:
            print(f"  ERROR: {e}")


def test_orchestration():
    """Test full orchestration flow."""
    print("\n" + "=" * 80)
    print("TEST 2: Knowledge Graph Orchestration")
    print("=" * 80)

    orchestrator = KnowledgeGraphOrchestrator()

    user_input = """
    We need to build a new web application on Azure for our e-commerce platform.
    We expect around 10,000 concurrent users. The app should be highly available
    with 99.9% uptime. We need to store customer data in a SQL database with
    proper encryption. The app should be accessible from the internet but the
    database should be private. We also need Azure AD authentication for our
    internal admin panel.
    """

    try:
        print(f"\nProcessing input: {user_input[:150]}...")
        kg = orchestrator.orchestrate(user_input)

        print("\n" + "-" * 80)
        print("RESULTS:")
        print("-" * 80)
        print(f"Intent: {kg.context.intent.value}")
        print(f"Cloud: {kg.context.cloud_provider.value}")
        print(f"Workload: {kg.context.workload_type.value}")
        print(f"\nDomain Confidence Scores:")
        print(f"  - Identity & Access: {kg.identity_access.confidence:.2f}")
        print(f"  - Runtime Platform: {kg.runtime_platform.confidence:.2f}")
        print(f"  - Networking: {kg.networking_connectivity.confidence:.2f}")
        print(f"  - Data Persistence: {kg.data_persistence.confidence:.2f}")
        print(f"  - Resiliency & DR: {kg.resiliency_dr.confidence:.2f}")
        print(f"\nCritical Gaps: {len(kg.status.critical_gaps)}")
        if kg.status.critical_gaps:
            for gap in kg.status.critical_gaps[:5]:  # Show first 5
                print(f"  - {gap}")
        print(f"\nConflicts: {len(kg.status.conflicts)}")
        if kg.status.conflicts:
            for conflict in kg.status.conflicts[:3]:  # Show first 3
                print(f"  - [{conflict.severity.upper()}] {conflict.description}")
        print(f"\nReady for Design: {kg.status.ready_for_design}")

        # Get next questions
        domain, questions = orchestrator.get_next_questions(kg)
        if questions:
            print(f"\nNext Questions ({domain}):")
            for q in questions[:5]:  # Show first 5
                print(f"  - [{q.priority}] {q.question_text}")

    except Exception as e:
        print(f"\nERROR during orchestration: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n🚀 Testing Knowledge Graph Orchestrator")
    print("=" * 80)

    # Check environment variables
    required_vars = [
        "AZURE_AI_PROJECT",
        "MODEL_DEPLOYMENT_NAME",
        "AZURE_SUBSCRIPTION_ID",
    ]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please ensure .env is loaded and contains all required values.")
        return 1

    print("✅ Environment variables loaded")

    try:
        # Test 1: Intent extraction
        test_intent_extraction()

        # Test 2: Full orchestration
        test_orchestration()

        print("\n" + "=" * 80)
        print("✅ All tests completed!")
        print("=" * 80 + "\n")
        return 0

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
