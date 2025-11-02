# Azure AI Agent Service Setup Guide

**Last Updated:** November 1, 2025  
**Version:** 1.0  
**Prerequisites:** Azure subscription with Contributor/Owner role

---

## 📋 Overview

This guide walks you through setting up **Azure AI Agent Service** with **Grounding with Bing Search** for the Co-Pilot SE application.

**Estimated Time:** 30-45 minutes  
**Required:** Azure Portal access, Azure CLI

---

## 🎯 What You'll Create

1. **Azure AI Foundry Project** (if not exists)
2. **Grounding with Bing Search Resource**
3. **Connection between Bing and AI Foundry**
4. **Service Principal for Authentication** (optional)

---

## Step 1: Verify Azure AI Foundry Project

### 1.1 Check if Project Exists

1. Go to [Azure AI Foundry Portal](https://ai.azure.com)
2. Sign in with your Azure credentials
3. Check if you see a project named **copilot-se-foundry** (or similar)

**If project exists:** Proceed to Step 1.2  
**If no project:** Create one first (see Appendix A)

### 1.2 Get Project Endpoint

1. In Azure AI Foundry Portal, click on your project
2. Click **Settings** in left sidebar
3. Click **Project details**
4. **Copy the "Project endpoint" URL**
   - Format: `https://<name>.services.ai.azure.com/api/projects/<project-id>`
   - Example: `https://copilot-se-foundry.services.ai.azure.com/api/projects/abc123`
5. **Save this for later** - you'll need it for `.env`

### 1.3 Get Model Deployment Name

1. In your project, click **Deployments** in left sidebar
2. Find your GPT-5 or GPT-4 deployment
3. **Copy the deployment name** (e.g., `gpt-5`, `gpt-4-turbo`)
4. **Save this for later**

---

## Step 2: Create Grounding with Bing Search Resource

### 2.1 Create Resource in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** (top left)
3. Search for **"Grounding with Bing Search"**
4. Click **Create**

### 2.2 Configure Resource

Fill in the creation form:

| Field | Value | Notes |
|-------|-------|-------|
| **Subscription** | Your Azure subscription | Same as AI Foundry project |
| **Resource Group** | `copilot-se-rg` | **Use same RG as AI Foundry** |
| **Region** | Sweden Central | **Use same region as AI Foundry** |
| **Name** | `copilot-se-bing-grounding` | Unique name |
| **Pricing Tier** | S1 | 10,000 queries/month, ~$7/month |

5. Click **Review + Create**
6. Review the terms and conditions
7. Click **Create**
8. **Wait 2-3 minutes** for deployment

### 2.3 Verify Resource Created

1. After deployment completes, click **Go to resource**
2. Verify you see the Bing Grounding resource page
3. Note the resource name: `copilot-se-bing-grounding`

---

## Step 3: Connect Bing to AI Foundry Project

### 3.1 Navigate to AI Foundry Portal

1. Go to [Azure AI Foundry Portal](https://ai.azure.com)
2. Click on your project: **copilot-se-foundry**

### 3.2 Add Connection

1. Click **Connected resources** in left sidebar
2. Click **+ New connection** (or **+ Add connection**)
3. Select **Grounding with Bing Search**

### 3.3 Configure Connection

1. **Select resource:** Choose `copilot-se-bing-grounding` from dropdown
2. **Connection name:** `bing-grounding-connection`
3. **Authentication:** Use default (Key-based)
4. Click **Add connection**

### 3.4 Get Connection ID

**CRITICAL:** You need to copy the exact Connection ID.

1. After connection is created, it appears in the **Connected resources** list
2. Click on the connection name: `bing-grounding-connection`
3. In the connection details, find the **Connection ID**
4. **Copy the full ID** - it should look like:
   ```
   /subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/copilot-se-rg/providers/Microsoft.CognitiveServices/accounts/copilot-se-foundry/projects/copilot-se-project/connections/bing-grounding-connection
   ```
5. **Save this for later** - you'll need it for `.env`

**Alternative method to get Connection ID:**
```bash
# Using Azure CLI
az cognitiveservices account show \
  --name copilot-se-foundry \
  --resource-group copilot-se-rg \
  --query "id" -o tsv

# Then append: /projects/<project-name>/connections/bing-grounding-connection
```

---

## Step 4: Configure Authentication

### 4.1 Choose Authentication Method

Azure AI Agent Service supports multiple authentication methods:

**Option A: Azure CLI (Recommended for development)**
- Simple, no credentials in code
- Requires `az login`

**Option B: Service Principal (Recommended for production)**
- More secure
- Requires creating service principal

**Option C: Managed Identity (For Azure-hosted apps)**
- Best for production
- Only works when app runs in Azure

### 4.2 Option A: Azure CLI (Development)

```bash
# Install Azure CLI if not installed
brew install azure-cli  # macOS
# or download from https://docs.microsoft.com/cli/azure/install-azure-cli

# Login
az login

# Set subscription (if you have multiple)
az account set --subscription "Your Subscription Name"

# Verify
az account show
```

**That's it!** The app will use your Azure CLI credentials automatically.

### 4.3 Option B: Service Principal (Production)

```bash
# Create service principal
az ad sp create-for-rbac \
  --name copilot-se-app \
  --role Contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/copilot-se-rg

# Output will include:
# {
#   "appId": "<client-id>",
#   "displayName": "copilot-se-app",
#   "password": "<client-secret>",
#   "tenant": "<tenant-id>"
# }

# Copy these values for .env
```

Then in `.env`:
```bash
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<client-id>
AZURE_CLIENT_SECRET=<client-secret>
```

---

## Step 5: Update .env File

### 5.1 Open .env

```bash
cd /Users/robenhai/CoPilot-SE
nano .env  # or use your preferred editor
```

### 5.2 Update Required Variables

Replace the placeholder values:

```bash
# ===== AZURE AI FOUNDRY PROJECT =====
# From Step 1.2
AZURE_AI_PROJECT=https://copilot-se-foundry.services.ai.azure.com/api/projects/<YOUR-PROJECT-ID>

# From Step 1.3
MODEL_DEPLOYMENT_NAME=gpt-5

# ===== GROUNDING WITH BING SEARCH =====
# From Step 3.4
BING_CONNECTION_ID=/subscriptions/<sub-id>/resourceGroups/copilot-se-rg/providers/Microsoft.CognitiveServices/accounts/copilot-se-foundry/projects/<project>/connections/bing-grounding-connection

# ===== AUTHENTICATION (if using Service Principal) =====
# From Step 4.3 (optional - only if not using Azure CLI)
# AZURE_TENANT_ID=<tenant-id>
# AZURE_CLIENT_ID=<client-id>
# AZURE_CLIENT_SECRET=<client-secret>
```

### 5.3 Verify .env

Double-check:
- [ ] `AZURE_AI_PROJECT` starts with `https://` and ends with `/projects/<id>`
- [ ] `BING_CONNECTION_ID` starts with `/subscriptions/`
- [ ] No extra spaces or quotes around values
- [ ] File is named `.env` (not `.env.txt`)

---

## Step 6: Install Python Packages

### 6.1 Activate Virtual Environment

```bash
cd /Users/robenhai/CoPilot-SE
source .venv/bin/activate
```

### 6.2 Install Azure AI Agent Service Packages

```bash
# Uninstall old Bing package
pip uninstall azure-cognitiveservices-search-websearch -y

# Install new packages
pip install azure-ai-projects==1.0.0b5 azure-ai-agents==1.0.0b5

# Verify installation
pip list | grep azure-ai
```

You should see:
```
azure-ai-agents    1.0.0b5
azure-ai-projects  1.0.0b5
```

---

## Step 7: Test Configuration

### 7.1 Test Azure Authentication

```bash
# Test Azure CLI authentication
az account show

# Should output your subscription details
```

### 7.2 Test Python Imports

```bash
python -c "from azure.ai.projects import AIProjectClient; print('✓ azure-ai-projects')"
python -c "from azure.ai.agents.models import BingGroundingTool; print('✓ azure-ai-agents')"
python -c "from azure.identity import DefaultAzureCredential; print('✓ azure-identity')"
```

All three should print ✓ without errors.

### 7.3 Test Azure AI Project Connection

```bash
python scripts/test_azure_connection.py
```

This script will:
- Test authentication
- Connect to AI Foundry project
- Verify Bing connection
- Create a test agent with Bing tool
- Run a simple test query
- Output: SUCCESS or specific error

---

## Step 8: Verify in Azure Portal

### 8.1 Check Resources Created

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to resource group: `copilot-se-rg`
3. Verify you see:
   - ✅ Azure AI Foundry project
   - ✅ Grounding with Bing Search resource
   - ✅ Azure OpenAI resource

### 8.2 Check Connection in AI Foundry

1. Go to [Azure AI Foundry Portal](https://ai.azure.com)
2. Navigate to your project
3. Click **Connected resources**
4. Verify you see: `bing-grounding-connection` (Status: Connected)

---

## 🎉 Setup Complete!

You're now ready to use Azure AI Agent Service with Bing Grounding.

**Next steps:**
1. Run the backend: `./test_backend.sh`
2. Test an agent: `python scripts/test_agent.py`
3. Run full workflow: `pytest tests/integration/test_azure_agent_service.py`

---

## 🆘 Troubleshooting

### Error: "DefaultAzureCredential failed to retrieve a token"

**Solution:**
```bash
az login
az account set --subscription <subscription-id>
```

### Error: "AZURE_AI_PROJECT environment variable is required"

**Solution:** Check `.env` file - ensure `AZURE_AI_PROJECT` is set correctly.

### Error: "Connection ID not found"

**Solution:** 
1. Go to Azure AI Foundry Portal
2. Check **Connected resources**
3. Verify `bing-grounding-connection` exists
4. Copy the full Connection ID path

### Error: "Agent run failed: BingGroundingTool not configured"

**Solution:** 
1. Verify Bing resource is connected to AI Foundry project
2. Check `BING_CONNECTION_ID` format is correct
3. Ensure connection name matches: `bing-grounding-connection`

### Error: "Region not supported"

**Solution:** Both AI Foundry and Bing Grounding must be in same region (Sweden Central).

### Import Error: "No module named 'azure.ai.projects'"

**Solution:**
```bash
pip install azure-ai-projects==1.0.0b5 azure-ai-agents==1.0.0b5
```

---

## 📚 Appendix A: Create New AI Foundry Project

If you don't have an AI Foundry project:

1. Go to [Azure AI Foundry Portal](https://ai.azure.com)
2. Click **+ New project**
3. Fill in:
   - **Project name:** `copilot-se-foundry`
   - **Subscription:** Your subscription
   - **Resource group:** Create new: `copilot-se-rg`
   - **Region:** Sweden Central
4. Click **Create**
5. Wait 5-10 minutes for provisioning
6. Return to Step 1 of this guide

---

## 📚 Appendix B: Cost Estimation

| Service | Tier | Monthly Cost (USD) |
|---------|------|--------------------|
| Grounding with Bing Search | S1 (10K queries) | ~$7 |
| Azure OpenAI | Pay-per-token | Variable |
| AI Foundry Project | Free | $0 |
| **Total (estimated)** | | **$7-50/month** |

---

## 📚 Additional Resources

- [Azure AI Agent Service Docs](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/)
- [Grounding with Bing Search](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding)
- [Azure CLI Installation](https://docs.microsoft.com/cli/azure/install-azure-cli)
- [DefaultAzureCredential](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential)

---

**Need Help?**
- Check `docs/AZURE_AI_AGENT_SERVICE_MIGRATION.md` for full migration guide
- Review `docs/TROUBLESHOOTING.md` for common issues
- Open issue on GitHub
