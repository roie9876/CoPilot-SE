"""
End-to-end test for complete workflow with Agent Framework SDK.
Tests Requirements → Architecture → Cost → Documentation pipeline.
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

from src.orchestrator.master_orchestrator import MasterOrchestrator


async def test_e2e_workflow():
    """Test complete workflow from requirements to documentation."""
    print("\n" + "=" * 60)
    print("END-TO-END WORKFLOW TEST (Agent Framework SDK)")
    print("=" * 60)
    
    # Test input: E-commerce platform on AWS
    user_input = """
Build an e-commerce platform on AWS for a retail company.

Requirements:
- Product catalog with search and filtering
- Shopping cart and checkout
- Payment processing (Stripe integration)
- User authentication and profiles
- Order management and tracking
- Admin dashboard

Expected load: 10,000 concurrent users
Need PCI DSS compliance for payment data
High availability required (99.9% uptime)
Monthly budget: $5,000
Team knows Python and React
Timeline: 3 months
    """.strip()
    
    print(f"\nUser Input:")
    print(f"{user_input}\n")
    print("=" * 60)
    
    try:
        # Initialize orchestrator
        orchestrator = MasterOrchestrator(max_retries=2)
        
        # Run complete workflow
        print("\nStarting workflow orchestration...")
        print("This will take 2-5 minutes with Bing research...\n")
        
        result = await orchestrator.orchestrate(user_input)
        
        # Display results
        print("\n" + "=" * 60)
        print("WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Handle both dict and object access patterns
        req = result.get("requirements", result.requirements) if hasattr(result, 'get') else result.requirements
        arch = result.get("architecture", result.architecture) if hasattr(result, 'get') else result.architecture
        costs = result.get("costs", result.costs) if hasattr(result, 'get') else result.costs
        doc = result.get("documentation", result.documentation) if hasattr(result, 'get') else result.documentation
        
        print(f"\n📋 REQUIREMENTS:")
        print(f"  Target Cloud: {req.target_cloud if hasattr(req, 'target_cloud') else req.get('target_cloud', 'N/A')}")
        print(f"  Industry: {req.industry_vertical if hasattr(req, 'industry_vertical') else req.get('industry_vertical', 'N/A')}")
        func_reqs = req.functional_requirements if hasattr(req, 'functional_requirements') else req.get('functional_requirements', [])
        print(f"  Functional Requirements: {len(func_reqs)}")
        nfr = req.non_functional_requirements if hasattr(req, 'non_functional_requirements') else req.get('non_functional_requirements', {})
        compliance = nfr.compliance if hasattr(nfr, 'compliance') else nfr.get('compliance', [])
        print(f"  Compliance: {compliance}")
        needs_clar = req.needs_clarification if hasattr(req, 'needs_clarification') else req.get('needs_clarification', False)
        print(f"  Needs Clarification: {needs_clar}")
        
        print(f"\n🏗️  ARCHITECTURE:")
        services = arch.services if hasattr(arch, 'services') else arch.get('services', [])
        print(f"  Services Selected: {len(services)}")
        for i, svc in enumerate(services[:5], 1):
            svc_name = svc.service_name if hasattr(svc, 'service_name') else svc.get('service_name', 'Unknown')
            svc_cat = svc.category if hasattr(svc, 'category') else svc.get('category', 'other')
            print(f"  {i}. {svc_name} ({svc_cat})")
        if len(services) > 5:
            print(f"  ... and {len(services) - 5} more services")
        
        print(f"\n💰 COSTS:")
        low = costs.total_monthly_cost_low if hasattr(costs, 'total_monthly_cost_low') else costs.get('total_monthly_cost_low', 0)
        med = costs.total_monthly_cost_medium if hasattr(costs, 'total_monthly_cost_medium') else costs.get('total_monthly_cost_medium', 0)
        high = costs.total_monthly_cost_high if hasattr(costs, 'total_monthly_cost_high') else costs.get('total_monthly_cost_high', 0)
        opt_recs = costs.cost_optimization_recommendations if hasattr(costs, 'cost_optimization_recommendations') else costs.get('cost_optimization_recommendations', [])
        print(f"  Low Usage: ${low:.2f}/month")
        print(f"  Medium Usage: ${med:.2f}/month")
        print(f"  High Usage: ${high:.2f}/month")
        print(f"  Optimizations: {len(opt_recs)}")
        
        print(f"\n📄 DOCUMENTATION:")
        content = doc.content if hasattr(doc, 'content') else doc.get('content', '')
        fmt = doc.format if hasattr(doc, 'format') else doc.get('format', 'markdown')
        diagrams = doc.diagrams if hasattr(doc, 'diagrams') else doc.get('diagrams', [])
        print(f"  Content Length: {len(content)} chars")
        print(f"  Format: {fmt}")
        print(f"  Diagrams: {len(diagrams)}")
        
        meta = result.workflow_metadata
        status = result.status
        all_cit = result.citations
        
        print(f"\n📊 WORKFLOW METADATA:")
        print(f"  Status: {status}")
        print(f"  Total Time: {meta.total_duration_seconds:.2f}s")
        print(f"  Stages Completed: {', '.join(meta.stages_completed)}")
        print(f"  Agents Invoked: {', '.join(meta.agents_invoked)}")
        print(f"  Total Citations: {len(all_cit)}")
        
        print("\n" + "=" * 60)
        print("✅ ALL STAGES COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        # Save HLD to file
        output_file = Path(__file__).parent.parent / "output" / "test_hld.md"
        output_file.parent.mkdir(exist_ok=True)
        # doc.content is the full HLD markdown
        hld_content = doc.content if hasattr(doc, 'content') else doc.get('content', '# No content generated')
        output_file.write_text(hld_content)
        print(f"\n💾 HLD saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ WORKFLOW FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_e2e_workflow())
    sys.exit(0 if success else 1)
