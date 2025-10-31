# Pre-Push Verification Checklist

Complete this checklist before pushing the Co-Pilot SE repository to GitHub.

## 🔒 Security Checks

- [ ] `.env` file is **NOT** committed (only `.env.example` should be in Git)
- [ ] No API keys, secrets, or passwords in any committed files
- [ ] `.gitignore` includes all sensitive file patterns
- [ ] Azure subscription IDs and tenant IDs are not hardcoded
- [ ] No personal information or internal Microsoft details exposed

## 📁 File Structure

- [ ] All required directories exist:
  - [ ] `docs/` (with 9 documentation files)
  - [ ] `src/` (with `__init__.py`)
  - [ ] `src/agents/` (with `__init__.py` and README)
  - [ ] `src/orchestrator/` (with `__init__.py` and README)
  - [ ] `mcp-server/` (with `package.json`, `tsconfig.json`, README)
  - [ ] `tests/` (with subdirectories: unit, integration, e2e)
  - [ ] `infrastructure/` (with README)
  - [ ] `config/` (with README)
  - [ ] `.github/workflows/` (with 3 workflow files)

## 📄 Configuration Files

- [ ] `.gitignore` exists and is comprehensive
- [ ] `requirements.txt` includes all Python dependencies
- [ ] `mcp-server/package.json` includes all Node.js dependencies
- [ ] `.env.example` is complete and up-to-date
- [ ] `README.md` at root level is accurate
- [ ] `CONTRIBUTING.md` includes contribution guidelines
- [ ] `LICENSE` file is present (Microsoft proprietary)
- [ ] `SECURITY.md` includes security policy
- [ ] `CHANGELOG.md` documents version history

## 📚 Documentation

- [ ] All documentation files are up-to-date:
  - [ ] `docs/00-project-overview.md`
  - [ ] `docs/01-architecture-decisions.md`
  - [ ] `docs/02-system-architecture.md`
  - [ ] `docs/03-agent-specifications.md`
  - [ ] `docs/04-data-sources-strategy.md`
  - [ ] `docs/05-mcp-integration-spec.md`
  - [ ] `docs/07-implementation-roadmap.md`
  - [ ] `docs/08-open-questions.md`
  - [ ] `docs/README.md`
- [ ] No broken internal links between documentation files
- [ ] No TODO or FIXME comments left unresolved in docs

## 🔧 CI/CD

- [ ] `.github/workflows/python-ci.yml` is configured correctly
- [ ] `.github/workflows/mcp-server-ci.yml` is configured correctly
- [ ] `.github/workflows/docs-check.yml` is configured correctly
- [ ] `.markdownlint.json` and `.github/markdown-link-check-config.json` exist

## 🧪 Testing Readiness

- [ ] `tests/` directory structure is in place
- [ ] `tests/__init__.py` exists
- [ ] `tests/README.md` documents testing approach
- [ ] `pytest.ini` or `pyproject.toml` configuration (if needed)

## 🏗️ Infrastructure Readiness

- [ ] `infrastructure/README.md` documents deployment approach
- [ ] Cost estimates are documented (docs/00-project-overview.md)
- [ ] Azure resources are clearly defined

## 🎯 POC Alignment

- [ ] Documentation reflects multi-cloud POC (AWS, GCP, Azure, Oracle)
- [ ] Online-only data strategy is documented (no RAG)
- [ ] 4 specialized agents are specified (not 5)
- [ ] MCP integration is documented
- [ ] POC scope is clearly defined (10 users, 8-10 weeks)
- [ ] Cost estimates reflect simplified architecture (~$839/month)

## 📝 Git Hygiene

- [ ] `.git` directory is initialized
- [ ] Initial commit message is descriptive
- [ ] Default branch is set to `main`
- [ ] Remote repository is added (if applicable)
- [ ] No large binary files committed (use Git LFS if needed)
- [ ] File permissions are correct (executable scripts have +x)

## 🚀 GitHub Repository Settings

- [ ] Repository visibility is set to **Private** (Microsoft Confidential)
- [ ] Repository description is accurate
- [ ] Topics/tags are added (e.g., `azure`, `openai`, `multi-cloud`, `poc`)
- [ ] Branch protection rules planned (optional for POC):
  - [ ] Require pull request reviews
  - [ ] Require status checks to pass (CI workflows)
  - [ ] Require linear history

## ✅ Final Checks

- [ ] Run `git status` to ensure no untracked sensitive files
- [ ] Review staged files with `git diff --cached`
- [ ] Test that `.env` is properly ignored: `git check-ignore -v .env`
- [ ] Verify file count: `git ls-files | wc -l` (should be ~40+ files)
- [ ] All team members notified about new repository

---

## Verification Commands

Run these commands to verify the checklist:

```bash
# Check that .env is ignored
git check-ignore -v .env
# Expected output: .gitignore:X:.env    .env

# List all tracked files
git ls-files

# Check for potential secrets (install git-secrets first)
# git secrets --scan

# Verify no staged sensitive files
git diff --cached --name-only | grep -E '(\.env$|\.key$|\.pem$|secret|password)'
# Expected output: (empty)

# Count total files
git ls-files | wc -l

# Show directory structure
tree -L 2 -a -I '.git|node_modules|__pycache__|*.pyc'
```

---

## Post-Push Tasks

After successfully pushing to GitHub:

1. [ ] Verify all files are visible in GitHub web interface
2. [ ] Check that GitHub Actions workflows are visible (Actions tab)
3. [ ] Configure branch protection rules (if applicable)
4. [ ] Add collaborators and set permissions
5. [ ] Create initial GitHub Project board (optional)
6. [ ] Create first issue/milestone for Phase 2 kickoff
7. [ ] Update internal wiki with repository link
8. [ ] Notify team via email/Teams

---

**Date Completed**: _______________

**Completed By**: _______________

**Repository URL**: _______________
