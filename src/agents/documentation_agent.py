"""
Documentation Agent - Generates High-Level Design (HLD) documents with diagrams and recommendations.

This agent transforms the outputs from Requirements, Architecture, and Cost agents
into professional HLD documentation suitable for stakeholders and implementation teams.
"""

import logging
from datetime import datetime
from typing import List, Optional

from ..models.schemas import (
    DocumentationInput,
    DocumentationOutput,
    DocumentMetadata,
    DiagramOutput,
    ServiceSelection,
    WellArchitectedAnalysis,
    CostScenario,
    CostOptimization,
    Citation,
    ErrorType,
    CloudPlatform,
)
from .base_agent import BaseAgent


class DocumentationAgent(BaseAgent):
    """
    Agent responsible for generating comprehensive High-Level Design (HLD) documents.
    
    Features:
    - Executive summary for stakeholders
    - Requirements documentation
    - Architecture diagrams (Mermaid format)
    - Service selection rationale
    - Cost breakdown and optimization recommendations
    - Well-Architected Framework analysis
    - Deployment guide
    - References and citations
    """

    def __init__(self):
        super().__init__("DocumentationAgent")
        self.logger.info("DocumentationAgent initialized")

    async def process(self, input_data: DocumentationInput) -> DocumentationOutput:
        """
        Generate comprehensive HLD documentation from agent outputs.
        
        Args:
            input_data: Documentation input containing all agent outputs
            
        Returns:
            DocumentationOutput with markdown HLD, diagrams, and metadata
            
        Raises:
            AgentError: If documentation generation fails
        """
        try:
            self.logger.info("Starting HLD document generation")
            
            # Validate and parse input
            validated_input = DocumentationInput(**input_data)
            
            # Generate main HLD document
            hld_markdown = self._generate_hld_document(validated_input)
            
            # Generate additional diagrams if needed
            diagrams = self._generate_additional_diagrams(validated_input)
            
            # Create metadata with DocumentMetadata model
            cloud_platform = validated_input.requirements.target_cloud
            if isinstance(cloud_platform, str):
                cloud_platform = CloudPlatform(cloud_platform.lower())
            
            metadata = DocumentMetadata(
                title=f"High-Level Design - {cloud_platform.value.upper()} Architecture",
                generated_at=datetime.utcnow(),
                cloud_platform=cloud_platform,
                version="1.0",
                filename=f"hld-{cloud_platform.value}-{datetime.utcnow().strftime('%Y%m%d')}.md",
                author="Co-Pilot SE v2.0"
            )
            
            self.logger.info("HLD document generated successfully")
            
            return DocumentationOutput(
                format="markdown",
                content=hld_markdown,
                diagrams=diagrams,
                metadata=metadata,
            )
            
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            raise self._create_error(
                error_message="Failed to generate HLD documentation",
                error_type=ErrorType.UNKNOWN_ERROR,
                details={"error": str(e)},
            )

    def _generate_hld_document(self, input_data: DocumentationInput) -> str:
        """
        Generate the main HLD document in markdown format.
        
        Args:
            input_data: All agent outputs
            
        Returns:
            Complete HLD document as markdown string
        """
        sections = []
        
        # Title and metadata
        sections.append(self._generate_title_section(input_data))
        
        # Executive summary
        sections.append(self._generate_executive_summary(input_data))
        
        # Requirements overview
        sections.append(self._generate_requirements_section(input_data))
        
        # Architecture design
        sections.append(self._generate_architecture_section(input_data))
        
        # Cost analysis
        sections.append(self._generate_cost_section(input_data))
        
        # Well-Architected Framework analysis
        sections.append(self._generate_well_architected_section(input_data))
        
        # Deployment guide
        sections.append(self._generate_deployment_guide(input_data))
        
        # References
        sections.append(self._generate_references_section(input_data))
        
        return "\n\n".join(sections)

    def _generate_title_section(self, input_data: DocumentationInput) -> str:
        """Generate title page and metadata."""
        cloud = input_data.requirements.target_cloud.upper()
        industry = (
            input_data.requirements.industry_vertical.replace("_", " ").title()
            if input_data.requirements.industry_vertical
            else "General"
        )
        
        return f"""# High-Level Design Document

**Cloud Platform:** {cloud}  
**Industry Vertical:** {industry}  
**Generated:** {datetime.utcnow().strftime("%B %d, %Y")}  
**Version:** 1.0

---"""

    def _generate_executive_summary(self, input_data: DocumentationInput) -> str:
        """Generate executive summary for stakeholders."""
        cloud = input_data.requirements.target_cloud.upper()
        num_services = len(input_data.architecture.services)
        
        # Get medium cost scenario
        medium_cost = next(
            (s.total_monthly_cost for s in input_data.costs.cost_scenarios if s.scenario == "MEDIUM"),
            0.0
        )
        
        # Count key service categories
        compute_services = [s for s in input_data.architecture.services if s.category == "compute"]
        storage_services = [s for s in input_data.architecture.services if s.category == "storage"]
        database_services = [s for s in input_data.architecture.services if s.category == "database"]
        
        summary = f"""## Executive Summary

This High-Level Design (HLD) document outlines a comprehensive cloud architecture solution on **{cloud}** that addresses the identified business and technical requirements. The proposed architecture leverages **{num_services} {cloud} services** to deliver a scalable, secure, and cost-effective solution.

### Key Highlights

- **Cloud Platform:** {cloud}
- **Total Services:** {num_services} ({len(compute_services)} compute, {len(storage_services)} storage, {len(database_services)} database)
- **Estimated Monthly Cost:** ${medium_cost:,.2f} (baseline production workload)
- **Architecture Pattern:** {self._infer_architecture_pattern(input_data.architecture.services)}

### Requirements Confidence

The solution is designed based on the extracted requirements with a confidence score of **{input_data.requirements.confidence_score:.0%}**. """
        
        if input_data.requirements.clarifying_questions:
            summary += f"""Additional clarifications may further optimize the architecture (see Requirements section).

"""
        else:
            summary += """All critical requirements have been captured and addressed.

"""
        
        summary += f"""### Well-Architected Framework Alignment

The architecture has been evaluated against the {cloud} Well-Architected Framework across five pillars:

- **Operational Excellence:** {self._get_pillar_score(input_data.architecture.design_rationale, "operational_excellence")}
- **Security:** {self._get_pillar_score(input_data.architecture.design_rationale, "security")}
- **Reliability:** {self._get_pillar_score(input_data.architecture.design_rationale, "reliability")}
- **Performance Efficiency:** {self._get_pillar_score(input_data.architecture.design_rationale, "performance")}
- **Cost Optimization:** {self._get_pillar_score(input_data.architecture.design_rationale, "cost_optimization")}

### Cost Optimization Opportunities

{len(input_data.costs.cost_optimizations)} cost optimization strategies have been identified, with potential savings of up to **{self._calculate_max_savings(input_data.costs.cost_optimizations)}%**."""
        
        return summary

    def _generate_requirements_section(self, input_data: DocumentationInput) -> str:
        """Generate requirements documentation section."""
        reqs = input_data.requirements
        
        section = """## Requirements Overview

### Functional Requirements

"""
        
        if reqs.functional_requirements:
            for i, req in enumerate(reqs.functional_requirements, 1):
                section += f"{i}. {req}\n"
        else:
            section += "_No specific functional requirements captured._\n"
        
        section += "\n### Non-Functional Requirements\n\n"
        
        if reqs.non_functional_requirements:
            nfr = reqs.non_functional_requirements
            # NonFunctionalRequirements is a model with fields: scalability, performance, availability, security, compliance
            if nfr.scalability:
                section += "**Scalability:**\n"
                for key, value in nfr.scalability.items():
                    section += f"- {key}: {value}\n"
                section += "\n"
            if nfr.performance:
                section += "**Performance:**\n"
                for key, value in nfr.performance.items():
                    section += f"- {key}: {value}\n"
                section += "\n"
            if nfr.availability:
                section += "**Availability:**\n"
                for key, value in nfr.availability.items():
                    section += f"- {key}: {value}\n"
                section += "\n"
            if nfr.security:
                section += "**Security:**\n"
                for key, value in nfr.security.items():
                    section += f"- {key}: {value}\n"
                section += "\n"
            if nfr.compliance:
                section += "**Compliance:**\n"
                for item in nfr.compliance:
                    section += f"- {item}\n"
                section += "\n"
        
        if not reqs.non_functional_requirements or all([
            not reqs.non_functional_requirements.scalability,
            not reqs.non_functional_requirements.performance,
            not reqs.non_functional_requirements.availability,
            not reqs.non_functional_requirements.security,
            not reqs.non_functional_requirements.compliance
        ]):
            section += "_No specific non-functional requirements captured._\n\n"
        
        # Technical constraints
        if reqs.technical_constraints:
            tc = reqs.technical_constraints
            section += "### Technical Constraints\n\n"
            # TechnicalConstraints has: budget, timeline, team_skills, existing_infrastructure, preferred_technologies
            if tc.budget:
                section += f"**Budget:** {tc.budget}\n"
            if tc.timeline:
                section += f"**Timeline:** {tc.timeline}\n"
            if tc.team_skills:
                section += f"**Team Skills:** {', '.join(tc.team_skills)}\n"
            if tc.existing_infrastructure:
                section += f"**Existing Infrastructure:** {', '.join(tc.existing_infrastructure)}\n"
            if tc.preferred_technologies:
                section += f"**Preferred Technologies:** {', '.join(tc.preferred_technologies)}\n"
            section += "\n"
        
        # Clarifying questions
        if reqs.clarifying_questions:
            section += "### Clarifying Questions\n\n"
            section += "_The following questions could help refine the architecture:_\n\n"
            for i, question in enumerate(reqs.clarifying_questions, 1):
                section += f"{i}. {question}\n"
            section += "\n"
        
        return section

    def _generate_architecture_section(self, input_data: DocumentationInput) -> str:
        """Generate architecture design section with diagrams and service details."""
        arch = input_data.architecture
        
        section = f"""## Architecture Design

### Architecture Diagram

```mermaid
{arch.architecture_diagram}
```

### Design Rationale

The architecture has been designed according to the Well-Architected Framework:

**Operational Excellence:**
{arch.design_rationale.operational_excellence}

**Security:**
{arch.design_rationale.security}

**Reliability:**
{arch.design_rationale.reliability}

**Performance Efficiency:**
{arch.design_rationale.performance_efficiency}

**Cost Optimization:**
{arch.design_rationale.cost_optimization}

### Selected Services

The following table summarizes the {len(arch.services)} selected services:

| Service Name | Type | SKU | Region | Purpose |
|--------------|------|-----|--------|---------|
"""
        
        for service in arch.services:
            sku = service.configuration.sku if service.configuration and service.configuration.sku else 'Default'
            region = arch.region or 'Multi-region'
            section += f"| {service.service_name} | {service.category.title()} | {sku} | {region} | {service.rationale[:80]}... |\n"
        
        section += "\n### Service Details\n\n"
        
        # Group services by type
        services_by_type = {}
        for service in arch.services:
            if service.category not in services_by_type:
                services_by_type[service.category] = []
            services_by_type[service.category].append(service)
        
        for service_type, services in services_by_type.items():
            section += f"#### {service_type.replace('_', ' ').title()} Services\n\n"
            for service in services:
                sku = service.configuration.sku if service.configuration and service.configuration.sku else 'Default'
                section += f"**{service.service_name}** ({sku})\n\n"
                section += f"- **Rationale:** {service.rationale}\n"
                if service.configuration:
                    # ServiceConfiguration is a model, convert to dict
                    config_dict = service.configuration.model_dump(exclude_none=True)
                    if config_dict:
                        section += "- **Configuration:**\n"
                        for key, value in config_dict.items():
                            section += f"  - {key}: {value}\n"
                section += "\n"
        
        # Trade-offs
        if arch.trade_offs:
            section += "### Trade-Offs and Considerations\n\n"
            for trade_off in arch.trade_offs:
                section += f"- {trade_off}\n"
            section += "\n"
        
        return section

    def _generate_cost_section(self, input_data: DocumentationInput) -> str:
        """Generate cost analysis section with scenarios and optimizations."""
        costs = input_data.costs
        
        section = """## Cost Analysis

### Cost Scenarios

The following cost scenarios illustrate different usage patterns:

| Scenario | Usage Profile | Monthly Cost | Key Assumptions |
|----------|---------------|--------------|-----------------|
"""
        
        for scenario in costs.cost_scenarios:
            assumptions = ", ".join(scenario.assumptions[:2]) if scenario.assumptions else "Standard usage"
            section += f"| **{scenario.scenario}** | {scenario.usage_profile} | ${scenario.total_monthly_cost:,.2f} | {assumptions} |\n"
        
        section += "\n### Cost Breakdown (Medium Scenario)\n\n"
        
        # Get medium scenario
        medium_scenario = next((s for s in costs.cost_scenarios if s.scenario == "MEDIUM"), None)
        
        if medium_scenario:
            section += "| Service | Monthly Cost | Unit Cost | Assumptions |\n"
            section += "|---------|--------------|-----------|-------------|\n"
            
            for service_cost in medium_scenario.service_breakdown:
                assumptions = ", ".join(service_cost.assumptions[:2]) if service_cost.assumptions else "Standard"
                section += f"| {service_cost.service_name} | ${service_cost.monthly_cost:,.2f} | {service_cost.unit_cost} | {assumptions} |\n"
            
            section += f"\n**Total Monthly Cost:** ${medium_scenario.total_monthly_cost:,.2f}\n\n"
        
        # Cost optimizations
        section += "### Cost Optimization Recommendations\n\n"
        
        for i, optimization in enumerate(costs.cost_optimizations, 1):
            section += f"#### {i}. {optimization.recommendation}\n\n"
            section += f"- **Estimated Savings:** {optimization.estimated_savings}\n"
            section += f"- **Implementation Effort:** {optimization.implementation_effort}\n"
            section += f"- **Impact:** {optimization.impact}\n\n"
        
        # Disclaimers
        if costs.disclaimers:
            section += "### Cost Disclaimers\n\n"
            for disclaimer in costs.disclaimers:
                section += f"- {disclaimer}\n"
            section += "\n"
        
        return section

    def _generate_well_architected_section(self, input_data: DocumentationInput) -> str:
        """Generate Well-Architected Framework analysis section."""
        waf = input_data.architecture.design_rationale
        
        section = """## Well-Architected Framework Analysis

This section evaluates the architecture against the five pillars of the Well-Architected Framework.

"""
        
        # WellArchitectedAnalysis fields are strings, not lists
        pillars = [
            ("Operational Excellence", waf.operational_excellence),
            ("Security", waf.security),
            ("Reliability", waf.reliability),
            ("Performance Efficiency", waf.performance_efficiency),
            ("Cost Optimization", waf.cost_optimization),
        ]
        
        for pillar_name, description in pillars:
            section += f"### {pillar_name}\n\n"
            if description:
                section += f"{description}\n\n"
            else:
                section += "_No specific recommendations for this pillar._\n\n"
        
        return section

    def _generate_deployment_guide(self, input_data: DocumentationInput) -> str:
        """Generate deployment guide section."""
        cloud = input_data.requirements.target_cloud.upper()
        
        section = f"""## Deployment Guide

### Prerequisites

1. **{cloud} Account** with appropriate subscription and permissions
2. **Infrastructure as Code (IaC) Tools:**
   - Azure CLI or AWS CLI or gcloud CLI
   - Terraform or Bicep (recommended for production)
3. **Access Credentials:**
   - Service principal or IAM role with deployment permissions
4. **Development Tools:**
   - Git for version control
   - CI/CD pipeline (GitHub Actions, Azure DevOps, or GitLab CI)

### Deployment Steps

#### 1. Environment Setup

"""
        
        if input_data.requirements.target_cloud == "azure":
            section += """```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "<subscription-id>"

# Create resource group
az group create --name "rg-app-prod" --location "eastus"
```

"""
        elif input_data.requirements.target_cloud == "aws":
            section += """```bash
# Configure AWS CLI
aws configure

# Set default region
export AWS_DEFAULT_REGION=us-east-1
```

"""
        elif input_data.requirements.target_cloud == "gcp":
            section += """```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project <project-id>
```

"""
        
        section += """#### 2. Infrastructure Deployment

Deploy the infrastructure using IaC tools:

```bash
# Using Terraform
terraform init
terraform plan -out=deployment.tfplan
terraform apply deployment.tfplan

# Using Bicep (Azure)
az deployment group create \\
  --resource-group rg-app-prod \\
  --template-file main.bicep \\
  --parameters @parameters.json
```

#### 3. Application Deployment

Deploy the application code to the provisioned infrastructure:

1. Build application artifacts
2. Run automated tests
3. Deploy to staging environment
4. Run smoke tests
5. Deploy to production (blue-green or canary)

#### 4. Post-Deployment Validation

- Verify all services are running
- Check application health endpoints
- Validate monitoring and alerting
- Review security configurations
- Test disaster recovery procedures

### Rollback Strategy

In case of deployment issues:

1. Use blue-green deployment to switch back to previous version
2. Restore from automated backups if needed
3. Review deployment logs and error messages
4. Fix issues and re-deploy

"""
        
        return section

    def _generate_references_section(self, input_data: DocumentationInput) -> str:
        """Generate references and citations section."""
        section = """## References

### Documentation and Best Practices

"""
        
        # Collect all citations from requirements, architecture, and costs
        all_citations = []
        if input_data.requirements.citations:
            all_citations.extend(input_data.requirements.citations)
        if input_data.architecture.citations:
            all_citations.extend(input_data.architecture.citations)
        if input_data.costs.citations:
            all_citations.extend(input_data.costs.citations)
        
        if all_citations:
            # Group citations by source type
            docs = [c for c in all_citations if "docs" in c.url.lower() or "documentation" in c.url.lower()]
            pricing = [c for c in all_citations if "pricing" in c.url.lower() or "calculator" in c.url.lower()]
            other = [c for c in all_citations if c not in docs and c not in pricing]
            
            if docs:
                section += "**Official Documentation:**\n\n"
                for i, citation in enumerate(docs, 1):
                    section += f"{i}. [{citation.title}]({citation.url})\n"
                section += "\n"
            
            if pricing:
                section += "**Pricing References:**\n\n"
                for i, citation in enumerate(pricing, 1):
                    section += f"{i}. [{citation.title}]({citation.url})\n"
                section += "\n"
            
            if other:
                section += "**Additional Resources:**\n\n"
                for i, citation in enumerate(other, 1):
                    section += f"{i}. [{citation.title}]({citation.url})\n"
                section += "\n"
        else:
            section += "_No external references cited._\n\n"
        
        section += """### Contact Information

For questions or clarifications regarding this HLD, please contact:

- **Solution Architect:** [Your Name]
- **Email:** [your.email@company.com]
- **Last Updated:** """ + datetime.utcnow().strftime("%B %d, %Y")
        
        return section

    def _generate_additional_diagrams(self, input_data: DocumentationInput) -> List[DiagramOutput]:
        """
        Generate additional diagrams beyond the main architecture diagram.
        
        Returns:
            List of DiagramOutput objects
        """
        diagrams = []
        
        # Include the main architecture diagram
        diagrams.append(DiagramOutput(
            name="Architecture Diagram",
            format="mermaid",
            content=input_data.architecture.architecture_diagram,
            description="High-level architecture diagram showing all services and their relationships"
        ))
        
        # Could add more diagrams here (e.g., deployment flow, data flow, etc.)
        
        return diagrams

    # Helper methods

    def _infer_architecture_pattern(self, services: List[ServiceSelection]) -> str:
        """Infer the primary architecture pattern from selected services."""
        service_types = [s.category for s in services]
        
        if "container" in service_types or any("kubernetes" in s.service_name.lower() for s in services):
            return "Microservices / Containerized"
        elif any("function" in s.service_name.lower() for s in services):
            return "Serverless / Event-Driven"
        elif any("vm" in s.service_name.lower() or "compute" in s.service_name.lower() for s in services):
            return "Traditional / IaaS"
        else:
            return "Cloud-Native / PaaS"

    def _get_pillar_score(self, waf: WellArchitectedAnalysis, pillar: str) -> str:
        """Get a qualitative score for a Well-Architected pillar."""
        # WellArchitectedAnalysis fields are strings, not lists
        description = getattr(waf, pillar, "")
        
        if not description or len(description) < 20:
            return "⚠️ Needs attention"
        elif len(description) < 100:
            return "✅ Good"
        else:
            return "✅ Excellent"

    def _calculate_max_savings(self, optimizations: List[CostOptimization]) -> int:
        """Calculate maximum potential savings percentage from optimizations."""
        max_savings = 0
        
        for opt in optimizations:
            # Extract percentage from estimated_savings string
            savings_text = opt.estimated_savings.lower()
            if "%" in savings_text:
                try:
                    # Extract first number before %
                    import re
                    match = re.search(r'(\d+)%', savings_text)
                    if match:
                        savings = int(match.group(1))
                        max_savings = max(max_savings, savings)
                except:
                    pass
        
        return max_savings if max_savings > 0 else 30  # Default to 30% if no specific percentage found
