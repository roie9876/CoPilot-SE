"""
Master Orchestrator - Coordinates all 4 specialized agents in a sequential workflow.

The orchestrator implements a linear pipeline:
1. Requirements Agent - Extract and validate requirements
2. Architecture Agent - Design cloud architecture
3. Cost Agent - Estimate infrastructure costs
4. Documentation Agent - Generate HLD documentation

Each stage passes its output to the next stage, with retry logic and error handling.

REFACTORED: Now uses Agent Framework SDK-based agents
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.models.schemas import (
    OrchestratorInput,
    OrchestratorOutput,
    RequirementsInput,
    RequirementsOutput,
    ArchitectureInput,
    ArchitectureOutput,
    CostInput,
    CostOutput,
    DocumentationInput,
    DocumentationOutput,
    WorkflowStatus,
    WorkflowMetadata,
    Citation,
    AgentError,
    AgentException,
    ErrorType,
)
from src.agents.requirements_agent import RequirementsAgent
from src.agents.architecture_agent import ArchitectureAgent
from src.agents.cost_agent import CostAgent
from src.agents.documentation_agent import DocumentationAgent


class MasterOrchestrator:
    """
    Master Orchestrator that coordinates all 4 specialized agents.
    
    Features:
    - Sequential pipeline execution (Requirements → Architecture → Cost → Documentation)
    - Retry logic with exponential backoff
    - Error handling and graceful degradation
    - Citation collection and deduplication
    - Workflow metadata tracking (timings, status, errors)
    - Clarification flow support (pauses if Requirements Agent needs input)
    """

    def __init__(self, max_retries: int = 2, retry_delay: float = 2.0):
        """
        Initialize the Master Orchestrator.
        
        Args:
            max_retries: Maximum number of retries per agent (default: 2)
            retry_delay: Initial delay between retries in seconds (default: 2.0)
        """
        self.logger = logging.getLogger("MasterOrchestrator")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize all agents
        self.requirements_agent = RequirementsAgent()
        self.architecture_agent = ArchitectureAgent()
        self.cost_agent = CostAgent()
        self.documentation_agent = DocumentationAgent()
        
        # Workflow state
        self.workflow_metadata: Dict[str, Any] = {}
        self.all_citations: List[Citation] = []
        self.all_errors: List[AgentError] = []
        
        self.logger.info("MasterOrchestrator initialized")

    async def orchestrate(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> OrchestratorOutput:
        """
        Main orchestration method that executes the full workflow.
        
        Args:
            user_input: Natural language requirements from user
            context: Optional conversation context
            
        Returns:
            OrchestratorOutput with all agent results and metadata
            
        Raises:
            AgentError: If critical workflow failure occurs
        """
        workflow_start = time.time()
        self.logger.info("Starting workflow orchestration")
        
        try:
            # Initialize workflow metadata
            self._initialize_workflow_metadata()
            
            # Stage 1: Requirements Analysis
            self.logger.info("Stage 1: Requirements Analysis")
            requirements_output = await self._execute_requirements_stage(user_input, context)
            
            # Check if clarification is needed
            if requirements_output.clarifying_questions:
                self.logger.warning(f"Clarification needed: {len(requirements_output.clarifying_questions)} questions")
                # For POC, we continue with available information
                # In production, this would pause the workflow and request user input
            
            # Stage 2: Architecture Design
            self.logger.info("Stage 2: Architecture Design")
            architecture_output = await self._execute_architecture_stage(requirements_output)
            
            # Stage 3: Cost Estimation
            self.logger.info("Stage 3: Cost Estimation")
            cost_output = await self._execute_cost_stage(requirements_output, architecture_output)
            
            # Stage 4: Documentation Generation
            self.logger.info("Stage 4: Documentation Generation")
            documentation_output = await self._execute_documentation_stage(
                requirements_output,
                architecture_output,
                cost_output
            )
            
            # Finalize workflow
            workflow_duration = time.time() - workflow_start
            self._finalize_workflow_metadata(workflow_duration, WorkflowStatus.SUCCESS)
            
            # Deduplicate citations
            unique_citations = self._deduplicate_citations(self.all_citations)
            
            self.logger.info(f"Workflow completed successfully in {workflow_duration:.2f}s")
            
            # Convert models to dicts for OrchestratorOutput
            return OrchestratorOutput(
                status=WorkflowStatus.SUCCESS,
                requirements=requirements_output.model_dump(),
                architecture=architecture_output.model_dump(),
                costs=cost_output.model_dump(),
                documentation=documentation_output.model_dump(),
                citations=unique_citations,
                workflow_metadata=WorkflowMetadata(
                    stages_completed=["requirements", "architecture", "cost", "documentation"],
                    total_duration_seconds=workflow_duration,
                    agents_invoked=["RequirementsAgent", "ArchitectureAgent", "CostAgent", "DocumentationAgent"],
                    start_time=datetime.fromtimestamp(workflow_start),
                    end_time=datetime.utcnow()
                ),
                errors=[e.model_dump() for e in self.all_errors] if self.all_errors else [],
            )
            
        except Exception as e:
            workflow_duration = time.time() - workflow_start
            self._finalize_workflow_metadata(workflow_duration, WorkflowStatus.ERROR)
            
            self.logger.error(f"Workflow failed: {e}")
            
            # Create error object
            error = AgentError(
                agent_name="MasterOrchestrator",
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message="Workflow orchestration failed",
                details={"error": str(e), "duration": workflow_duration},
                retryable=False,
            )
            self.all_errors.append(error)
            
            raise AgentException(error)

    async def _execute_requirements_stage(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> RequirementsOutput:
        """Execute Requirements Agent with retry logic."""
        stage_start = time.time()
        
        try:
            requirements_input = RequirementsInput(
                user_input=user_input,
                context=context,
            )
            
            result = await self._invoke_with_retry(
                agent=self.requirements_agent,
                input_data=requirements_input.model_dump(),
                stage_name="Requirements Analysis"
            )
            
            # Collect citations
            if result.citations:
                self.all_citations.extend(result.citations)
            
            # Record stage timing
            self.workflow_metadata["requirements_stage_duration"] = time.time() - stage_start
            self.workflow_metadata["requirements_confidence"] = result.confidence_score
            
            return result
            
        except Exception as e:
            self.logger.error(f"Requirements stage failed: {e}")
            error = AgentError(
                agent_name="RequirementsAgent",
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=f"Requirements analysis failed: {str(e)}",
                details={"error": str(e)},
                retryable=True,
            )
            self.all_errors.append(error)
            raise AgentException(error)

    async def _execute_architecture_stage(self, requirements: RequirementsOutput) -> ArchitectureOutput:
        """Execute Architecture Agent with retry logic."""
        stage_start = time.time()
        
        try:
            architecture_input = ArchitectureInput(
                requirements=requirements,
                target_cloud=requirements.target_cloud,
                context={},
            )
            
            result = await self._invoke_with_retry(
                agent=self.architecture_agent,
                input_data=architecture_input.model_dump(),
                stage_name="Architecture Design"
            )
            
            # Collect citations
            if result.citations:
                self.all_citations.extend(result.citations)
            
            # Record stage timing
            self.workflow_metadata["architecture_stage_duration"] = time.time() - stage_start
            self.workflow_metadata["total_services_selected"] = len(result.services)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Architecture stage failed: {e}")
            error = AgentError(
                agent_name="ArchitectureAgent",
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=f"Architecture design failed: {str(e)}",
                details={"error": str(e)},
                retryable=True,
            )
            self.all_errors.append(error)
            raise AgentException(error)

    async def _execute_cost_stage(
        self,
        requirements: RequirementsOutput,
        architecture: ArchitectureOutput
    ) -> CostOutput:
        """Execute Cost Agent with retry logic."""
        stage_start = time.time()
        
        try:
            cost_input = CostInput(
                architecture=architecture,
                target_cloud=architecture.target_cloud,
                region=architecture.region,
            )
            
            result = await self._invoke_with_retry(
                agent=self.cost_agent,
                input_data=cost_input.model_dump(),
                stage_name="Cost Estimation"
            )
            
            # Collect citations
            if result.citations:
                self.all_citations.extend(result.citations)
            
            # Record stage timing
            self.workflow_metadata["cost_stage_duration"] = time.time() - stage_start
            
            # Extract medium scenario cost
            medium_cost = next(
                (s.total_monthly_cost for s in result.cost_scenarios if s.scenario == "MEDIUM"),
                0.0
            )
            self.workflow_metadata["estimated_monthly_cost"] = medium_cost
            
            return result
            
        except Exception as e:
            self.logger.error(f"Cost stage failed: {e}")
            error = AgentError(
                agent_name="CostAgent",
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=f"Cost estimation failed: {str(e)}",
                details={"error": str(e)},
                retryable=True,
            )
            self.all_errors.append(error)
            raise error

    async def _execute_documentation_stage(
        self,
        requirements: RequirementsOutput,
        architecture: ArchitectureOutput,
        costs: CostOutput
    ) -> DocumentationOutput:
        """Execute Documentation Agent with retry logic."""
        stage_start = time.time()
        
        try:
            documentation_input = DocumentationInput(
                requirements=requirements,
                architecture=architecture,
                costs=costs,
                citations=self.all_citations,
            )
            
            result = await self._invoke_with_retry(
                agent=self.documentation_agent,
                input_data=documentation_input.model_dump(),
                stage_name="Documentation Generation"
            )
            
            # Record stage timing
            self.workflow_metadata["documentation_stage_duration"] = time.time() - stage_start
            
            return result
            
        except Exception as e:
            self.logger.error(f"Documentation stage failed: {e}")
            error = AgentError(
                agent_name="DocumentationAgent",
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=f"Documentation generation failed: {str(e)}",
                details={"error": str(e)},
                retryable=True,
            )
            self.all_errors.append(error)
            raise AgentException(error)

    async def _invoke_with_retry(
        self,
        agent: Any,
        input_data: Any,
        stage_name: str
    ) -> Any:
        """
        Invoke an agent with retry logic and exponential backoff.
        
        Args:
            agent: Agent instance to invoke
            input_data: Input data for the agent
            stage_name: Name of the stage (for logging)
            
        Returns:
            Agent output
            
        Raises:
            AgentError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"{stage_name}: Attempt {attempt + 1}/{self.max_retries + 1}")
                
                result = await agent.process(input_data)
                
                if attempt > 0:
                    self.logger.info(f"{stage_name}: Succeeded on retry {attempt}")
                
                return result
                
            except AgentException as e:
                last_error = e
                
                # Don't retry validation errors
                if e.agent_error.error_type == ErrorType.VALIDATION_ERROR:
                    self.logger.error(f"{stage_name}: Validation error, not retrying")
                    raise e
                
                if attempt < self.max_retries:
                    # Calculate backoff delay
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"{stage_name}: Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {e.agent_error.error_message}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"{stage_name}: All retries exhausted")
                    raise e
            
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"{stage_name}: Unexpected error on attempt {attempt + 1}, retrying in {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"{stage_name}: All retries exhausted")
                    error = AgentError(
                        agent_name=stage_name,
                        error_type=ErrorType.UNKNOWN_ERROR,
                        error_message=f"{stage_name} failed after {self.max_retries + 1} attempts",
                        details={"error": str(e)},
                        retryable=False,
                    )
                    raise AgentException(error)
        
        # Should never reach here, but just in case
        if last_error:
            raise last_error

    def _initialize_workflow_metadata(self) -> None:
        """Initialize workflow metadata dictionary."""
        self.workflow_metadata = {
            "workflow_id": f"workflow-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "started_at": datetime.utcnow().isoformat(),
            "status": WorkflowStatus.IN_PROGRESS.value,
            "agent_versions": {
                "requirements_agent": "1.0.0",
                "architecture_agent": "1.0.0",
                "cost_agent": "1.0.0",
                "documentation_agent": "1.0.0",
            },
        }
        
        # Reset citations and errors
        self.all_citations = []
        self.all_errors = []

    def _finalize_workflow_metadata(self, duration: float, status: WorkflowStatus) -> None:
        """
        Finalize workflow metadata with completion information.
        
        Args:
            duration: Total workflow duration in seconds
            status: Final workflow status
        """
        self.workflow_metadata.update({
            "completed_at": datetime.utcnow().isoformat(),
            "total_duration": duration,
            "status": status.value,
        })

    def _deduplicate_citations(self, citations: List[Citation]) -> List[Citation]:
        """
        Deduplicate citations based on URL.
        
        Args:
            citations: List of citations from all agents
            
        Returns:
            Deduplicated list of citations
        """
        seen_urls = set()
        unique_citations = []
        
        for citation in citations:
            if citation.url not in seen_urls:
                seen_urls.add(citation.url)
                unique_citations.append(citation)
        
        self.logger.info(f"Deduplicated citations: {len(citations)} -> {len(unique_citations)}")
        
        return unique_citations

    # Public API methods for external integration

    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get current workflow status and metadata.
        
        Returns:
            Workflow metadata dictionary
        """
        return self.workflow_metadata.copy()

    def cancel_workflow(self) -> None:
        """
        Cancel the current workflow (best effort).
        
        Note: In this synchronous implementation, cancellation is not supported.
        In a production async implementation, this would set a cancellation flag.
        """
        self.logger.warning("Workflow cancellation requested, but not supported in synchronous mode")
        self.workflow_metadata["status"] = WorkflowStatus.CANCELLED.value
