"""
Pytest configuration and shared fixtures.

This file contains common test fixtures and configuration for all tests.
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def sample_requirements_input() -> Dict[str, Any]:
    """Sample requirements input for testing."""
    return {
        "user_input": "Build an e-commerce platform on Azure with 10,000 users",
        "context": None,
    }


@pytest.fixture
def sample_azure_requirements_output() -> Dict[str, Any]:
    """Sample requirements output for Azure testing."""
    return {
        "target_cloud": "azure",
        "industry_vertical": "retail",
        "functional_requirements": [
            "Product catalog management",
            "Shopping cart functionality",
            "User authentication",
        ],
        "nonfunctional_requirements": {
            "scalability": ["Support 10,000 concurrent users"],
            "security": ["SSL/TLS encryption", "Secure authentication"],
        },
        "technical_constraints": {
            "budget": ["$5,000/month"],
        },
        "clarifying_questions": [],
        "confidence_score": 0.8,
        "citations": [],
    }


@pytest.fixture
def mock_bing_search_results():
    """Mock Bing Search API results."""
    return [
        {
            "name": "Azure App Service Pricing",
            "url": "https://azure.microsoft.com/pricing/details/app-service/",
            "snippet": "Azure App Service pricing information",
        },
        {
            "name": "Azure Architecture Center",
            "url": "https://learn.microsoft.com/azure/architecture/",
            "snippet": "Best practices for Azure architecture",
        },
    ]


@pytest.fixture
def mock_openai_response():
    """Mock Azure OpenAI response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a mock response from Azure OpenAI"
                }
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }
