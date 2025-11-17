"""
Agent Framework client wrapper for Co-Pilot SE.
Replaces azure_agent_client.py with modern Agent Framework SDK.

This module provides a high-level interface to the Microsoft Agent Framework,
which combines Semantic Kernel and AutoGen patterns for agent development.
"""

from __future__ import annotations

from typing import Optional, List, Any, TYPE_CHECKING
import os

if TYPE_CHECKING:  # pragma: no cover - typing only
    from agent_framework import ChatAgent, HostedWebSearchTool
    from agent_framework.azure import AzureOpenAIChatClient
    from azure.identity import DefaultAzureCredential
else:  # pragma: no cover - runtime fallback for optional dependency
    ChatAgent = HostedWebSearchTool = AzureOpenAIChatClient = Any  # type: ignore[assignment]
    DefaultAzureCredential = Any  # type: ignore[assignment]

try:  # pragma: no cover - import side effects only
    from agent_framework import ChatAgent as _ChatAgentRuntime, HostedWebSearchTool as _HostedWebSearchToolRuntime
    from agent_framework.azure import AzureOpenAIChatClient as _AzureOpenAIChatClientRuntime
    from azure.identity import DefaultAzureCredential as _DefaultAzureCredentialRuntime
    ChatAgent = _ChatAgentRuntime  # type: ignore[assignment]
    HostedWebSearchTool = _HostedWebSearchToolRuntime  # type: ignore[assignment]
    AzureOpenAIChatClient = _AzureOpenAIChatClientRuntime  # type: ignore[assignment]
    DefaultAzureCredential = _DefaultAzureCredentialRuntime  # type: ignore[assignment]
    _AGENT_FRAMEWORK_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - handled at runtime/test environments
    _AGENT_FRAMEWORK_AVAILABLE = False


class AgentFrameworkClient:
    """
    Wrapper for Agent Framework SDK operations.
    
    Provides methods to create ChatAgents with Azure OpenAI backend and
    optional Bing Grounding tool for web search capabilities.
    """
    
    def __init__(self):
        """
        Initialize Agent Framework client with Azure OpenAI configuration.
        
        Reads configuration from environment variables:
        - AZURE_OPENAI_ENDPOINT: Azure OpenAI service endpoint
        - MODEL_DEPLOYMENT_NAME: Model deployment name (e.g., 'gpt-4', 'gpt-5')
        - BING_CONNECTION_ID: Bing Grounding connection ID (for web search)
        
        Uses DefaultAzureCredential for authentication (supports Azure CLI,
        managed identity, service principal, etc.)
        """
        if not _AGENT_FRAMEWORK_AVAILABLE:
            raise ModuleNotFoundError(
                "The 'agent_framework' package is required to instantiate AgentFrameworkClient. "
                "Install the Microsoft Agent Framework SDK in the active environment."
            )

        # Azure OpenAI configuration
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not self.openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
        
        self.model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4")
        self.bing_connection_id = os.getenv("BING_CONNECTION_ID")
        
        # Create Azure credential
        self.credential = DefaultAzureCredential()
        
        # Create Azure OpenAI chat client using Agent Framework's Azure wrapper
        # This implements the ChatClient protocol that ChatAgent requires
        self.chat_client = AzureOpenAIChatClient(
            endpoint=self.openai_endpoint,
            credential=self.credential,
            deployment_name=self.model_deployment
        )
    
    def create_agent(
        self,
        name: str,
        instructions: str,
        enable_bing: bool = False,
        model: Optional[str] = None,
    ) -> Any:
        """Create a ChatAgent with specified configuration.

        Args:
            name: Agent name/identifier
            instructions: System prompt that defines the agent's behavior
            enable_bing: Whether to enable Bing Grounding for web search
            model: Optional model override (defaults to MODEL_DEPLOYMENT_NAME)

        Returns:
            ChatAgent: Configured agent instance ready for execution

        Raises:
            ValueError: If Bing is enabled but BING_CONNECTION_ID is not set

        Example:
            >>> client = AgentFrameworkClient()
            >>> agent = client.create_agent(
            ...     name="requirements-agent",
            ...     instructions="Extract requirements from user input.",
            ...     enable_bing=False
            ... )
            >>> result = await agent.run("Design an e-commerce platform")
        """
        tools = []
        
        if enable_bing:
            if not self.bing_connection_id:
                raise ValueError(
                    "BING_CONNECTION_ID environment variable is required "
                    "when enable_bing=True"
                )
            
            # Create Bing Grounding tool for web search
            bing_tool = HostedWebSearchTool(connection_id=self.bing_connection_id)
            tools.append(bing_tool)
        
        # Use model override if provided, otherwise use default
        agent_model = model or self.model_deployment
        
        # Create ChatAgent with Agent Framework
        # The agent automatically handles:
        # - Conversation/thread management
        # - Tool invocation
        # - Response streaming (if requested)
        # - OpenTelemetry tracing
        agent = ChatAgent(
            chat_client=self.chat_client,
            name=name,
            instructions=instructions,
            tools=tools if tools else None,
            model=agent_model,
        )
        
        return agent
    
    def get_chat_client(self) -> Any:
        """
        Get the underlying Azure OpenAI chat client.
        
        Returns:
            AzureOpenAIChatClient: The Agent Framework Azure chat client
            
        Note:
            Useful for advanced scenarios where direct access to the
            chat client is needed (e.g., custom chat completion calls).
        """
        return self.chat_client
    
    def get_model_deployment(self) -> str:
        """
        Get the configured model deployment name.
        
        Returns:
            str: Model deployment name (e.g., 'gpt-4', 'gpt-5')
        """
        return self.model_deployment
    
    def get_bing_connection_id(self) -> Optional[str]:
        """
        Get the Bing Grounding connection ID if configured.
        
        Returns:
            Optional[str]: Bing connection ID or None if not configured
        """
        return self.bing_connection_id
