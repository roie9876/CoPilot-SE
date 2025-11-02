#!/bin/bash
# Quick Test Runner for Co-Pilot SE
# This script helps you run tests easily

set -e  # Exit on error

echo "🧪 Co-Pilot SE Test Runner"
echo "=========================="
echo ""

# Check if we're in the right directory
if [ ! -f "pytest.ini" ]; then
    echo "❌ Error: Must run from project root (where pytest.ini is located)"
    exit 1
fi

# Function to show usage
show_usage() {
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  smoke       Run smoke tests only (fast)"
    echo "  unit        Run all unit tests"
    echo "  coverage    Run tests with coverage report"
    echo "  verbose     Run tests with verbose output"
    echo "  specific    Run a specific test file (provide path)"
    echo "  all         Run all tests (default)"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh smoke"
    echo "  ./run_tests.sh coverage"
    echo "  ./run_tests.sh specific tests/test_smoke.py"
    echo ""
}

# Parse command
COMMAND=${1:-all}

case $COMMAND in
    smoke)
        echo "🔥 Running smoke tests..."
        python -m pytest tests/test_smoke.py -v
        ;;
    
    unit)
        echo "🧪 Running unit tests..."
        python -m pytest tests/ -v -m unit
        ;;
    
    coverage)
        echo "📊 Running tests with coverage..."
        python -m pytest tests/ --cov=src --cov-report=term --cov-report=html
        echo ""
        echo "✅ Coverage report generated in: htmlcov/index.html"
        echo "   Open with: open htmlcov/index.html"
        ;;
    
    verbose)
        echo "🔊 Running tests with verbose output..."
        python -m pytest tests/ -vv -s
        ;;
    
    specific)
        if [ -z "$2" ]; then
            echo "❌ Error: Please provide test file path"
            echo "Example: ./run_tests.sh specific tests/test_smoke.py"
            exit 1
        fi
        echo "🎯 Running specific test: $2"
        python -m pytest "$2" -v
        ;;
    
    all)
        echo "🚀 Running all tests..."
        python -m pytest tests/ -v
        ;;
    
    help|--help|-h)
        show_usage
        exit 0
        ;;
    
    *)
        echo "❌ Unknown command: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac

echo ""
echo "✅ Test run complete!"
