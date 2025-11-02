"""
Azure AI Agent Service Client - Centralized wrapper for Azure AI Agent operations.

This module provides a unified interface for creating and managing Azure AI Agents
with optional Bing Grounding tool integration.

Features:
- AIProjectClient initialization with DefaultAzureCredential
- Agent creation with Bing Grounding tool
- Thread and message management
- Run execution and status polling
- Citation extraction from agent responses
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    BingGroundingTool,
    Agent,
    AgentThread,
    ThreadMessage,
    ThreadRun,
)
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError


@dataclass
class AgentResponse:
    """
    Response from an Azure AI Agent execution.
    
    Attributes:
        content: The agent's text response
        citations: List of citations from Bing Grounding (if used)
        tool_calls: List of tool calls made by the agent
        status: Run status (completed, failed, etc.)
        error: Error message if run failed
    """
    content: str
    citations: List[Dict[str, str]]
    tool_calls: List[str]
    status: str
    error: Optional[str] = None


class AzureAgentClient:
    """
    Wrapper for Azure AI Agent Service operations.
    
    This class provides a simplified interface for:
    - Creating agents with optional Bing Grounding
    - Running agents with thread-based execution
    - Extracting citations from agent responses
    - Managing agent lifecycle
    
    Environment Variables Required:
        AZURE_AI_PROJECT: Azure AI Foundry project endpoint URL
        MODEL_DEPLOYMENT_NAME: Azure OpenAI model deployment name
        BING_CONNECTION_ID: Connection ID for Bing Grounding (optional)
    
    Authentication:
        Uses DefaultAzureCredential (requires `az login` or environment variables)
    """

    def __init__(self):
        """
        Initialize the Azure AI Agent Service client.
        
        Raises:
            ValueError: If required environment variables are not set
            AzureError: If authentication fails
        """
        self.logger = logging.getLogger("AzureAgentClient")
        
        # Get required environment variables
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = "copilot-se"  # From your Azure resources
        self.project_name = "se-project"  # From your Azure resources
        self.endpoint = "https://copilot-se-foundry.cognitiveservices.azure.com/"
        
        if not self.subscription_id:
            raise ValueError("AZURE_SUBSCRIPTION_ID environment variable is required")
        
        self.model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4")
        self.bing_connection_id = os.getenv("BING_CONNECTION_ID")
        
        # Initialize credential and client
        try:
            self.credential = DefaultAzureCredential()
            self.client = AIProjectClient(
                endpoint=self.endpoint,
                subscription_id=self.subscription_id,
                resource_group_name=self.resource_group,
                project_name=self.project_name,
                credential=self.credential
            )
            self.logger.info(
                f"Initialized Azure AI Agent Service client: "
                f"endpoint={self.endpoint}, "
                f"subscription={self.subscription_id[:8]}..., "
                f"rg={self.resource_group}, project={self.project_name}"
            )
        except AzureError as e:
            self.logger.error(f"Failed to initialize Azure AI Agent Service: {e}")
            raise
    
    def create_agent(
        self,
        name: str,
        instructions: str,
        model: str,
        enable_bing: bool = False,
    ) -> Agent:
        """
        Create an agent with specified configuration.
        
        Args:
            name: Agent name
            instructions: System prompt for the agent
            model: Model deployment name (e.g., 'gpt-4')
            enable_bing: Whether to enable Bing Grounding for web search
            
        Returns:
            Agent: Created agent instance
        """
        tools = []
        tool_resources = None
        
        if enable_bing:
            # Create Bing Grounding tool with connection
            bing_tool = BingGroundingTool(connection_id=self.bing_connection_id)
            tools = bing_tool.definitions
        
        # Create agent with tools
        agent = self.client.agents.create_agent(
            model=model,
            name=name,
            instructions=instructions,
            tools=tools,
        )
        return agent
    
    def create_thread(self) -> AgentThread:
        """
        Create a new conversation thread.
        
        Returns:
            AgentThread: New thread instance
        """
        thread = self.client.agents.threads.create()
        self.logger.debug(f"Created thread: {thread.id}")
        return thread
    
    def create_message(
        self,
        thread_id: str,
        content: str,
        role: str = "user"
    ) -> ThreadMessage:
        """
        Add a message to a thread.
        
        Args:
            thread_id: Thread ID
            content: Message content
            role: Message role (default: "user")
            
        Returns:
            ThreadMessage: Created message
        """
        message = self.client.agents.messages.create(
            thread_id=thread_id,
            role=role,
            content=content
        )
        self.logger.debug(f"Created message in thread {thread_id}")
        return message
    
    def run_agent(
        self,
        thread_id: str,
        agent_id: str,
        additional_instructions: Optional[str] = None
    ) -> ThreadRun:
        """
        Run an agent on a thread and wait for completion.
        
        This method uses create_and_process which automatically:
        - Creates the run
        - Polls for completion
        - Handles tool calls (including Bing Search)
        
        Args:
            thread_id: Thread ID
            agent_id: Agent ID
            additional_instructions: Optional additional instructions for this run
            
        Returns:
            ThreadRun: Completed run with status
        """
        self.logger.info(f"Running agent {agent_id} on thread {thread_id}")
        
        try:
            run = self.client.agents.runs.create_and_process(
                thread_id=thread_id,
                agent_id=agent_id,
                additional_instructions=additional_instructions
            )
            
            self.logger.info(f"Run completed with status: {run.status}")
            
            if run.status == "failed":
                error_msg = getattr(run, 'last_error', 'Unknown error')
                self.logger.error(f"Run failed: {error_msg}")
            
            return run
        except AzureError as e:
            self.logger.error(f"Failed to run agent: {e}")
            raise
    
    def get_messages(self, thread_id: str) -> List[ThreadMessage]:
        """
        Get all messages from a thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            List of messages in chronological order
        """
        messages = self.client.agents.messages.list(thread_id=thread_id)
        return list(messages)
    
    def extract_agent_response(
        self,
        thread_id: str,
        run: ThreadRun
    ) -> AgentResponse:
        """
        Extract the agent's response from a completed run.
        
        This method:
        - Gets the latest assistant message
        - Extracts text content
        - Extracts citations from Bing Grounding annotations
        - Captures tool calls
        
        Args:
            thread_id: Thread ID
            run: Completed run
            
        Returns:
            AgentResponse with content and citations
        """
        messages = self.get_messages(thread_id)
        
        # Find the latest assistant message
        assistant_messages = [m for m in messages if m.role == "assistant"]
        if not assistant_messages:
            return AgentResponse(
                content="",
                citations=[],
                tool_calls=[],
                status=run.status,
                error="No assistant response found"
            )
        
        latest_message = assistant_messages[-1]
        
        # Extract content
        content_parts = []
        citations = []
        
        for content_item in latest_message.content:
            # Extract text
            if hasattr(content_item, 'text'):
                content_parts.append(content_item.text.value)
                
                # Extract citations from annotations
                if hasattr(content_item.text, 'annotations'):
                    for annotation in content_item.text.annotations:
                        if hasattr(annotation, 'url'):
                            citations.append({
                                "text": getattr(annotation, 'text', ''),
                                "url": annotation.url,
                                "source_type": "bing_grounding"
                            })
        
        content = "\n".join(content_parts)
        
        # Extract tool calls from run steps (if needed for debugging)
        tool_calls = []
        try:
            steps = self.client.agents.runs.list_steps(
                thread_id=thread_id,
                run_id=run.id
            )
            for step in steps:
                if hasattr(step, 'step_details') and hasattr(step.step_details, 'tool_calls'):
                    for tool_call in step.step_details.tool_calls:
                        tool_calls.append(tool_call.type)
        except Exception as e:
            self.logger.warning(f"Could not extract tool calls: {e}")
        
        return AgentResponse(
            content=content,
            citations=citations,
            tool_calls=list(set(tool_calls)),
            status=run.status,
            error=getattr(run, 'last_error', None) if run.status == "failed" else None
        )
    
    def delete_agent(self, agent_id: str) -> None:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID to delete
        """
        try:
            self.client.agents.delete_agent(agent_id)
            self.logger.info(f"Deleted agent: {agent_id}")
        except AzureError as e:
            self.logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise
    
    def delete_thread(self, thread_id: str) -> None:
        """
        Delete a thread.
        
        Args:
            thread_id: Thread ID to delete
        """
        try:
            self.client.agents.threads.delete(thread_id)
            self.logger.debug(f"Deleted thread: {thread_id}")
        except AzureError as e:
            self.logger.error(f"Failed to delete thread {thread_id}: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        # Note: credential.close() if using async context
        pass
