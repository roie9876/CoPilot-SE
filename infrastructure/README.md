# Infrastructure

Infrastructure as Code (IaC) for Co-Pilot SE deployment.

## Structure

```
infrastructure/
├── bicep/          # Azure Bicep templates (primary)
├── terraform/      # Terraform configs (optional, multi-cloud)
└── scripts/        # Deployment and setup scripts
```

## Resources

The POC infrastructure includes:
- **Azure OpenAI**: GPT-5 deployment (Sweden Central)
- **Azure Functions**: Serverless compute for agents
- **Azure Cognitive Search**: Bing Search API integration
- **Application Insights**: Monitoring and logging
- **Azure Key Vault**: Secrets management (optional for POC)
- **Azure Cache for Redis**: Optional caching layer

## Cost Estimation

Monthly cost: ~$839/month for 10 users (see [00-project-overview.md](../docs/00-project-overview.md#cost-estimates))

## Deployment (Phase 2)

```bash
# Using Azure Developer CLI (azd)
cd infrastructure
azd init
azd up

# Or using Bicep directly
az deployment group create \
  --resource-group copilot-se-poc \
  --template-file bicep/main.bicep \
  --parameters environment=dev
```

## Implementation Status

⚠️ **Phase 2**: Infrastructure code will be created during the POC deployment phase.
