# Contributing to Co-Pilot SE

Thank you for your interest in contributing to Co-Pilot SE! This document provides guidelines for contributing to the project.

## 🎯 POC Scope

This is a **10-user multi-cloud POC** (8-10 weeks). Contributions should align with the POC scope:
- Multi-cloud support (AWS, GCP, Azure, Oracle Cloud)
- Online-only data strategy (no RAG for POC)
- 4-agent architecture (Master Orchestrator + Requirements + Multi-Cloud Architecture + Cost + Documentation)
- Simplified infrastructure

## 🚀 Getting Started

### Prerequisites

1. **Development Environment:**
   - Python 3.11+
   - Node.js 20 LTS
   - Git
   - VS Code (recommended)

2. **Azure Resources:**
   - Azure OpenAI (GPT-5 or GPT-4 Turbo)
   - Bing Search API key
   - YouTube Data API key
   - Azure AD tenant access

### Setup

```bash
# Clone repository
git clone https://github.com/your-org/copilot-se.git
cd copilot-se

# Python setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# MCP server setup
cd mcp-server
npm install
cd ..

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

## 🔀 Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

### 2. Make Changes

- Write clean, readable code
- Follow coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 3. Test

```bash
# Python tests
pytest tests/ -v

# MCP server tests
cd mcp-server && npm test

# Code quality
black .
flake8
```

### 4. Commit

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```bash
git commit -m "feat: add multi-cloud service mapping"
git commit -m "fix: resolve Bing Search rate limiting issue"
git commit -m "docs: update implementation roadmap"
```

**Commit types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test additions/updates
- `chore:` - Maintenance tasks

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (if UI changes)
- Test results

## 📏 Coding Standards

### Python

- **Style:** PEP 8
- **Formatter:** Black (line length: 88)
- **Linter:** Flake8
- **Type hints:** Required for all functions

```python
def search_bing(query: str, count: int = 10) -> list[dict]:
    """
    Search Bing for the given query.
    
    Args:
        query: Search query string
        count: Number of results to return
        
    Returns:
        List of search results
    """
    # Implementation
    pass
```

### TypeScript (MCP Server)

- **Style:** ESLint + Prettier
- **Type safety:** Strict mode enabled
- **Naming:** camelCase for variables, PascalCase for classes

```typescript
interface SearchResult {
  url: string;
  title: string;
  snippet: string;
}

async function searchBing(query: string, count: number = 10): Promise<SearchResult[]> {
  // Implementation
}
```

### Documentation

- Update relevant `/docs/*.md` files
- Add inline comments for complex logic
- Update README if adding new features
- Include examples in docstrings

## 🧪 Testing

### Unit Tests

```python
# tests/test_agents.py
import pytest
from src.agents.requirements_agent import RequirementsAgent

def test_extract_cloud_platform():
    agent = RequirementsAgent()
    result = agent.detect_cloud("Build an AWS Lambda function")
    assert result == "aws"
```

### Integration Tests

```python
# tests/integration/test_workflow.py
@pytest.mark.integration
async def test_end_to_end_workflow():
    orchestrator = MasterOrchestrator()
    result = await orchestrator.process("Design an AWS e-commerce platform")
    assert result.architecture is not None
    assert result.costs is not None
```

### Test Coverage

Aim for >80% coverage for new code:

```bash
pytest --cov=src --cov-report=html
```

## 📝 Documentation Updates

When contributing, update:

1. **Code documentation** - Docstrings, inline comments
2. **README files** - If adding features or changing setup
3. **Architecture docs** - If changing design (`/docs`)
4. **ADRs** - If making architectural decisions (`/docs/01-architecture-decisions.md`)

## 🐛 Reporting Bugs

Use GitHub Issues with the following template:

**Title:** Brief description

**Description:**
- What happened?
- What did you expect?
- Steps to reproduce
- Environment (OS, Python version, etc.)

**Screenshots/Logs:** If applicable

## 💡 Feature Requests

For POC, feature requests should align with:
- Multi-cloud architecture design
- Online data source improvements
- Agent prompt optimization
- Cost estimation accuracy

Use GitHub Issues with:
- **Use case** - Why is this needed?
- **Proposed solution** - How would it work?
- **Alternatives** - Other approaches considered?

## 🔍 Code Review Process

All PRs require:
1. ✅ Tests passing
2. ✅ Code quality checks passing (black, flake8, eslint)
3. ✅ Documentation updated
4. ✅ At least 1 approval from team member
5. ✅ No merge conflicts

## 🎓 Resources

- [Project Documentation](/docs/README.md)
- [System Architecture](/docs/02-system-architecture.md)
- [Agent Specifications](/docs/03-agent-specifications.md)
- [Implementation Roadmap](/docs/07-implementation-roadmap.md)

## 📞 Questions?

- **Team Channel:** [Co-Pilot SE Development]
- **GitHub Discussions:** For general questions
- **GitHub Issues:** For bugs and feature requests

## 📜 License

This project is licensed under the MIT License. By contributing, you agree that your contributions will be licensed under the same terms. See [LICENSE](LICENSE) for details.

---

**Thank you for contributing to Co-Pilot SE!** 🚀
