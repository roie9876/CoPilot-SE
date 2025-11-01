"""
External services for Co-Pilot SE.

This package contains clients for external APIs:
- Azure OpenAI (GPT-5)
- Bing Search API
- YouTube Data API (optional)
"""

from .openai_client import AzureOpenAIClient
from .bing_search import BingSearchClient

__all__ = [
    "AzureOpenAIClient",
    "BingSearchClient",
]
