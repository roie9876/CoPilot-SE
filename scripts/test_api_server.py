#!/usr/bin/env python3
"""
Test script for Co-Pilot SE API Server
Tests health endpoint and generate endpoint with Agent Framework
"""

import asyncio
import subprocess
import time
import requests
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_health_endpoint():
    """Test the /health endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Endpoint")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Health endpoint working!")
            return True
        else:
            print("❌ Health endpoint failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_info_endpoint():
    """Test the root / endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Info Endpoint")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Info endpoint working!")
            return True
        else:
            print("❌ Info endpoint failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_generate_endpoint():
    """Test the /api/generate endpoint with a simple request"""
    print("\n" + "="*60)
    print("TEST 3: Generate Endpoint (Simple Blog on AWS)")
    print("="*60)
    print("⏳ This will take 1-2 minutes with Agent Framework...")
    
    request_data = {
        "requirements": "Build a simple blog website on AWS. Need storage for posts and images. Budget is $100/month. Team knows Python and React."
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/generate",
            json=request_data,
            timeout=180  # 3 minutes timeout
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Generate endpoint working!")
            print(f"\nWorkflow Status: {result.get('status', 'unknown')}")
            
            # Print summary
            if 'requirements' in result and result['requirements']:
                req = result['requirements']
                print(f"\n📋 Requirements:")
                print(f"  - Target Cloud: {req.get('target_cloud', 'N/A')}")
                print(f"  - Functional Requirements: {len(req.get('functional_requirements', []))}")
            
            if 'architecture' in result and result['architecture']:
                arch = result['architecture']
                print(f"\n🏗️  Architecture:")
                print(f"  - Services: {len(arch.get('services', []))}")
            
            if 'costs' in result and result['costs']:
                costs = result['costs']
                print(f"\n💰 Costs:")
                print(f"  - Low: ${costs.get('total_monthly_cost_low', 0):.2f}/month")
                print(f"  - Medium: ${costs.get('total_monthly_cost_medium', 0):.2f}/month")
                print(f"  - High: ${costs.get('total_monthly_cost_high', 0):.2f}/month")
            
            if 'documentation' in result and result['documentation']:
                doc = result['documentation']
                print(f"\n📄 Documentation:")
                print(f"  - Format: {doc.get('format', 'N/A')}")
                print(f"  - Content Length: {len(doc.get('content', ''))} chars")
            
            if 'workflow_metadata' in result:
                meta = result['workflow_metadata']
                print(f"\n⏱️  Performance:")
                print(f"  - Total Time: {meta.get('total_duration_seconds', 0):.2f}s")
                print(f"  - Stages Completed: {', '.join(meta.get('stages_completed', []))}")
            
            return True
        else:
            print(f"\n❌ Generate endpoint failed!")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>3 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("🧪 Co-Pilot SE API Server Tests")
    print("="*60)
    print("Testing Agent Framework integration via FastAPI")
    print("="*60)
    
    # Check if server is running
    try:
        requests.get("http://localhost:8000/health", timeout=2)
    except:
        print("\n❌ Server is not running!")
        print("Please start the server first:")
        print("  cd /Users/robenhai/CoPilot-SE")
        print("  .venv/bin/python api/server.py")
        return False
    
    # Run tests
    results = []
    results.append(("Health Endpoint", test_health_endpoint()))
    results.append(("Info Endpoint", test_info_endpoint()))
    results.append(("Generate Endpoint", test_generate_endpoint()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
