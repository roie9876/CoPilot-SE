"""
Base agent class for all specialized agents.

All agents (Requirements, Architecture, Cost, Documentation) inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from datetime import datetime
import logging

from src.models.schemas import AgentError, AgentException, ErrorType

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Provides:
    - Common initialization
    - Logging setup
    - Error handling patterns
    - Metadata tracking
    """
    
    def __init__(self, name: str):
        """
        Initialize agent.
        
        Args:
            name: Agent name (e.g., "RequirementsAgent", "ArchitectureAgent")
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.invocation_count = 0
        self.last_invocation: Optional[datetime] = None
        
        self.logger.info(f"{self.name} initialized")
    
    @abstractmethod
    async def process(self, input_data: Dict) -> Dict:
        """
        Main processing method - must be implemented by subclasses.
        
        Args:
            input_data: Input dictionary matching agent's input schema
            
        Returns:
            Output dictionary matching agent's output schema
            
        Raises:
            AgentError: If processing fails
        """
        pass
    
    def _record_invocation(self) -> None:
        """Record agent invocation for metrics."""
        self.invocation_count += 1
        self.last_invocation = datetime.now()
        self.logger.info(
            f"{self.name} invoked (total invocations: {self.invocation_count})"
        )
    
    def _create_error(
        self,
        error_message: str,
        error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
        details: Optional[Dict] = None,
        retryable: bool = False
    ) -> AgentException:
        """
        Create standardized error response.
        
        Args:
            error_message: Human-readable error description
            error_type: Type of error
            details: Additional error context
            retryable: Whether this error can be retried
            
        Returns:
            AgentException instance (wrapping AgentError model)
        """
        error_model = AgentError(
            agent_name=self.name,
            error_type=error_type,
            error_message=error_message,
            details=details or {},
            retryable=retryable,
            timestamp=datetime.now()
        )
        
        self.logger.error(
            f"{self.name} error: {error_message} "
            f"(type={error_type}, retryable={retryable})"
        )
        
        return AgentException(error_model)
    
    def _validate_input(self, input_data: Dict, required_fields: list) -> None:
        """
        Validate required fields are present in input.
        
        Args:
            input_data: Input data to validate
            required_fields: List of required field names
            
        Raises:
            AgentError: If validation fails
        """
        missing_fields = [
            field for field in required_fields 
            if field not in input_data or input_data[field] is None
        ]
        
        if missing_fields:
            raise self._create_error(
                f"Missing required fields: {', '.join(missing_fields)}",
                error_type=ErrorType.VALIDATION_ERROR,
                details={"missing_fields": missing_fields},
                retryable=False
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent metrics.
        
        Returns:
            Dictionary with agent statistics
        """
        return {
            "agent_name": self.name,
            "invocation_count": self.invocation_count,
            "last_invocation": self.last_invocation.isoformat() if self.last_invocation else None
        }
    
    def __repr__(self) -> str:
        """String representation of agent."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"invocations={self.invocation_count})"
        )
