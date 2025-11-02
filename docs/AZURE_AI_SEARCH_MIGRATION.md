# Azure AI Search Migration Guide

## Overview

**IMPORTANT CHANGE**: Microsoft has migrated Bing Search API to Azure AI Services. The direct Bing Search endpoint (`https://api.bing.microsoft.com/v7.0/search`) is deprecated and will be discontinued.

All Bing Search functionality is now accessed through **Azure AI Foundry**.

## What Changed?

### Before (Deprecated)
```bash
BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com/v7.0/search
BING_SEARCH_API_KEY=your-bing-api-key
```

### After (Current)
```bash
AZURE_AI_SEARCH_ENDPOINT=https://your-ai-foundry.cognitiveservices.azure.com/
AZURE_AI_SEARCH_API_KEY=your-azure-ai-key
AZURE_AI_SEARCH_DEPLOYMENT_NAME=bing-search
```

## Migration Steps

### 1. Access Azure AI Foundry

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure AI Foundry** (formerly Azure Cognitive Services)
3. Create or select your AI Foundry resource

### 2. Deploy Bing Search

1. In your AI Foundry resource, go to **Deployments**
2. Click **+ Create deployment**
3. Select **Bing Search** from available services
4. Name your deployment (e.g., `bing-search`)
5. Select pricing tier (S1 recommended for POC)
6. Click **Create**

### 3. Get API Keys

1. In your AI Foundry resource, go to **Keys and Endpoint**
2. Copy **Key 1** or **Key 2**
3. Copy the **Endpoint URL**

Example endpoint format:
```
https://copilot-se-foundry.cognitiveservices.azure.com/
```

### 4. Update Environment Variables

Update your `.env` file:

```bash
# Old (remove these)
# BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com/v7.0/search
# BING_SEARCH_API_KEY=old-bing-key

# New (add these)
AZURE_AI_SEARCH_ENDPOINT=https://your-ai-foundry.cognitiveservices.azure.com/
AZURE_AI_SEARCH_API_KEY=your-azure-ai-key
AZURE_AI_SEARCH_DEPLOYMENT_NAME=bing-search
```

### 5. Restart Your Application

```bash
# Stop backend if running
pkill -f 'python.*server.py'

# Start backend with new configuration
./test_backend.sh
```

## Code Changes

### Automatic Migration

The `BingSearchClient` class has been updated to automatically handle both:
- ✅ **New Azure AI Foundry endpoints** (recommended)
- ✅ **Legacy Bing Search endpoints** (for backward compatibility)

### Endpoint Detection

The client automatically detects Azure AI Foundry endpoints:

```python
# If endpoint contains 'cognitiveservices.azure.com'
if "cognitiveservices.azure.com" in self.endpoint:
    # Append Bing Search API path
    self.endpoint += "bing/v7.0/search"
```

### Variable Fallback Order

The client checks environment variables in this order:

1. `AZURE_AI_SEARCH_API_KEY` (new, recommended)
2. `BING_SEARCH_API_KEY` (legacy, for compatibility)

```python
self.api_key = (
    api_key 
    or os.getenv("AZURE_AI_SEARCH_API_KEY") 
    or os.getenv("BING_SEARCH_API_KEY")
)
```

## Benefits of Azure AI Foundry

### Enhanced Features
- ✅ **Unified API access** for all Azure AI services
- ✅ **Better quota management** across services
- ✅ **Improved monitoring** via Azure Monitor
- ✅ **Integrated billing** with Azure subscription
- ✅ **Enterprise security** with Azure AD integration

### Consistency
- ✅ Same authentication as Azure OpenAI
- ✅ Consistent endpoint structure
- ✅ Unified API key management
- ✅ Better rate limiting control

## Pricing

Bing Search pricing remains the same:
- **S1 Tier**: $7 per 1,000 transactions
- **POC Quota**: 10,000 queries/month recommended

## Troubleshooting

### Error: "Invalid API key"

**Solution**: Verify you're using the correct key from Azure AI Foundry (not the old Bing Search key)

```bash
# Check your key in Azure Portal
# Azure AI Foundry > Keys and Endpoint > Key 1
```

### Error: "Endpoint not found"

**Solution**: Ensure endpoint is correct format

```bash
# Correct format:
AZURE_AI_SEARCH_ENDPOINT=https://your-resource.cognitiveservices.azure.com/

# Note: No trailing /bing/v7.0/search (client adds this automatically)
```

### Error: "Deployment not found"

**Solution**: Verify Bing Search deployment exists in Azure AI Foundry

```bash
# In Azure Portal:
# Azure AI Foundry > Deployments > Check for 'bing-search'
```

### Search Results Empty

**Solution**: Check rate limits and quotas

```bash
# In Azure Portal:
# Azure AI Foundry > Metrics > Check API calls
```

## Testing

### Verify Configuration

```bash
# Test backend with new configuration
./test_backend.sh

# Should see: ✅ Backend server is running!
```

### Test Search Functionality

```python
from src.services.bing_search import BingSearchClient

# Initialize client (auto-detects Azure AI Foundry)
client = BingSearchClient()

# Perform search
results = client.search("Azure App Service pricing")
print(f"Found {len(results)} results")
```

### Check Logs

```bash
# Backend logs show Azure AI Foundry usage
tail -f /tmp/copilot_backend.log

# Should see: "Using Azure AI Foundry endpoint for Bing Search"
```

## Rollback Plan

If you need to temporarily use the old Bing Search API:

```bash
# In .env, use legacy variables
BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com/v7.0/search
BING_SEARCH_API_KEY=your-old-bing-key

# Remove or comment out new variables
# AZURE_AI_SEARCH_ENDPOINT=...
# AZURE_AI_SEARCH_API_KEY=...
```

**Note**: This is temporary only. Old endpoint will be sunset by Microsoft.

## Migration Checklist

- [ ] Create Azure AI Foundry resource
- [ ] Deploy Bing Search in AI Foundry
- [ ] Copy new endpoint and API key
- [ ] Update `.env` file with new variables
- [ ] Test backend with `./test_backend.sh`
- [ ] Verify search functionality works
- [ ] Check logs for "Using Azure AI Foundry endpoint"
- [ ] Remove old Bing Search API keys
- [ ] Update documentation for team

## Support Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Bing Search API Migration Guide](https://learn.microsoft.com/azure/cognitive-services/bing-web-search/migration-guide)
- [Azure AI Services Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/)

## Timeline

- **October 2024**: Azure AI Foundry GA (General Availability)
- **November 2024**: Bing Search migration to AI Foundry
- **December 2024**: Old endpoint deprecation warnings
- **Q1 2025**: Old endpoint sunset (exact date TBD)

## Questions?

For Co-Pilot SE specific questions:
1. Check `docs/` directory for additional documentation
2. Review `QUICKSTART.md` for setup instructions
3. Open GitHub issue for support

---

**Last Updated**: November 1, 2025  
**Version**: 2.0 (Multi-Cloud POC)
