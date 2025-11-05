# Requirements Files Structure

## Production (Azure Deployment)
- **`requirements.txt`** - Production dependencies ONLY (24 packages)
  - Used by Azure App Service during deployment
  - No test, dev, or doc dependencies
  - Optimized for fast deployment (~2-3 min)

## Development (Local)
- **`requirements-dev.txt`** - Full development dependencies (70+ packages)
  - Includes all production packages
  - Plus: pytest, pytest-mock, httpx-mock (testing)
  - Plus: black, flake8, mypy, pylint (code quality)
  - Plus: jupyter, ipython (development)
  - Plus: mkdocs (documentation)

## Usage

### Azure Deployment (automatic)
Azure uses `requirements.txt` by default ✅

### Local Development
```bash
# Activate virtual environment
source .venv/bin/activate

# Install all development dependencies
pip install -r requirements-dev.txt
```

### Local Production Testing
```bash
# Test with production dependencies only
pip install -r requirements.txt
```

## Why Two Files?

1. **Faster Azure Deployments** - Installing 24 packages vs 70+ saves ~5 minutes
2. **Smaller Container Size** - Production image is ~500MB smaller
3. **Security** - Don't deploy dev tools to production
4. **Reliability** - Avoid conflicts with test-only packages like `httpx-mock==0.9.1`

## File History
- Originally: Single `requirements.txt` with all dependencies
- Updated: Split for Azure deployment optimization
- `requirements.txt` → renamed to `requirements-dev.txt`
- `requirements-prod.txt` → renamed to `requirements.txt`
