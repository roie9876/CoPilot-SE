"""
Test script for refactored Requirements Agent using Agent Framework.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from src.agents.requirements_agent import RequirementsAgent


async def test_requirements_agent():
    """Test Requirements Agent with Agent Framework."""
    print("\n" + "=" * 60)
    print("REQUIREMENTS AGENT TEST (Agent Framework SDK)")
    print("=" * 60)
    
    # Test case 1: E-commerce on AWS
    print("\n" + "=" * 60)
    print("TEST 1: E-commerce Platform on AWS")
    print("=" * 60)
    
    input1 = {
        "user_input": """I need to build an e-commerce platform on AWS for 10,000 concurrent users.
        The system should handle product catalog, shopping cart, and payment processing.
        We need PCI DSS compliance and 99.9% uptime.
        Budget is $5,000 per month. Our team knows Python and React."""
    }
    
    agent = RequirementsAgent()
    
    try:
        result1 = await agent.process(input1)
        print(f"\n✓ Requirements extracted successfully")
        print(f"  Target Cloud: {result1.target_cloud}")
        print(f"  Industry: {result1.industry_vertical}")
        print(f"  Functional Requirements: {len(result1.functional_requirements)}")
        for req in result1.functional_requirements[:3]:
            print(f"    - {req}")
        print(f"  Compliance: {result1.non_functional_requirements.compliance}")
        print(f"  Budget: {result1.technical_constraints.budget}")
        print(f"  Team Skills: {result1.technical_constraints.team_skills}")
        print(f"  Needs Clarification: {result1.needs_clarification}")
        print(f"  Confidence Score: {result1.confidence_score}")
    except Exception as e:
        print(f"\n✗ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test case 2: Healthcare app with ambiguity
    print("\n" + "=" * 60)
    print("TEST 2: Healthcare Application (Missing Cloud Platform)")
    print("=" * 60)
    
    input2 = {
        "user_input": """Build a patient management system for a hospital.
        Need to store medical records and comply with HIPAA.
        Support 500 concurrent users."""
    }
    
    try:
        result2 = await agent.process(input2)
        print(f"\n✓ Requirements extracted successfully")
        print(f"  Target Cloud: {result2.target_cloud}")
        print(f"  Industry: {result2.industry_vertical}")
        print(f"  Compliance: {result2.non_functional_requirements.compliance}")
        print(f"  Needs Clarification: {result2.needs_clarification}")
        if result2.needs_clarification:
            print(f"  Clarifying Questions:")
            for q in result2.clarifying_questions:
                print(f"    - {q}")
        print(f"  Confidence Score: {result2.confidence_score}")
    except Exception as e:
        print(f"\n✗ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_requirements_agent())
    sys.exit(0 if success else 1)
