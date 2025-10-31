#!/bin/bash

# Git Initialization Script for Co-Pilot SE
# This script initializes the Git repository and prepares it for the first push to GitHub

set -e  # Exit on error

echo "=========================================="
echo "Co-Pilot SE - Git Repository Initialization"
echo "=========================================="
echo ""

# Check if .git directory already exists
if [ -d ".git" ]; then
    echo "⚠️  Git repository already initialized"
    echo "   To start fresh, run: rm -rf .git"
    exit 1
fi

# Initialize Git repository
echo "📦 Initializing Git repository..."
git init
echo "✅ Git repository initialized"
echo ""

# Set main as the default branch
echo "🌿 Setting 'main' as the default branch..."
git branch -M main
echo "✅ Default branch set to 'main'"
echo ""

# Create .env from .env.example (don't commit it)
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created (remember to fill in your actual values)"
    echo "   ⚠️  Never commit the .env file!"
else
    echo "⚠️  .env already exists, skipping creation"
fi
echo ""

# Stage all files
echo "➕ Staging all files..."
git add .
echo "✅ All files staged"
echo ""

# Show status
echo "📊 Git status:"
git status
echo ""

# Create initial commit
echo "💾 Creating initial commit..."
read -p "Enter commit message (default: 'Initial commit - Multi-Cloud POC v2.0.0'): " COMMIT_MSG
COMMIT_MSG=${COMMIT_MSG:-"Initial commit - Multi-Cloud POC v2.0.0"}
git commit -m "$COMMIT_MSG"
echo "✅ Initial commit created"
echo ""

# Prompt for remote repository
echo "🔗 GitHub Remote Repository Setup"
echo "   Before continuing, create a new repository on GitHub:"
echo "   1. Go to https://github.com/new"
echo "   2. Repository name: copilot-se or CoPilot-SE"
echo "   3. Visibility: Private (recommended for Microsoft Confidential)"
echo "   4. DO NOT initialize with README, .gitignore, or license"
echo ""
read -p "Enter the GitHub repository URL (e.g., https://github.com/microsoft/copilot-se.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "⚠️  No repository URL provided"
    echo "   You can add it later with:"
    echo "   git remote add origin <repository-url>"
    echo "   git push -u origin main"
else
    echo "🔗 Adding remote 'origin'..."
    git remote add origin "$REPO_URL"
    echo "✅ Remote 'origin' added"
    echo ""
    
    # Confirm before push
    read -p "Push to GitHub now? (y/n): " PUSH_NOW
    if [ "$PUSH_NOW" = "y" ] || [ "$PUSH_NOW" = "Y" ]; then
        echo "🚀 Pushing to GitHub..."
        git push -u origin main
        echo "✅ Successfully pushed to GitHub!"
        echo ""
        echo "🎉 Repository URL: $REPO_URL"
    else
        echo "⏸️  Skipping push. To push later, run:"
        echo "   git push -u origin main"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Git initialization complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Fill in actual values in .env (never commit this file!)"
echo "2. Review and update documentation as needed"
echo "3. Start Phase 2 implementation (see docs/07-implementation-roadmap.md)"
echo ""
echo "Repository structure:"
git ls-tree --name-only -r HEAD | head -20
echo "   ... (and more)"
echo ""
