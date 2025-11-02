"""
Azure AI Search Client (formerly Bing Search API) - Online data retrieval for Co-Pilot SE.

IMPORTANT: Bing Search API has been migrated to Azure AI Services.
Direct Bing Search endpoint is deprecated. Use Azure AI Foundry instead.

This client provides access to Azure AI Search for:
- Cloud service documentation
- Pricing information
- Best practices and tutorials
- Official product pages
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.schemas import Citation


class BingSearchClient:
    """
    Client for Azure AI Search (formerly Bing Search API v7.0).
    
    NOTE: This client now uses Azure AI Foundry endpoint instead of direct Bing Search.
    The legacy Bing Search API endpoint has been deprecated.
    
    Features:
    - Web search with filtering via Azure AI Services
    - Result ranking and relevance scoring
    - Citation extraction
    - Rate limiting and error handling
    - Result caching (optional)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        results_per_page: int = 10,
    ):
        """
        Initialize Azure AI Search client (formerly Bing Search).
        
        Args:
            api_key: Azure AI Search API key (defaults to env var AZURE_AI_SEARCH_API_KEY)
            endpoint: Azure AI Search endpoint (defaults to env var AZURE_AI_SEARCH_ENDPOINT)
            results_per_page: Number of results per page (default: 10, max: 50)
        """
        self.logger = logging.getLogger("BingSearchClient")
        
        # Try new Azure AI Search variables first, fall back to legacy Bing variables
        self.api_key = (
            api_key 
            or os.getenv("AZURE_AI_SEARCH_API_KEY") 
            or os.getenv("BING_SEARCH_API_KEY")
        )
        
        self.endpoint = (
            endpoint 
            or os.getenv("AZURE_AI_SEARCH_ENDPOINT")
            or os.getenv("BING_SEARCH_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")
        )
        
        # If using Azure AI Foundry, append the search path
        if "cognitiveservices.azure.com" in self.endpoint:
            if not self.endpoint.endswith("/"):
                self.endpoint += "/"
            self.endpoint += "bing/v7.0/search"
            self.logger.info("Using Azure AI Foundry endpoint for Bing Search")
        
        self.results_per_page = min(results_per_page, 50)  # Max is 50
        
        if not self.api_key:
            raise ValueError(
                "Azure AI Search API key must be provided or set in environment variable "
                "AZURE_AI_SEARCH_API_KEY or BING_SEARCH_API_KEY"
            )
        
        # Request headers
        self.headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        
        # Usage tracking
        self.total_searches = 0
        
        self.logger.info("BingSearchClient initialized")

    def search(
        self,
        query: str,
        count: int = 10,
        market: str = "en-US",
        safe_search: str = "Moderate",
        filters: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform a Bing web search.
        
        Args:
            query: Search query string
            count: Number of results to return (default: 10, max: 50)
            market: Market code (default: en-US)
            safe_search: Safe search level (Off, Moderate, Strict)
            filters: Optional list of site filters (e.g., ["site:microsoft.com"])
            
        Returns:
            List of search result dictionaries
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Apply site filters if provided
            if filters:
                for filter_term in filters:
                    query += f" {filter_term}"
            
            self.logger.info(f"Searching Bing: '{query}' (count: {count})")
            
            # Build request parameters
            params = {
                "q": query,
                "count": min(count, 50),
                "mkt": market,
                "safeSearch": safe_search,
                "textDecorations": False,
                "textFormat": "Raw",
            }
            
            # Make API request
            response = requests.get(
                self.endpoint,
                headers=self.headers,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            results = data.get("webPages", {}).get("value", [])
            
            self.total_searches += 1
            self.logger.info(f"Found {len(results)} results")
            
            return results
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Bing Search API call failed: {e}")
            raise Exception(f"Bing Search API error: {e}")

    def search_cloud_docs(
        self,
        query: str,
        cloud_platform: str,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for official cloud platform documentation.
        
        Args:
            query: Search query
            cloud_platform: Cloud platform (azure, aws, gcp, oracle)
            count: Number of results (default: 10)
            
        Returns:
            List of search results from official documentation sites
        """
        # Map cloud platforms to official doc sites
        doc_sites = {
            "azure": "site:learn.microsoft.com OR site:docs.microsoft.com",
            "aws": "site:docs.aws.amazon.com OR site:aws.amazon.com",
            "gcp": "site:cloud.google.com",
            "oracle": "site:docs.oracle.com OR site:oracle.com",
        }
        
        site_filter = doc_sites.get(cloud_platform.lower(), "")
        
        # Construct search query
        full_query = f"{query} {site_filter}" if site_filter else query
        
        return self.search(
            query=full_query,
            count=count,
            filters=[],  # Already included in query
        )

    def search_pricing_info(
        self,
        service_name: str,
        cloud_platform: str,
        count: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for cloud service pricing information.
        
        Args:
            service_name: Service name (e.g., "App Service", "Lambda")
            cloud_platform: Cloud platform (azure, aws, gcp, oracle)
            count: Number of results (default: 5)
            
        Returns:
            List of pricing-related search results
        """
        # Construct pricing-focused query
        query = f"{service_name} pricing {cloud_platform}"
        
        # Platform-specific pricing sites
        pricing_sites = {
            "azure": "site:azure.microsoft.com/pricing OR site:azure.com/pricing",
            "aws": "site:aws.amazon.com/pricing OR site:calculator.aws",
            "gcp": "site:cloud.google.com/pricing OR site:cloud.google.com/products",
            "oracle": "site:oracle.com/cloud/pricing",
        }
        
        site_filter = pricing_sites.get(cloud_platform.lower(), "")
        full_query = f"{query} {site_filter}" if site_filter else query
        
        return self.search(
            query=full_query,
            count=count,
            filters=[],
        )

    def search_best_practices(
        self,
        topic: str,
        cloud_platform: str,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for cloud best practices and architecture patterns.
        
        Args:
            topic: Topic or service (e.g., "microservices", "high availability")
            cloud_platform: Cloud platform (azure, aws, gcp, oracle)
            count: Number of results (default: 10)
            
        Returns:
            List of best practices search results
        """
        query = f"{topic} best practices architecture {cloud_platform}"
        
        # Include Well-Architected Framework sites
        waf_sites = {
            "azure": "site:learn.microsoft.com/azure/well-architected",
            "aws": "site:aws.amazon.com/architecture/well-architected",
            "gcp": "site:cloud.google.com/architecture",
            "oracle": "site:docs.oracle.com/en/solutions",
        }
        
        site_filter = waf_sites.get(cloud_platform.lower(), "")
        full_query = f"{query} {site_filter}" if site_filter else query
        
        return self.search(
            query=full_query,
            count=count,
            filters=[],
        )

    def extract_citations(self, search_results: List[Dict[str, Any]]) -> List[Citation]:
        """
        Extract citations from Bing search results.
        
        Args:
            search_results: List of Bing search result dictionaries
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        for result in search_results:
            try:
                citation = Citation(
                    title=result.get("name", "Untitled"),
                    url=result.get("url", ""),
                    accessed_at=datetime.utcnow().isoformat(),
                    snippet=result.get("snippet", "")[:200],  # Limit snippet length
                )
                citations.append(citation)
                
            except Exception as e:
                self.logger.warning(f"Failed to extract citation: {e}")
                continue
        
        self.logger.info(f"Extracted {len(citations)} citations from {len(search_results)} results")
        
        return citations

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get search usage statistics.
        
        Returns:
            Dictionary with total_searches
        """
        return {
            "total_searches": self.total_searches,
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.total_searches = 0
        self.logger.info("Usage statistics reset")
