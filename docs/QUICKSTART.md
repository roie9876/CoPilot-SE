# Co-Pilot SE - Quick Start Guide

This guide will help you get the Co-Pilot SE web portal up and running in minutes.

## Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend runtime  
- **API Keys**:
  - Azure OpenAI API key and endpoint
  - Bing Search API key

## 🚀 Quick Start (5 minutes)

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/CoPilot-SE.git
cd CoPilot-SE

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

Required environment variables:
```env
# Azure OpenAI (REQUIRED)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Bing Search API (REQUIRED)
BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com/v7.0/search
BING_SEARCH_API_KEY=your-bing-key
```

### 3. Start the Application

**Option A: Automatic (Recommended)**
```bash
./start.sh
```

**Option B: Manual**

Terminal 1 - Backend:
```bash
source .venv/bin/activate
cd api
python server.py
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

### 4. Access the Application

- **Web Portal**: http://localhost:5173
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 Usage

1. **Enter Requirements**: Describe your cloud architecture needs
   - Example: "Design an Azure e-commerce platform for 50,000 users with PCI DSS compliance and $5,000/month budget"

2. **Generate**: Click "Generate Architecture" button

3. **View Results**: Explore tabs:
   - **Architecture**: Diagram, services, design rationale
   - **Cost Analysis**: Cost breakdown and optimization tips
   - **Documentation**: Full HLD document (download as .md)

4. **Download**: Save HLD document or copy to clipboard

## 🎯 Example Requests

### Azure E-Commerce Platform
```
Design an Azure e-commerce platform for a retail company supporting 50,000 concurrent users 
with product catalog, shopping cart, payment processing, and order tracking. Requires 99.9% 
uptime, PCI DSS compliance, and auto-scaling. Budget: $5,000-10,000/month.
```

### AWS Serverless API
```
Build a serverless API backend on AWS for a mobile app with 100,000 users. Need user 
authentication, file storage, real-time notifications, and database. Budget: $2,000/month.
```

### GCP Microservices
```
Create a GCP microservices architecture with Kubernetes for a SaaS application. Need container 
orchestration, CI/CD pipeline, monitoring, and logging. Region: us-central1. Budget: $8,000/month.
```

### Oracle Cloud Data Warehouse
```
Design an Oracle Cloud data warehouse solution for analytics with 10TB of data. Need data 
ingestion, transformation, visualization, and ML capabilities. Budget: $15,000/month.
```

## 🔧 Troubleshooting

### Backend Issues

**ImportError: No module named 'src'**
```bash
# Make sure you're in the project root
cd /path/to/CoPilot-SE
source .venv/bin/activate
cd api
python server.py
```

**OpenAI API Error**
- Verify Azure OpenAI endpoint and key in .env
- Check deployment name matches your Azure OpenAI deployment
- Ensure you have sufficient quota

**Bing Search API Error**
- Verify Bing Search API key in .env
- Check you have S1 tier (required for 10K queries/month)
- Ensure endpoint is correct

### Frontend Issues

**npm install fails**
```bash
# Try removing node_modules and reinstalling
rm -rf node_modules package-lock.json
npm install
```

**Can't connect to backend**
- Verify backend is running on http://localhost:8000
- Check CORS configuration in api/server.py
- Try http://127.0.0.1:8000 instead

**Mermaid diagrams not rendering**
- Check browser console for errors
- Verify backend returns valid Mermaid syntax
- Try refreshing the page

### Node Version Issues

**Vite requires Node 20+**
```bash
# Check Node version
node --version

# If < 18, upgrade Node.js or use nvm
nvm install 20
nvm use 20
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_requirements_agent.py

# Run E2E tests (requires API keys)
pytest tests/e2e/
```

Expected output: **35 tests passing, 78% coverage**

## 📊 System Architecture

```
User (Browser)
    ↓
Web Portal (React, localhost:5173)
    ↓
API Server (FastAPI, localhost:8000)
    ↓
Master Orchestrator
    ↓
┌───────────────┬───────────────┬───────────────┬──────────────┐
│ Requirements  │ Architecture  │ Cost          │ Documentation│
│ Agent         │ Agent         │ Agent         │ Agent        │
└───────────────┴───────────────┴───────────────┴──────────────┘
    ↓               ↓               ↓               ↓
    └───────────────┴───────────────┴───────────────┘
                    ↓
          Azure OpenAI GPT-5
                    ↓
          Bing Search API
```

## 🔐 Security Notes

- Never commit .env file to version control
- API keys are only used by backend (never sent to frontend)
- CORS is restricted to localhost for development
- For production, configure proper CORS origins

## 📝 Development

### Adding New Features

1. **Backend**: Create agent in `src/agents/`
2. **Frontend**: Create component in `frontend/src/components/`
3. **API**: Add endpoint in `api/server.py`
4. **Types**: Update `frontend/src/types.ts` and `src/schemas.py`

### Code Quality

```bash
# Format Python code
black src/ tests/

# Lint Python code
flake8 src/ tests/

# Format TypeScript code
cd frontend
npm run lint
```

## 📚 Documentation

- **Main README**: Overview and project structure
- **Agent Prompts**: `.copilot/agent-prompts.md`
- **API Schemas**: `.copilot/api-schemas.md`
- **Workflow**: `.copilot/orchestration-workflow.md`
- **Full Docs**: `docs/README.md`

## 🆘 Getting Help

1. Check troubleshooting section above
2. Review test results: `pytest -v`
3. Check API logs in terminal
4. Open browser console for frontend errors
5. Create GitHub issue with logs

## 🎓 Next Steps

1. ✅ Run the application
2. ✅ Try example requests
3. ✅ Explore generated architectures
4. ✅ Download HLD documents
5. 📖 Read full documentation in `docs/`
6. 🔧 Customize agents for your needs
7. 🚀 Deploy to production (see deployment guide)

## 📦 Production Deployment

### Backend (Azure Functions)
```bash
# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4

# Deploy
func azure functionapp publish <app-name>
```

### Frontend (Azure Static Web Apps)
```bash
# Build
cd frontend
npm run build

# Deploy (manual or via GitHub Actions)
# See docs/05-deployment-plan.md for details
```

## ⚡ Performance Tips

- **Backend**: Use Azure Functions consumption plan for auto-scaling
- **Frontend**: Enable CDN for static assets
- **Caching**: Implement Redis for frequently requested architectures
- **Database**: Add session storage for conversation history (future)

## 🙏 Support

For issues, questions, or contributions, please:
1. Check existing documentation
2. Search closed issues
3. Open new issue with details

---

**Version**: 2.0 (Multi-Cloud POC)  
**Last Updated**: November 2025  
**License**: See LICENSE file
