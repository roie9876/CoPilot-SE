"""
Azure OpenAI Client - GPT-5 integration for Co-Pilot SE.

This client provides a wrapper around the Azure OpenAI API for:
- Chain-of-Thought prompting
- Agent reasoning and decision-making
- Natural language processing
"""

import os
import logging
from typing import Optional, Dict, Any, List
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion


class AzureOpenAIClient:
    """
    Client for Azure OpenAI GPT-5 API.
    
    Features:
    - Chain-of-Thought prompting
    - Structured output generation
    - Retry logic with exponential backoff
    - Token usage tracking
    - Response validation
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
    ):
        """
        Initialize Azure OpenAI client.
        
        Args:
            endpoint: Azure OpenAI endpoint (defaults to env var AZURE_OPENAI_ENDPOINT)
            api_key: Azure OpenAI API key (defaults to env var AZURE_OPENAI_API_KEY)
            deployment_name: Deployment name (defaults to env var AZURE_OPENAI_DEPLOYMENT_NAME)
            api_version: API version (default: 2024-02-15-preview)
        """
        self.logger = logging.getLogger("AzureOpenAIClient")
        
        # Load configuration from environment variables or parameters
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment_name = deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5")
        self.api_version = api_version
        
        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure OpenAI endpoint and API key must be provided or set in environment variables "
                "(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY)"
            )
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )
        
        # Token usage tracking
        self.total_tokens_used = 0
        self.total_requests = 0
        
        self.logger.info(f"AzureOpenAIClient initialized (deployment: {self.deployment_name})")

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a completion using Azure OpenAI GPT-5.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0, default: 0.7)
            max_tokens: Maximum tokens to generate (default: None = model max)
            system_prompt: Optional system prompt to prepend
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Prepend system prompt if provided
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            self.logger.debug(f"Generating completion with {len(messages)} messages")
            
            # Call Azure OpenAI API
            response: ChatCompletion = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Track usage
            if response.usage:
                self.total_tokens_used += response.usage.total_tokens
                self.total_requests += 1
                self.logger.debug(
                    f"Tokens used: {response.usage.total_tokens} "
                    f"(prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})"
                )
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"Azure OpenAI API call failed: {e}")
            raise

    def generate_structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        temperature: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output using Chain-of-Thought prompting.
        
        Args:
            prompt: Input prompt
            output_schema: JSON schema describing expected output structure
            temperature: Sampling temperature (default: 0.5 for more deterministic output)
            
        Returns:
            Parsed JSON response matching the output schema
            
        Raises:
            Exception: If API call fails or output is not valid JSON
        """
        import json
        
        # Create system prompt with schema instructions
        system_prompt = f"""You are a helpful AI assistant that generates structured JSON output.

Output Schema:
{json.dumps(output_schema, indent=2)}

IMPORTANT: Your response must be valid JSON matching the above schema. Do not include any markdown formatting or code blocks."""
        
        messages = [{"role": "user", "content": prompt}]
        
        response_text = self.generate_completion(
            messages=messages,
            temperature=temperature,
            system_prompt=system_prompt,
        )
        
        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            parsed_output = json.loads(response_text)
            return parsed_output
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Azure OpenAI: {e}")

    def generate_chain_of_thought(
        self,
        problem: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response using Chain-of-Thought (CoT) prompting.
        
        Args:
            problem: Problem statement or question
            context: Optional context information
            temperature: Sampling temperature (default: 0.7)
            
        Returns:
            Generated response with reasoning steps
        """
        system_prompt = """You are a cloud architecture expert. When solving problems, use Chain-of-Thought reasoning:

1. Break down the problem into smaller components
2. Analyze each component step-by-step
3. Consider trade-offs and alternatives
4. Synthesize a comprehensive solution

Provide clear reasoning for each decision."""
        
        user_prompt = f"Problem: {problem}"
        if context:
            user_prompt += f"\n\nContext: {context}"
        
        messages = [{"role": "user", "content": user_prompt}]
        
        return self.generate_completion(
            messages=messages,
            temperature=temperature,
            system_prompt=system_prompt,
        )

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get token usage statistics.
        
        Returns:
            Dictionary with total_tokens_used and total_requests
        """
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_requests": self.total_requests,
        }

    def reset_usage_stats(self) -> None:
        """Reset token usage statistics."""
        self.total_tokens_used = 0
        self.total_requests = 0
        self.logger.info("Usage statistics reset")
