"""
Cost Agent - Estimates Azure infrastructure costs.

This agent:
1. Analyzes architecture design and calculates costs
2. Provides low/medium/high usage scenarios
3. Generates cost optimization recommendations
4. Uses deterministic pricing data (no cloud provider auth needed for POC)
"""

from typing import Dict, List
import logging
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.models.schemas import (
    CostInput,
    CostOutput,
    ServiceCost,
    UsageAssumptions,
    CostOptimization,
    Citation,
    ArchitectureOutput,
    CloudPlatform,
    ErrorType,
)

logger = logging.getLogger(__name__)


class CostAgent(BaseAgent):
    """
    Azure cost estimation agent.
    
    Provides ±30% accuracy for POC using public pricing data.
    For production, integrate with Azure Pricing API or Cost Management API.
    """
    
    # Azure pricing data (East US region, Pay-As-You-Go rates, November 2025)
    # Source: https://azure.microsoft.com/en-us/pricing/
    AZURE_PRICING = {
        # Compute
        "Azure App Service": {
            "B1 (Basic)": {"hourly": 0.075, "monthly": 54.75, "billing": "hourly"},
            "S1 (Standard)": {"hourly": 0.10, "monthly": 73.00, "billing": "hourly"},
            "P1v2 (Premium)": {"hourly": 0.175, "monthly": 127.75, "billing": "hourly"},
        },
        "Azure Functions": {
            "Consumption": {
                "monthly": 20.0,  # Estimated average
                "per_execution": 0.0000002,
                "per_gb_second": 0.000016,
                "billing": "consumption"
            },
            "Premium": {"hourly": 0.169, "monthly": 123.37, "billing": "hourly"},
        },
        "Azure Kubernetes Service (AKS)": {
            "cluster_management": {"monthly": 0.0},  # Free
            "node_pool_vm": {
                "D2s_v3": {"hourly": 0.096, "monthly": 70.08, "billing": "hourly"}
            }
        },
        "Azure Container Instances (ACI)": {
            "per_vcpu_second": 0.0000125,
            "per_gb_second": 0.0000014,
            "monthly_estimate": 50.0,  # 1 vCPU, 2GB RAM
            "billing": "per-second"
        },
        "Azure Virtual Machines": {
            "B1s (Burstable)": {"hourly": 0.0104, "monthly": 7.59, "billing": "hourly"},
            "D2s_v3 (General)": {"hourly": 0.096, "monthly": 70.08, "billing": "hourly"},
        },
        
        # Storage
        "Azure Blob Storage": {
            "Hot": {
                "per_gb": 0.0184,
                "operations_per_10k": 0.05,
                "monthly_100gb": 2.0,
                "billing": "per-GB + operations"
            },
            "Cool": {
                "per_gb": 0.0102,
                "operations_per_10k": 0.10,
                "billing": "per-GB + operations"
            },
        },
        "Azure Queue Storage": {
            "per_gb": 0.045,
            "operations_per_10k": 0.05,
            "monthly_estimate": 5.0,
            "billing": "per-GB + operations"
        },
        "Azure Files": {
            "per_gb": 0.06,
            "monthly_100gb": 6.0,
            "billing": "per-GB"
        },
        
        # Database
        "Azure SQL Database": {
            "Basic": {"monthly": 4.99, "billing": "monthly"},
            "Standard S1": {"monthly": 30.00, "billing": "monthly"},
            "Standard S2": {"monthly": 75.00, "billing": "monthly"},
            "Premium P1": {"monthly": 465.00, "billing": "monthly"},
        },
        "Azure Cosmos DB": {
            "provisioned_throughput": {
                "per_100_ru": 0.008,  # per hour
                "monthly_400ru": 23.36,  # 400 RU/s minimum
                "billing": "hourly"
            },
            "serverless": {
                "per_million_ru": 0.25,
                "per_gb": 0.25,
                "billing": "consumption"
            }
        },
        "Azure Database for PostgreSQL": {
            "Flexible Server - B1ms": {"monthly": 12.41, "billing": "monthly"},
            "Flexible Server - D2s_v3": {"monthly": 140.16, "billing": "monthly"},
        },
        "Azure Database for MySQL": {
            "Flexible Server - B1ms": {"monthly": 12.41, "billing": "monthly"},
        },
        "Azure Cache for Redis": {
            "Basic C0": {"monthly": 16.06, "billing": "monthly"},
            "Standard C1": {"monthly": 62.05, "billing": "monthly"},
            "Premium P1": {"monthly": 203.00, "billing": "monthly"},
        },
        
        # Networking
        "Azure Application Gateway": {
            "WAF_v2": {
                "per_hour": 0.443,
                "per_capacity_unit": 0.008,
                "monthly_base": 323.39,
                "billing": "hourly + capacity units"
            }
        },
        "Azure Front Door": {
            "Standard": {
                "per_month": 35.00,
                "per_gb_outbound": 0.085,
                "monthly_estimate": 200.0,
                "billing": "monthly + data transfer"
            }
        },
        "Azure Load Balancer": {
            "Standard": {"monthly": 25.00, "billing": "monthly"},
        },
        
        # Security
        "Azure Key Vault": {
            "operations_per_10k": 0.03,
            "monthly_estimate": 5.0,
            "billing": "per-operation"
        },
        "Azure Active Directory (Entra ID)": {
            "Free": {"monthly": 0.0, "billing": "free"},
            "Premium P1": {"monthly": 6.00, "billing": "per-user"},
        },
        
        # Monitoring
        "Azure Monitor": {
            "log_ingestion_per_gb": 2.76,
            "log_retention_per_gb": 0.12,
            "monthly_estimate": 50.0,
            "billing": "per-GB"
        },
    }
    
    def __init__(self):
        """Initialize Cost Agent."""
        super().__init__(name="CostAgent")
    
    async def process(self, input_data: Dict) -> Dict:
        """
        Estimate costs for Azure architecture.
        
        Args:
            input_data: Dict with 'architecture', 'target_cloud', 'region', 'usage_profile'
            
        Returns:
            CostOutput dict
        """
        self._record_invocation()
        
        try:
            # Validate input
            cost_input = CostInput(**input_data)
            
            # Only process Azure (for now)
            if cost_input.target_cloud != CloudPlatform.AZURE:
                raise self._create_error(
                    f"Only Azure is supported in current implementation. Got: {cost_input.target_cloud}",
                    error_type=ErrorType.VALIDATION_ERROR,
                    retryable=False
                )
            
            self.logger.info(f"Estimating costs for {len(cost_input.architecture.services)} Azure services")
            
            # Calculate costs for each service
            service_costs = []
            for service in cost_input.architecture.services:
                # Convert ServiceSelection model to dict for cost calculation
                service_dict = service.model_dump() if hasattr(service, 'model_dump') else service
                cost = self._calculate_service_cost(
                    service_dict,
                    cost_input.usage_profile
                )
                if cost:
                    service_costs.append(cost)
            
            # Calculate totals
            total_low = sum(sc.low_usage_monthly for sc in service_costs)
            total_medium = sum(sc.medium_usage_monthly for sc in service_costs)
            total_high = sum(sc.high_usage_monthly for sc in service_costs)
            
            # Group by category
            cost_by_category = self._group_by_category(service_costs)
            
            # Generate optimization recommendations
            optimizations = self._generate_optimizations(
                service_costs,
                cost_input.architecture.services
            )
            
            # Generate assumptions
            assumptions = self._generate_assumptions(cost_input.usage_profile)
            
            # Generate citations
            citations = self._generate_pricing_citations()
            
            # Build output
            output = CostOutput(
                target_cloud=CloudPlatform.AZURE,
                region=cost_input.region,
                currency="USD",
                time_period="monthly",
                service_costs=service_costs,
                total_monthly_cost_low=round(total_low, 2),
                total_monthly_cost_medium=round(total_medium, 2),
                total_monthly_cost_high=round(total_high, 2),
                cost_by_category=cost_by_category,
                cost_optimization_recommendations=optimizations,
                assumptions=assumptions,
                confidence_level="medium",
                sources=citations
            )
            
            self.logger.info(
                f"Cost estimation complete: Low=${total_low:.2f}, "
                f"Medium=${total_medium:.2f}, High=${total_high:.2f}"
            )
            
            return output
        
        except Exception as e:
            self.logger.error(f"Error estimating costs: {e}", exc_info=True)
            error = self._create_error(
                f"Failed to estimate costs: {str(e)}",
                error_type=ErrorType.UNKNOWN_ERROR,
                retryable=True
            )
            raise error
    
    def _calculate_service_cost(
        self,
        service: Dict,
        usage_profile: str
    ) -> ServiceCost:
        """
        Calculate cost for a single service.
        
        Args:
            service: Service selection dict
            usage_profile: 'low', 'medium', or 'high'
            
        Returns:
            ServiceCost instance
        """
        service_name = service["service_name"]
        
        # Get pricing data
        pricing = self.AZURE_PRICING.get(service_name)
        if not pricing:
            self.logger.warning(f"No pricing data for {service_name}, using estimate")
            return self._create_default_cost(service_name, service["category"])
        
        # Calculate based on service type
        if service_name == "Azure App Service":
            return self._calculate_app_service_cost(service, pricing)
        elif service_name == "Azure Functions":
            return self._calculate_functions_cost(service, pricing)
        elif service_name == "Azure Kubernetes Service (AKS)":
            return self._calculate_aks_cost(service, pricing)
        elif service_name == "Azure Container Instances (ACI)":
            return self._calculate_aci_cost(service, pricing)
        elif service_name == "Azure Blob Storage":
            return self._calculate_blob_storage_cost(service, pricing)
        elif service_name == "Azure Queue Storage":
            return self._calculate_queue_storage_cost(service, pricing)
        elif service_name in ["Azure SQL Database", "Azure Database for PostgreSQL", "Azure Database for MySQL"]:
            return self._calculate_database_cost(service, pricing)
        elif service_name == "Azure Cosmos DB":
            return self._calculate_cosmos_cost(service, pricing)
        elif service_name == "Azure Cache for Redis":
            return self._calculate_redis_cost(service, pricing)
        elif service_name in ["Azure Application Gateway", "Azure Front Door", "Azure Load Balancer"]:
            return self._calculate_networking_cost(service, pricing)
        elif service_name in ["Azure Key Vault", "Azure Active Directory (Entra ID)", "Azure Monitor"]:
            return self._calculate_platform_cost(service, pricing)
        else:
            return self._create_default_cost(service_name, service["category"])
    
    def _calculate_app_service_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate Azure App Service cost."""
        config = service.get("configuration", {})
        sku = config.get("sku", "B1 (Basic)")
        replicas = config.get("replicas", 1)
        
        # Get SKU pricing
        sku_pricing = None
        for key in pricing.keys():
            if key in sku:
                sku_pricing = pricing[key]
                break
        
        if not sku_pricing:
            sku_pricing = pricing["B1 (Basic)"]
        
        base_monthly = sku_pricing["monthly"] * replicas
        
        return ServiceCost(
            service_name=service["service_name"],
            category="compute",
            pricing_model="hourly",
            low_usage_monthly=base_monthly * 0.5,  # Scale down 50%
            medium_usage_monthly=base_monthly,
            high_usage_monthly=base_monthly * 2,  # Scale up 2x
            assumptions=UsageAssumptions(
                hours_per_month=730,
                additional_metrics={"replicas": replicas, "sku": sku}
            ),
            pricing_tier=sku,
            pricing_url="https://azure.microsoft.com/en-us/pricing/details/app-service/",
            cost_breakdown={
                "base": base_monthly,
                "scaling": "Included in plan"
            }
        )
    
    def _calculate_functions_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate Azure Functions cost."""
        config = service.get("configuration", {})
        sku = config.get("sku", "Consumption Plan")
        
        if "Consumption" in sku:
            # Consumption plan (serverless)
            return ServiceCost(
                service_name=service["service_name"],
                category="compute",
                pricing_model="per-execution",
                low_usage_monthly=10.0,
                medium_usage_monthly=20.0,
                high_usage_monthly=50.0,
                assumptions=UsageAssumptions(
                    additional_metrics={
                        "executions_per_month": 1_000_000,
                        "avg_duration_ms": 500,
                        "memory_mb": 512
                    }
                ),
                pricing_tier="Consumption",
                pricing_url="https://azure.microsoft.com/en-us/pricing/details/functions/",
                cost_breakdown={
                    "executions": 15.0,
                    "compute_time": 5.0
                }
            )
        else:
            # Premium plan
            base = pricing["Premium"]["monthly"]
            return ServiceCost(
                service_name=service["service_name"],
                category="compute",
                pricing_model="hourly",
                low_usage_monthly=base * 0.5,
                medium_usage_monthly=base,
                high_usage_monthly=base * 2,
                assumptions=UsageAssumptions(hours_per_month=730),
                pricing_tier="Premium",
                pricing_url="https://azure.microsoft.com/en-us/pricing/details/functions/"
            )
    
    def _calculate_aks_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate AKS cost."""
        config = service.get("configuration", {})
        replicas = config.get("replicas", 3)
        
        node_cost = pricing["node_pool_vm"]["D2s_v3"]["monthly"]
        total_monthly = node_cost * replicas
        
        return ServiceCost(
            service_name=service["service_name"],
            category="compute",
            pricing_model="hourly",
            low_usage_monthly=node_cost * 2,  # Min 2 nodes
            medium_usage_monthly=total_monthly,
            high_usage_monthly=node_cost * 10,  # Scale to 10 nodes
            assumptions=UsageAssumptions(
                hours_per_month=730,
                additional_metrics={"nodes": replicas, "vm_size": "D2s_v3"}
            ),
            pricing_tier="Standard",
            pricing_url="https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/",
            cost_breakdown={
                "cluster_management": 0.0,
                "node_pool": total_monthly
            }
        )
    
    def _calculate_aci_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate Azure Container Instances cost."""
        return ServiceCost(
            service_name=service["service_name"],
            category="compute",
            pricing_model="per-second",
            low_usage_monthly=25.0,
            medium_usage_monthly=50.0,
            high_usage_monthly=100.0,
            assumptions=UsageAssumptions(
                additional_metrics={"vcpu": 1, "memory_gb": 2, "hours_per_day": 12}
            ),
            pricing_tier="Pay-per-use",
            pricing_url="https://azure.microsoft.com/en-us/pricing/details/container-instances/"
        )
    
    def _calculate_blob_storage_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate Blob Storage cost."""
        config = service.get("configuration", {})
        storage_gb = config.get("storage_gb", 100)
        settings = config.get("additional_settings", {})
        tier = settings.get("tier", "Hot")
        
        tier_pricing = pricing.get(tier, pricing["Hot"])
        storage_cost = storage_gb * tier_pricing["per_gb"]
        
        return ServiceCost(
            service_name=service["service_name"],
            category="storage",
            pricing_model="per-GB",
            low_usage_monthly=storage_cost * 0.5,
            medium_usage_monthly=storage_cost,
            high_usage_monthly=storage_cost * 3,
            assumptions=UsageAssumptions(
                storage_gb=storage_gb,
                additional_metrics={"tier": tier, "redundancy": settings.get("redundancy", "LRS")}
            ),
            pricing_tier=tier,
            pricing_url="https://azure.microsoft.com/en-us/pricing/details/storage/blobs/",
            cost_breakdown={
                "storage": storage_cost,
                "operations": 5.0
            }
        )
    
    def _calculate_queue_storage_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate Queue Storage cost."""
        return ServiceCost(
            service_name=service["service_name"],
            category="storage",
            pricing_model="per-GB + operations",
            low_usage_monthly=2.0,
            medium_usage_monthly=5.0,
            high_usage_monthly=15.0,
            assumptions=UsageAssumptions(
                additional_metrics={"messages_per_day": 100_000}
            ),
            pricing_tier="Standard",
            pricing_url="https://azure.microsoft.com/en-us/pricing/details/storage/queues/"
        )
    
    def _calculate_database_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate database cost (SQL, PostgreSQL, MySQL)."""
        config = service.get("configuration", {})
        sku = config.get("sku", list(pricing.keys())[0])
        
        # Find matching SKU
        monthly_cost = None
        for key, value in pricing.items():
            if key in sku or sku in key:
                monthly_cost = value.get("monthly", 50.0)
                break
        
        if monthly_cost is None:
            monthly_cost = list(pricing.values())[0].get("monthly", 50.0)
        
        return ServiceCost(
            service_name=service["service_name"],
            category="database",
            pricing_model="monthly",
            low_usage_monthly=monthly_cost,
            medium_usage_monthly=monthly_cost,
            high_usage_monthly=monthly_cost * 2,  # Upgrade tier for high usage
            assumptions=UsageAssumptions(
                storage_gb=config.get("storage_gb", 32),
                additional_metrics={"sku": sku}
            ),
            pricing_tier=sku,
            pricing_url=f"https://azure.microsoft.com/en-us/pricing/details/{service['service_name'].lower().replace(' ', '-')}/"
        )
    
    def _calculate_cosmos_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate Cosmos DB cost."""
        return ServiceCost(
            service_name=service["service_name"],
            category="database",
            pricing_model="hourly",
            low_usage_monthly=75.0,
            medium_usage_monthly=150.0,
            high_usage_monthly=400.0,
            assumptions=UsageAssumptions(
                storage_gb=10,
                additional_metrics={"throughput_ru": 400, "api": "SQL (Core)"}
            ),
            pricing_tier="Provisioned Throughput",
            pricing_url="https://azure.microsoft.com/en-us/pricing/details/cosmos-db/",
            cost_breakdown={
                "throughput": 100.0,
                "storage": 50.0
            }
        )
    
    def _calculate_redis_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate Redis Cache cost."""
        config = service.get("configuration", {})
        sku = config.get("sku", "Basic C0")
        
        monthly_cost = pricing.get(sku, pricing["Basic C0"])["monthly"]
        
        return ServiceCost(
            service_name=service["service_name"],
            category="database",
            pricing_model="monthly",
            low_usage_monthly=monthly_cost,
            medium_usage_monthly=monthly_cost,
            high_usage_monthly=pricing["Standard C1"]["monthly"],
            assumptions=UsageAssumptions(
                additional_metrics={"sku": sku, "cache_size_mb": 250}
            ),
            pricing_tier=sku,
            pricing_url="https://azure.microsoft.com/en-us/pricing/details/cache/"
        )
    
    def _calculate_networking_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate networking service cost."""
        service_name = service["service_name"]
        
        if "Application Gateway" in service_name:
            base = pricing["WAF_v2"]["monthly_base"]
            return ServiceCost(
                service_name=service_name,
                category="networking",
                pricing_model="hourly + capacity units",
                low_usage_monthly=base * 0.7,
                medium_usage_monthly=base,
                high_usage_monthly=base * 1.5,
                assumptions=UsageAssumptions(
                    additional_metrics={"capacity_units": 2, "data_processed_gb": 100}
                ),
                pricing_tier="WAF_v2",
                pricing_url="https://azure.microsoft.com/en-us/pricing/details/application-gateway/"
            )
        elif "Front Door" in service_name:
            base = pricing["Standard"]["monthly_estimate"]
            return ServiceCost(
                service_name=service_name,
                category="networking",
                pricing_model="monthly + data transfer",
                low_usage_monthly=base * 0.5,
                medium_usage_monthly=base,
                high_usage_monthly=base * 2,
                assumptions=UsageAssumptions(
                    additional_metrics={"data_transfer_gb": 500}
                ),
                pricing_tier="Standard",
                pricing_url="https://azure.microsoft.com/en-us/pricing/details/frontdoor/"
            )
        else:  # Load Balancer
            base = pricing["Standard"]["monthly"]
            return ServiceCost(
                service_name=service_name,
                category="networking",
                pricing_model="monthly",
                low_usage_monthly=base,
                medium_usage_monthly=base,
                high_usage_monthly=base,
                pricing_tier="Standard",
                pricing_url="https://azure.microsoft.com/en-us/pricing/details/load-balancer/"
            )
    
    def _calculate_platform_cost(self, service: Dict, pricing: Dict) -> ServiceCost:
        """Calculate platform service cost (Key Vault, AAD, Monitor)."""
        service_name = service["service_name"]
        
        if "Key Vault" in service_name:
            cost = pricing["monthly_estimate"]
        elif "Active Directory" in service_name or "Entra" in service_name:
            cost = pricing["Free"]["monthly"]
        else:  # Monitor
            cost = pricing["monthly_estimate"]
        
        return ServiceCost(
            service_name=service_name,
            category="security" if "Key Vault" in service_name or "Active Directory" in service_name else "monitoring",
            pricing_model="per-operation" if "Key Vault" in service_name else "per-GB",
            low_usage_monthly=cost * 0.5,
            medium_usage_monthly=cost,
            high_usage_monthly=cost * 2,
            pricing_tier="Standard",
            pricing_url=f"https://azure.microsoft.com/en-us/pricing/"
        )
    
    def _create_default_cost(self, service_name: str, category: str) -> ServiceCost:
        """Create default cost estimate for unknown services."""
        return ServiceCost(
            service_name=service_name,
            category=category,
            pricing_model="estimated",
            low_usage_monthly=25.0,
            medium_usage_monthly=50.0,
            high_usage_monthly=100.0,
            assumptions=UsageAssumptions(),
            pricing_tier="Standard",
            pricing_url="https://azure.microsoft.com/en-us/pricing/"
        )
    
    def _group_by_category(self, service_costs: List[ServiceCost]) -> Dict[str, float]:
        """Group costs by category."""
        by_category = {}
        for sc in service_costs:
            if sc.category not in by_category:
                by_category[sc.category] = 0.0
            by_category[sc.category] += sc.medium_usage_monthly
        
        return {k: round(v, 2) for k, v in by_category.items()}
    
    def _generate_optimizations(
        self, service_costs: List[ServiceCost], services: List[Dict]
    ) -> List[CostOptimization]:
        """Generate cost optimization recommendations."""
        optimizations = []
        
        # Reserved instances for always-on services
        compute_services = [sc for sc in service_costs if sc.category == "compute"]
        if compute_services:
            optimizations.append(
                CostOptimization(
                    category="compute",
                    recommendation="Consider Azure Reserved Instances for 1-year or 3-year commitments. Save up to 72% on compute costs.",
                    estimated_savings_monthly=sum(sc.medium_usage_monthly for sc in compute_services) * 0.30,
                    effort="low"
                )
            )
        
        # Storage lifecycle policies
        storage_services = [sc for sc in service_costs if sc.category == "storage"]
        if storage_services:
            optimizations.append(
                CostOptimization(
                    category="storage",
                    recommendation="Implement lifecycle policies to move infrequently accessed data to Cool or Archive tiers. Save up to 50% on storage costs.",
                    estimated_savings_monthly=sum(sc.medium_usage_monthly for sc in storage_services) * 0.25,
                    effort="medium"
                )
            )
        
        # Auto-scaling
        optimizations.append(
            CostOptimization(
                category="general",
                recommendation="Enable auto-scaling to match capacity with demand. Prevent over-provisioning during low-traffic periods.",
                estimated_savings_monthly=50.0,
                effort="low"
            )
        )
        
        # Azure Hybrid Benefit
        optimizations.append(
            CostOptimization(
                category="licensing",
                recommendation="If you have existing Windows Server or SQL Server licenses, use Azure Hybrid Benefit to save up to 85%.",
                estimated_savings_monthly=None,  # Depends on licenses
                effort="low"
            )
        )
        
        return optimizations
    
    def _generate_assumptions(self, usage_profile: str) -> List[str]:
        """Generate cost assumptions."""
        return [
            f"Usage profile: {usage_profile.capitalize()}",
            "Region: East US (pricing varies by region)",
            "Pricing: Pay-As-You-Go rates (November 2025)",
            "No Reserved Instances or Savings Plans applied",
            "Standard support tier (Basic is free)",
            "Data transfer within same region is free",
            "Outbound data transfer: ~100 GB/month included",
            "±30% accuracy expected (POC estimate)",
        ]
    
    def _generate_pricing_citations(self) -> List[Citation]:
        """Generate pricing citations."""
        return [
            Citation(
                title="Azure Pricing Calculator",
                url="https://azure.microsoft.com/en-us/pricing/calculator/",
                relevance="Interactive cost estimation tool",
                accessed_at=datetime.now()
            ),
            Citation(
                title="Azure Pricing",
                url="https://azure.microsoft.com/en-us/pricing/",
                relevance="Official Azure pricing information",
                accessed_at=datetime.now()
            ),
            Citation(
                title="Azure Cost Management",
                url="https://azure.microsoft.com/en-us/services/cost-management/",
                relevance="Cost optimization and management tools",
                accessed_at=datetime.now()
            ),
        ]
