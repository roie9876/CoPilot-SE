#!/bin/bash
# Test deployment dependencies locally before deploying to Azure
# This simulates what Azure Oryx does during deployment

set -e

echo "================================================"
echo "🧪 Testing Azure Deployment Dependencies Locally"
echo "================================================"
echo ""

TEMP_ENV="/tmp/copilot-se-deploy-test"

# Clean up previous test
if [ -d "$TEMP_ENV" ]; then
    echo "🧹 Cleaning up previous test environment..."
    rm -rf "$TEMP_ENV"
fi

# Create fresh Python 3.11 virtual environment (same as Azure)
echo "📦 Creating Python 3.11 virtual environment..."
# Use the Python from your .venv (which is 3.11)
.venv/bin/python -m venv "$TEMP_ENV"

# Activate it
source "$TEMP_ENV/bin/activate"

# Upgrade pip (Azure does this)
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Test installing requirements.txt
echo "🔍 Testing requirements.txt installation..."
echo "   (This is what Azure Oryx will do during deployment)"
echo ""

if pip install --no-cache-dir -r requirements.txt; then
    echo ""
    echo "================================================"
    echo "✅ SUCCESS! All dependencies resolved correctly"
    echo "================================================"
    echo ""
    echo "Your requirements.txt is ready for Azure deployment!"
    echo ""
    
    # Show installed versions of key packages
    echo "Key package versions that will be deployed:"
    pip show azure-core openai redis agent-framework 2>/dev/null | grep -E "^(Name|Version):" || true
    
    # Cleanup
    rm -rf "$TEMP_ENV"
    exit 0
else
    echo ""
    echo "================================================"
    echo "❌ FAILED! Dependency conflict detected"
    echo "================================================"
    echo ""
    echo "This deployment will FAIL on Azure."
    echo "Fix the conflicts above before deploying."
    echo ""
    
    # Cleanup
    rm -rf "$TEMP_ENV"
    exit 1
fi
