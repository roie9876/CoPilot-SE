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
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.knowledge_graph import KnowledgeGraph

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
    ClarificationQuestion,
    # New stage-based models
    ConversationStage,
    StageOutput,
    StageRecommendation,
    TradeOff,
    StageApprovalResponse,
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

    MAX_CLARIFICATION_ROUNDS = 3

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
        
        # NEW: Initialize Knowledge Graph Orchestrator
        from src.orchestrator.knowledge_graph_orchestrator import KnowledgeGraphOrchestrator
        self.kg_orchestrator = KnowledgeGraphOrchestrator()
        
        # Workflow state
        self.workflow_metadata: Dict[str, Any] = {}
        self.all_citations: List[Citation] = []
        self.all_errors: List[AgentError] = []
        
        # NEW: Knowledge Graph state (for interactive workflow)
        self.current_kg: Optional['KnowledgeGraph'] = None
        self.session_cache: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("MasterOrchestrator initialized with Knowledge Graph support")

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
            self.workflow_metadata["last_user_request"] = user_input
            
            # Stage 1: Requirements Analysis
            self.logger.info("Stage 1: Requirements Analysis")
            requirements_output = await self._execute_requirements_stage(user_input, context)
            requirements_output.source_user_input = user_input
            requirements_output.clarification_round = 0
            self._update_reviewer_context(requirements_output, None, None)
            
            # Check if clarification is needed - PAUSE workflow and return to user
            if requirements_output.needs_clarification and requirements_output.clarifying_questions:
                self.logger.warning(f"Clarification needed: {len(requirements_output.clarifying_questions)} questions")
                
                workflow_duration = time.time() - workflow_start
                
                # Generate session ID for continuing this conversation
                import uuid
                session_id = str(uuid.uuid4())
                requirements_output.clarification_round = 1
                self._register_clarification_session(session_id, user_input, requirements_output)
                self.workflow_metadata["clarification_rounds"] = 1
                
                # Store partial state (for session management - in production, use Redis/DB)
                self.workflow_metadata["session_id"] = session_id
                self.workflow_metadata["partial_requirements"] = requirements_output.model_dump()
                
                # Return clarification response
                return OrchestratorOutput(
                    status=WorkflowStatus.NEEDS_CLARIFICATION,
                    current_stage="requirements_clarification",
                    requirements=requirements_output.model_dump(),
                    clarifying_questions=requirements_output.clarifying_questions,
                    chain_of_thought=requirements_output.chain_of_thought,
                    decisions_made=requirements_output.decisions_made,
                    current_understanding=requirements_output.current_understanding,
                    ambiguities=requirements_output.ambiguities_detected,
                    session_id=session_id,
                    awaiting_response=True,
                    citations=self.all_citations,
                    workflow_metadata=WorkflowMetadata(
                        stages_completed=["requirements_analysis_partial"],
                        total_duration_seconds=workflow_duration,
                        agents_invoked=["RequirementsAgent"],
                        start_time=datetime.fromtimestamp(workflow_start),
                        end_time=None,  # Not finished yet
                        clarification_rounds=self.workflow_metadata.get("clarification_rounds", 1),
                        requirements_diff=self.workflow_metadata.get("requirements_diff"),
                        reviewer_context=self.workflow_metadata.get("reviewer_context"),
                    ),
                    errors=[e.model_dump() for e in self.all_errors] if self.all_errors else [],
                )
            
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
                    end_time=datetime.utcnow(),
                    clarification_rounds=self.workflow_metadata.get("clarification_rounds", 0),
                    requirements_diff=self.workflow_metadata.get("requirements_diff"),
                    reviewer_context=self.workflow_metadata.get("reviewer_context"),
                    architecture_validation_warnings=self.workflow_metadata.get(
                        "architecture_validation_warnings", []
                    ),
                ),
                architecture_validation_warnings=self.workflow_metadata.get(
                    "architecture_validation_warnings", []
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
    
    async def _execute_requirements_stage_with_kg(
        self,
        user_input: str,
        session_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute Requirements Stage using Knowledge Graph Orchestrator.
        
        This NEW method replaces the legacy multi-round wizard with adaptive
        domain-based requirements gathering.
        
        Args:
            user_input: Initial user request
            session_data: Session state (contains current KG, current domain, etc.)
            
        Returns:
            Dict with status, questions (if needed), or complete KG (if ready)
        """
        stage_start = time.time()
        self.logger.info("🌐 Starting Knowledge Graph requirements gathering")
        
        try:
            # Check if this is initial request or continuing conversation
            if not session_data or not session_data.get("kg"):
                # Initial request - start orchestration
                self.logger.info("🆕 Initial request - extracting intent and initializing KG")
                
                kg = self.kg_orchestrator.orchestrate(user_input)
                self.current_kg = kg
                
                # Store KG in session
                if session_data is None:
                    session_data = {}
                session_data["kg"] = kg
                
            else:
                # Continuing conversation - load existing KG
                kg = session_data["kg"]
                self.current_kg = kg
                self.logger.info("🔄 Continuing from existing KG session")
            
            # Check if ready for architecture design
            if kg.status.ready_for_design:
                self.logger.info("✅ Knowledge Graph ready for architecture design!")
                
                # Record stage timing
                self.workflow_metadata["requirements_stage_duration"] = time.time() - stage_start
                self.workflow_metadata["requirements_confidence"] = self._calculate_kg_confidence(kg)
                
                return {
                    "status": "complete",
                    "kg": kg,
                    "ready_for_design": True,
                    "confidence": self._calculate_kg_confidence(kg),
                    "domain_confidence": {
                        "identity": kg.identity_access.confidence,
                        "runtime": kg.runtime_platform.confidence,
                        "networking": kg.networking_connectivity.confidence,
                        "data": kg.data_persistence.confidence,
                        "resiliency": kg.resiliency_dr.confidence,
                        "monitoring": kg.monitoring_observability.confidence,
                        "security": kg.security_governance.confidence,
                    }
                }
            
            # Get next questions from orchestrator
            domain, questions = self.kg_orchestrator.get_next_questions(kg)
            
            if not questions:
                # No more questions but not ready - should not happen
                self.logger.warning("⚠️ No questions but not ready_for_design - forcing completion")
                return {
                    "status": "complete",
                    "kg": kg,
                    "ready_for_design": True,  # Force completion
                    "confidence": self._calculate_kg_confidence(kg),
                }
            
            self.logger.info(f"📋 Generated {len(questions)} questions for domain: {domain}")
            
            # Transform questions to match frontend schema
            transformed_questions = []
            for q in questions:
                transformed_questions.append({
                    "question_text": q["question"],
                    "field_name": q["field"],
                    "priority": "critical" if q.get("critical", False) else "optional",
                    "context": q.get("rationale"),
                    "options": q.get("options", []),
                })
            
            # Build domain confidence dict
            domain_confidence_dict = {
                "identity": kg.identity_access.confidence,
                "runtime": kg.runtime_platform.confidence,
                "networking": kg.networking_connectivity.confidence,
                "data": kg.data_persistence.confidence,
                "resiliency": kg.resiliency_dr.confidence,
                "monitoring": kg.monitoring_observability.confidence,
                "security": kg.security_governance.confidence,
            }
            
            self.logger.info(f"📊 Domain confidence: {domain_confidence_dict}")
            
            return {
                "status": "needs_clarification",
                "domain": domain,
                "questions": transformed_questions,
                "kg": kg,
                "ready_for_design": False,
                "critical_gaps": len(kg.status.critical_gaps),
                "conflicts": len(kg.status.conflicts),
                "domain_confidence": domain_confidence_dict,
            }
            
        except Exception as e:
            self.logger.error(f"❌ Knowledge Graph requirements stage failed: {e}", exc_info=True)
            error = AgentError(
                agent_name="KnowledgeGraphOrchestrator",
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=f"KG requirements analysis failed: {str(e)}",
                details={"error": str(e)},
                retryable=True,
            )
            self.all_errors.append(error)
            raise AgentException(error)
    
    def process_kg_answers(
        self,
        domain: str,
        answers: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process user answers for a specific domain and update Knowledge Graph.
        
        Args:
            domain: Domain being answered (e.g., "identity_access")
            answers: User's answers {field_name: value}
            session_data: Current session with KG
            
        Returns:
            Updated session data with next questions or ready status
        """
        self.logger.info(f"📝 Processing answers for domain: {domain}")
        
        try:
            kg = session_data.get("kg")
            if not kg:
                raise ValueError("No Knowledge Graph found in session")
            
            # Update KG with answers
            updated_kg = self.kg_orchestrator.process_user_answers(kg, domain, answers)
            
            # Update session
            session_data["kg"] = updated_kg
            self.current_kg = updated_kg
            
            self.logger.info(f"✅ Updated KG - Confidence now: {self._calculate_kg_confidence(updated_kg):.2f}")
            
            # Check if ready
            if updated_kg.status.ready_for_design:
                return {
                    "status": "complete",
                    "kg": updated_kg,
                    "ready_for_design": True,
                    "confidence": self._calculate_kg_confidence(updated_kg),
                    "domain_confidence": {
                        "identity": updated_kg.identity_access.confidence,
                        "runtime": updated_kg.runtime_platform.confidence,
                        "networking": updated_kg.networking_connectivity.confidence,
                        "data": updated_kg.data_persistence.confidence,
                        "resiliency": updated_kg.resiliency_dr.confidence,
                        "monitoring": updated_kg.monitoring_observability.confidence,
                        "security": updated_kg.security_governance.confidence,
                    },
                }
            
            # Get next questions
            next_domain, questions = self.kg_orchestrator.get_next_questions(updated_kg)
            
            if not questions:
                # Force completion if no questions
                return {
                    "status": "complete",
                    "kg": updated_kg,
                    "ready_for_design": True,
                    "confidence": self._calculate_kg_confidence(updated_kg),
                    "domain_confidence": {
                        "identity": updated_kg.identity_access.confidence,
                        "runtime": updated_kg.runtime_platform.confidence,
                        "networking": updated_kg.networking_connectivity.confidence,
                        "data": updated_kg.data_persistence.confidence,
                        "resiliency": updated_kg.resiliency_dr.confidence,
                        "monitoring": updated_kg.monitoring_observability.confidence,
                        "security": updated_kg.security_governance.confidence,
                    },
                }
            
            # Transform questions to match frontend schema
            transformed_questions = []
            for q in questions:
                transformed_questions.append({
                    "question_text": q["question"],
                    "field_name": q["field"],
                    "priority": "critical" if q.get("critical", False) else "optional",
                    "context": q.get("rationale"),
                    "options": q.get("options", []),
                })
            
            # Build domain confidence dict
            domain_confidence_dict = {
                "identity": updated_kg.identity_access.confidence,
                "runtime": updated_kg.runtime_platform.confidence,
                "networking": updated_kg.networking_connectivity.confidence,
                "data": updated_kg.data_persistence.confidence,
                "resiliency": updated_kg.resiliency_dr.confidence,
                "monitoring": updated_kg.monitoring_observability.confidence,
                "security": updated_kg.security_governance.confidence,
            }
            
            self.logger.info(f"📊 Domain confidence: {domain_confidence_dict}")
            
            return {
                "status": "needs_clarification",
                "domain": next_domain,
                "questions": transformed_questions,
                "kg": updated_kg,
                "ready_for_design": False,
                "critical_gaps": len(updated_kg.status.critical_gaps),
                "conflicts": len(updated_kg.status.conflicts),
                "domain_confidence": domain_confidence_dict,
                "confidence": self._calculate_kg_confidence(updated_kg),
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error processing KG answers: {e}", exc_info=True)
            raise
    
    def _calculate_kg_confidence(self, kg: 'KnowledgeGraph') -> float:
        """Calculate overall confidence from Knowledge Graph."""
        confidences = [
            kg.identity_access.confidence,
            kg.runtime_platform.confidence,
            kg.networking_connectivity.confidence,
            kg.data_persistence.confidence,
            kg.resiliency_dr.confidence,
            kg.security_governance.confidence,
        ]
        
        valid = [c for c in confidences if c is not None and c > 0]
        return sum(valid) / len(valid) if valid else 0.0
    
    async def _execute_architecture_stage_from_kg(self, kg: 'KnowledgeGraph') -> ArchitectureOutput:
        """
        Execute Architecture Agent with Knowledge Graph input.
        
        This NEW method uses the KG → Architecture integration.
        
        Args:
            kg: Completed Knowledge Graph from orchestrator
            
        Returns:
            ArchitectureOutput
        """
        stage_start = time.time()
        
        try:
            self.logger.info("🏗️ Generating architecture from Knowledge Graph")
            
            # Use the new KG integration method
            result = await self.architecture_agent.process_from_knowledge_graph(kg)
            
            # Collect citations
            if result.citations:
                self.all_citations.extend(result.citations)
            
            # Record stage timing
            self.workflow_metadata["architecture_stage_duration"] = time.time() - stage_start
            self.workflow_metadata["total_services_selected"] = len(result.services)
            self._record_architecture_validation_warnings(result.validation_warnings)
            
            self.logger.info(f"✅ Architecture generated: {len(result.services)} services selected")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Architecture stage (from KG) failed: {e}", exc_info=True)
            error = AgentError(
                agent_name="ArchitectureAgent",
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=f"Architecture design from KG failed: {str(e)}",
                details={"error": str(e)},
                retryable=True,
            )
            self.all_errors.append(error)
            raise AgentException(error)

    async def _execute_architecture_stage(self, requirements: RequirementsOutput) -> ArchitectureOutput:
        """Execute Architecture Agent with retry logic."""
        stage_start = time.time()
        
        try:
            workflow_context = {
                "clarification_round": requirements.clarification_round,
                "requirements_diff": self.workflow_metadata.get("requirements_diff"),
                "reviewer_context": self.workflow_metadata.get("reviewer_context"),
                "source_user_input": requirements.source_user_input,
                "current_understanding": requirements.current_understanding,
                "decisions_made": requirements.decisions_made,
                "ambiguities": requirements.ambiguities_detected,
            }
            # Remove empty values to keep payload lean
            workflow_context = {k: v for k, v in workflow_context.items() if v}

            architecture_input = ArchitectureInput(
                requirements=requirements,
                target_cloud=requirements.target_cloud,
                region=requirements.region or None,
                workflow_context=workflow_context,
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
            self._record_architecture_validation_warnings(result.validation_warnings)
            
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

    def _record_architecture_validation_warnings(self, warnings: Optional[List[str]]) -> None:
        """Persist architecture validation warnings for downstream consumers."""
        if warnings:
            self.workflow_metadata["architecture_validation_warnings"] = warnings
            self.logger.warning(
                "Architecture validation warnings detected: %s",
                "; ".join(warnings)
            )
        else:
            self.workflow_metadata["architecture_validation_warnings"] = []

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
            "clarification_rounds": 0,
            "requirements_diff": None,
            "reviewer_context": None,
            "last_user_request": None,
            "architecture_validation_warnings": [],
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
    
    async def continue_after_clarification(
        self,
        session_id: str,
        clarification_answers: Dict[str, str],
        partial_requirements: Dict
    ) -> OrchestratorOutput:
        """
        Continue workflow after user provides clarification answers.
        
        Args:
            session_id: Session ID from previous NEEDS_CLARIFICATION response
            clarification_answers: User's answers to clarifying questions
            partial_requirements: Partial requirements from previous stage
            
        Returns:
            OrchestratorOutput with complete workflow results
        """
        workflow_start = time.time()
        self.logger.info(f"Continuing workflow after clarification (session: {session_id})")
        
        try:
            session_state = self.session_cache.get(session_id, {})
            cleaned_requirements = self._clean_requirements_dict(partial_requirements)
            previous_requirements = RequirementsOutput(**cleaned_requirements)
            original_request = (
                session_state.get("original_request")
                or previous_requirements.source_user_input
                or self.workflow_metadata.get("last_user_request")  # type: ignore[arg-type]
                or previous_requirements.current_understanding
                or ""
            )
            if not original_request:
                raise ValueError("Original user request missing; cannot replay clarification")
            
            current_round = session_state.get("clarification_round", 1)
            self._record_clarification_round(session_state, clarification_answers, current_round)
            
            refined_request = self._compose_refined_request(
                original_request,
                session_state.get("clarification_history", []),
                clarification_answers,
            )
            clarification_context = {
                "previous_requirements": previous_requirements.model_dump(),
                "clarification_history": session_state.get("clarification_history", []),
                "clarification_round": current_round,
                "latest_answers": clarification_answers,
            }
            refined_input = RequirementsInput(
                user_input=refined_request,
                context=clarification_context,
            )
            refined_output = await self._invoke_with_retry(
                agent=self.requirements_agent,
                input_data=refined_input.model_dump(),
                stage_name="Requirements Clarification"
            )
            refined_output.source_user_input = original_request
            refined_output.clarification_round = current_round
            refined_output.chain_of_thought = (
                f"{refined_output.chain_of_thought or ''}\n\n"
                f"User clarifications (round {current_round}): {json.dumps(clarification_answers, indent=2)}"
            )
            diff_summary = self._diff_requirements(previous_requirements, refined_output)
            self.workflow_metadata["clarification_rounds"] = current_round
            self.workflow_metadata["requirements_diff"] = diff_summary
            self._update_reviewer_context(
                refined_output,
                session_state.get("clarification_history"),
                diff_summary,
            )
            
            if refined_output.needs_clarification and refined_output.clarifying_questions:
                if current_round >= self.MAX_CLARIFICATION_ROUNDS:
                    self.logger.warning(
                        "Maximum clarification rounds reached; proceeding with best-effort requirements"
                    )
                    refined_output.needs_clarification = False
                    refined_output.clarifying_questions = []
                else:
                    next_round = current_round + 1
                    session_state["clarification_round"] = next_round
                    session_state["requirements_snapshot"] = refined_output.model_dump()
                    session_state["pending_questions"] = [
                        q.model_dump() for q in refined_output.clarifying_questions
                    ]
                    self.session_cache[session_id] = session_state
                    workflow_duration = time.time() - workflow_start
                    self.logger.info(
                        "Additional clarification required (round %s)", next_round
                    )
                    return OrchestratorOutput(
                        status=WorkflowStatus.NEEDS_CLARIFICATION,
                        current_stage="requirements_clarification",
                        requirements=refined_output.model_dump(),
                        clarifying_questions=refined_output.clarifying_questions,
                        chain_of_thought=refined_output.chain_of_thought,
                        decisions_made=refined_output.decisions_made,
                        current_understanding=refined_output.current_understanding,
                        ambiguities=refined_output.ambiguities_detected,
                        session_id=session_id,
                        awaiting_response=True,
                        citations=self.all_citations,
                        workflow_metadata=WorkflowMetadata(
                            stages_completed=["requirements", "clarification_pending"],
                            total_duration_seconds=workflow_duration,
                            agents_invoked=["RequirementsAgent"],
                            start_time=datetime.fromtimestamp(workflow_start),
                            end_time=None,
                            clarification_rounds=next_round,
                            requirements_diff=diff_summary,
                            reviewer_context=self.workflow_metadata.get("reviewer_context"),
                        ),
                        errors=[e.model_dump() for e in self.all_errors] if self.all_errors else [],
                    )
            
            # Clarification satisfied - remove session cache entry
            self.session_cache.pop(session_id, None)
            
            # Continue with Architecture stage
            self.logger.info("Stage 2: Architecture Design (after clarification)")
            architecture_output = await self._execute_architecture_stage(refined_output)
            
            # Stage 3: Cost Estimation
            self.logger.info("Stage 3: Cost Estimation")
            cost_output = await self._execute_cost_stage(refined_output, architecture_output)
            
            # Stage 4: Documentation Generation
            self.logger.info("Stage 4: Documentation Generation")
            documentation_output = await self._execute_documentation_stage(
                refined_output,
                architecture_output,
                cost_output
            )
            
            # Finalize workflow
            workflow_duration = time.time() - workflow_start
            self._finalize_workflow_metadata(workflow_duration, WorkflowStatus.SUCCESS)
            
            # Deduplicate citations
            unique_citations = self._deduplicate_citations(self.all_citations)
            
            self.logger.info(
                f"Workflow completed successfully in {workflow_duration:.2f}s (after clarification)"
            )
            
            return OrchestratorOutput(
                status=WorkflowStatus.SUCCESS,
                current_stage="completed",
                requirements=refined_output.model_dump(),
                architecture=architecture_output.model_dump(),
                costs=cost_output.model_dump(),
                documentation=documentation_output.model_dump(),
                citations=unique_citations,
                workflow_metadata=WorkflowMetadata(
                    stages_completed=["requirements", "clarification", "architecture", "cost", "documentation"],
                    total_duration_seconds=workflow_duration,
                    agents_invoked=["RequirementsAgent", "ArchitectureAgent", "CostAgent", "DocumentationAgent"],
                    start_time=datetime.fromtimestamp(workflow_start),
                    end_time=datetime.utcnow(),
                    clarification_rounds=current_round,
                    requirements_diff=diff_summary,
                    reviewer_context=self.workflow_metadata.get("reviewer_context"),
                    architecture_validation_warnings=self.workflow_metadata.get(
                        "architecture_validation_warnings", []
                    ),
                ),
                architecture_validation_warnings=self.workflow_metadata.get(
                    "architecture_validation_warnings", []
                ),
                errors=[e.model_dump() for e in self.all_errors] if self.all_errors else [],
            )
            
        except Exception as e:
            workflow_duration = time.time() - workflow_start
            self._finalize_workflow_metadata(workflow_duration, WorkflowStatus.ERROR)
            
            self.logger.error(f"Workflow continuation failed: {e}")
            
            error = AgentError(
                agent_name="MasterOrchestrator",
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message="Workflow continuation failed after clarification",
                details={"error": str(e), "session_id": session_id},
                retryable=False,
            )
            self.all_errors.append(error)
            
            raise AgentException(error)

    def _clean_requirements_dict(self, requirements_dict: dict) -> dict:
        """
        Clean up requirements dictionary by converting None values to appropriate defaults.
        
        This is needed when reconstructing RequirementsOutput from serialized data,
        as Pydantic expects lists not None for list fields.
        
        Args:
            requirements_dict: Raw requirements dictionary
            
        Returns:
            Cleaned dictionary with proper defaults
        """
        cleaned = requirements_dict.copy()
        
        # Fix nested technical_constraints fields
        if "technical_constraints" in cleaned and cleaned["technical_constraints"]:
            tc = cleaned["technical_constraints"]
            if tc.get("team_skills") is None:
                tc["team_skills"] = []
            if tc.get("existing_infrastructure") is None:
                tc["existing_infrastructure"] = []
            if tc.get("preferred_technologies") is None:
                tc["preferred_technologies"] = []
        
        # Fix top-level list fields
        if cleaned.get("functional_requirements") is None:
            cleaned["functional_requirements"] = []
        if cleaned.get("implied_requirements") is None:
            cleaned["implied_requirements"] = []
        if cleaned.get("ambiguities_detected") is None:
            cleaned["ambiguities_detected"] = []
        if cleaned.get("clarifying_questions") is None:
            cleaned["clarifying_questions"] = []
        if cleaned.get("decisions_made") is None:
            cleaned["decisions_made"] = []
        if cleaned.get("all_grounding_sources") is None:
            cleaned["all_grounding_sources"] = []
        
        # Fix non_functional_requirements nested fields
        if "non_functional_requirements" in cleaned and cleaned["non_functional_requirements"]:
            nfr = cleaned["non_functional_requirements"]
            if nfr.get("compliance") is None:
                nfr["compliance"] = []
        
        return cleaned

    def _register_clarification_session(
        self, session_id: str, user_input: str, requirements: RequirementsOutput
    ) -> None:
        """Persist clarification session metadata for multi-round handling."""
        self.session_cache[session_id] = {
            "original_request": user_input,
            "clarification_round": requirements.clarification_round or 1,
            "requirements_snapshot": requirements.model_dump(),
            "clarification_history": [],
            "pending_questions": [q.model_dump() for q in requirements.clarifying_questions],
        }

    def _record_clarification_round(
        self,
        session_state: Dict[str, Any],
        clarification_answers: Dict[str, str],
        round_number: int,
    ) -> None:
        """Store answered questions for auditing and future prompts."""
        if not clarification_answers:
            return
        questions = session_state.pop("pending_questions", [])
        history = session_state.setdefault("clarification_history", [])
        history.append(
            {
                "round": round_number,
                "questions": questions,
                "answers": clarification_answers,
                "recorded_at": datetime.utcnow().isoformat(),
            }
        )

    def _compose_refined_request(
        self,
        original_request: str,
        clarification_history: Optional[List[Dict[str, Any]]],
        latest_answers: Dict[str, str],
    ) -> str:
        """Combine original prompt with clarification history for re-processing."""
        lines: List[str] = [original_request.strip(), "", "Clarifications provided so far:"]
        if clarification_history:
            for entry in clarification_history:
                lines.append(f"Round {entry.get('round')}:")
                questions = entry.get("questions", [])
                answers = entry.get("answers", {})
                for question in questions:
                    if isinstance(question, dict):
                        question_text = question.get("question", "")
                    else:
                        question_text = str(question)
                    answer_text = answers.get(question_text, "pending")
                    if question_text:
                        lines.append(f"- {question_text}: {answer_text}")
        if latest_answers:
            lines.append("Latest answers:")
            for question, answer in latest_answers.items():
                lines.append(f"- {question}: {answer}")
        return "\n".join([line for line in lines if line])

    def _diff_requirements(
        self,
        previous: RequirementsOutput,
        current: RequirementsOutput,
    ) -> Dict[str, Any]:
        """Create a lightweight diff between two requirements snapshots."""
        diff: Dict[str, Any] = {}

        def diff_list(field_name: str, before: List[str], after: List[str]) -> None:
            added = sorted(set(after) - set(before))
            removed = sorted(set(before) - set(after))
            if added or removed:
                diff[field_name] = {"added": added, "removed": removed}

        diff_list(
            "functional_requirements",
            previous.functional_requirements,
            current.functional_requirements,
        )
        diff_list(
            "implied_requirements",
            previous.implied_requirements,
            current.implied_requirements,
        )

        nfr_prev = previous.non_functional_requirements.model_dump()
        nfr_curr = current.non_functional_requirements.model_dump()
        nfr_changes: Dict[str, Any] = {}
        for key in sorted(set(nfr_prev.keys()) | set(nfr_curr.keys())):
            if nfr_prev.get(key) != nfr_curr.get(key):
                nfr_changes[key] = {"before": nfr_prev.get(key), "after": nfr_curr.get(key)}
        if nfr_changes:
            diff["non_functional_requirements"] = nfr_changes

        tc_prev = previous.technical_constraints.model_dump()
        tc_curr = current.technical_constraints.model_dump()
        tc_changes: Dict[str, Any] = {}
        for key in sorted(set(tc_prev.keys()) | set(tc_curr.keys())):
            if tc_prev.get(key) != tc_curr.get(key):
                tc_changes[key] = {"before": tc_prev.get(key), "after": tc_curr.get(key)}
        if tc_changes:
            diff["technical_constraints"] = tc_changes

        if previous.target_cloud != current.target_cloud:
            diff["target_cloud"] = {
                "before": previous.target_cloud,
                "after": current.target_cloud,
            }
        if previous.region != current.region:
            diff["region"] = {"before": previous.region, "after": current.region}
        if previous.industry_vertical != current.industry_vertical:
            diff["industry_vertical"] = {
                "before": previous.industry_vertical,
                "after": current.industry_vertical,
            }

        return diff

    def _update_reviewer_context(
        self,
        requirements: Optional[RequirementsOutput],
        clarification_history: Optional[List[Dict[str, Any]]],
        diff_summary: Optional[Dict[str, Any]],
    ) -> None:
        """Persist context blob for future reviewer agent consumption."""
        if not requirements:
            return
        try:
            self.workflow_metadata["reviewer_context"] = {
                "requirements": requirements.model_dump(),
                "clarification_history": clarification_history or [],
                "requirements_diff": diff_summary or {},
            }
        except Exception as err:  # pragma: no cover - defensive logging
            self.logger.warning("Failed to update reviewer context: %s", err)

    # ========================================================================
    # NEW: MULTI-STAGE WIZARD FLOW METHODS
    # ========================================================================

    async def orchestrate_stage_based(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> OrchestratorOutput:
        """
        NEW: Multi-stage wizard orchestration (5 stages with approval at each step).
        
        This replaces the single-round clarification with a truly interactive flow:
        - Stage 1: Requirements Discovery (basic questions)
        - Stage 2: Compute & Scalability (recommendations with trade-offs)
        - Stage 3: Data Architecture (DB, storage decisions)
        - Stage 4: Security & Compliance (security decisions)
        - Stage 5: Final Review (cost summary, all decisions)
        
        After Stage 5 approval → Full Architecture + Cost + Documentation
        
        Args:
            user_input: Initial user requirements
            context: Optional conversation context
            
        Returns:
            OrchestratorOutput with stage output and AWAITING_STAGE_APPROVAL status
        """
        workflow_start = time.time()
        self.logger.info("Starting STAGE-BASED workflow orchestration")
        
        try:
            self._initialize_workflow_metadata()
            
            # Start with Stage 1: Requirements Discovery
            import uuid
            session_id = str(uuid.uuid4())
            
            # Build session data for Stage 1
            session_data = {
                "initial_request": user_input,
                "context": context or {}
            }
            stage_output = await self._execute_stage_1_requirements(session_data)
            
            return OrchestratorOutput(
                status=WorkflowStatus.AWAITING_STAGE_APPROVAL,
                conversation_stage=ConversationStage.STAGE_1_REQUIREMENTS,
                stage_output=stage_output,
                stages_completed=[],
                all_stage_decisions={},
                session_id=session_id,
                awaiting_response=True,
                can_go_back=False,  # Can't go back from Stage 1
                citations=self.all_citations,
                workflow_metadata=WorkflowMetadata(
                    stages_completed=["stage_1_started"],
                    total_duration_seconds=time.time() - workflow_start,
                    agents_invoked=["RequirementsAgent"],
                    start_time=datetime.fromtimestamp(workflow_start),
                    end_time=None
                )
            )
            
        except Exception as e:
            self.logger.error(f"Stage-based workflow failed: {e}")
            raise

    async def continue_stage_based(
        self,
        session_id: str,
        stage_approval: StageApprovalResponse,
        session_data: Dict[str, Any]
    ) -> OrchestratorOutput:
        """
        Continue stage-based workflow after user approval/modification.
        
        Args:
            session_id: Session ID
            stage_approval: User's response (approve/modify/back/see_alternatives)
            session_data: Stored session data with previous decisions
            
        Returns:
            OrchestratorOutput with next stage or final results
        """
        self.logger.info(f"Continuing stage {stage_approval.stage} with action: {stage_approval.action}")
        
        current_stage = stage_approval.stage
        stages_completed = session_data.get("stages_completed", [])
        all_decisions = session_data.get("all_stage_decisions", {})
        
        # Handle different user actions
        if stage_approval.action == "back":
            return await self._go_back_to_previous_stage(session_id, current_stage, session_data)
        
        elif stage_approval.action == "see_alternatives":
            return await self._show_alternatives(session_id, current_stage, session_data)
        
        elif stage_approval.action == "modify":
            return await self._modify_stage_recommendations(
                session_id, current_stage, stage_approval.modification_request, session_data
            )
        
        elif stage_approval.action == "approve":
            # SPECIAL HANDLING: Stage 1 multi-round questioning
            if current_stage == ConversationStage.STAGE_1_REQUIREMENTS:
                self.logger.info("🔄 Stage 1 approved - checking if more rounds needed...")
                
                # Store answers from this round
                current_round = session_data.get("question_round", 1)
                if stage_approval.answers:
                    if "previous_answers" not in session_data:
                        session_data["previous_answers"] = {}
                    session_data["previous_answers"].update(stage_approval.answers)
                
                # Increment round and call Stage 1 again
                session_data["question_round"] = current_round + 1
                
                stage_output = await self._execute_stage_1_requirements(session_data)
                
                # Check if Stage 1 is complete (empty questions = done)
                if not stage_output.questions or len(stage_output.questions) == 0:
                    self.logger.info("✅ Stage 1 complete - moving to Stage 2")
                    # Stage 1 is complete - mark it as done and move to Stage 2
                    stages_completed.append(current_stage.value if hasattr(current_stage, 'value') else current_stage)
                    next_stage = self._get_next_stage(current_stage)
                    stage_output = await self._execute_stage(next_stage, session_data)
                    
                    return OrchestratorOutput(
                        status=WorkflowStatus.AWAITING_STAGE_APPROVAL,
                        conversation_stage=next_stage,
                        stage_output=stage_output,
                        stages_completed=stages_completed,
                        all_stage_decisions=all_decisions,
                        session_id=session_id,
                        awaiting_response=True,
                        can_go_back=len(stages_completed) > 0,
                        citations=self.all_citations,
                        workflow_metadata=WorkflowMetadata(
                            stages_completed=[s.value if hasattr(s, 'value') else s for s in stages_completed],
                            total_duration_seconds=0,
                            agents_invoked=[],
                            start_time=datetime.utcnow(),
                            end_time=None
                        )
                    )
                else:
                    # Still in Stage 1 - return next round of questions
                    self.logger.info(f"🔄 Stage 1 continuing - Round {current_round + 1}")
                    return OrchestratorOutput(
                        status=WorkflowStatus.AWAITING_STAGE_APPROVAL,
                        conversation_stage=ConversationStage.STAGE_1_REQUIREMENTS,
                        stage_output=stage_output,
                        stages_completed=stages_completed,
                        all_stage_decisions=all_decisions,
                        session_id=session_id,
                        awaiting_response=True,
                        can_go_back=False,  # Can't go back during Stage 1 rounds
                        citations=self.all_citations,
                        workflow_metadata=WorkflowMetadata(
                            stages_completed=["stage_1_in_progress"],
                            total_duration_seconds=0,
                            agents_invoked=["RequirementsAgent"],
                            start_time=datetime.utcnow(),
                            end_time=None
                        )
                    )
            
            # OTHER STAGES: User approved this stage - move to next
            # Store as string for consistency
            stages_completed.append(current_stage.value if hasattr(current_stage, 'value') else current_stage)
            
            # Determine next stage
            next_stage = self._get_next_stage(current_stage)
            
            if next_stage == ConversationStage.COMPLETE:
                # All stages approved - generate full architecture
                return await self._finalize_and_generate_architecture(session_id, session_data)
            else:
                # Execute next stage
                stage_output = await self._execute_stage(next_stage, session_data)
                
                return OrchestratorOutput(
                    status=WorkflowStatus.AWAITING_STAGE_APPROVAL,
                    conversation_stage=next_stage,
                    stage_output=stage_output,
                    stages_completed=stages_completed,
                    all_stage_decisions=all_decisions,
                    session_id=session_id,
                    awaiting_response=True,
                    can_go_back=len(stages_completed) > 0,
                    citations=self.all_citations,
                    workflow_metadata=WorkflowMetadata(
                        stages_completed=[s.value if hasattr(s, 'value') else s for s in stages_completed],
                        total_duration_seconds=0,  # Will calculate at end
                        agents_invoked=[],
                        start_time=datetime.utcnow(),
                        end_time=None
                    )
                )
    
    def _get_next_stage(self, current_stage: ConversationStage) -> ConversationStage:
        """Determine next stage in the wizard."""
        stage_order = [
            ConversationStage.STAGE_1_REQUIREMENTS,
            ConversationStage.STAGE_2_COMPUTE,
            ConversationStage.STAGE_3_DATA,
            ConversationStage.STAGE_4_SECURITY,
            ConversationStage.STAGE_5_REVIEW,
            ConversationStage.COMPLETE
        ]
        
        try:
            current_index = stage_order.index(current_stage)
            return stage_order[current_index + 1]
        except (ValueError, IndexError):
            return ConversationStage.COMPLETE

    async def _execute_stage_1_requirements(
        self,
        session_data: Optional[Dict[str, Any]] = None
    ) -> StageOutput:
        """
        Stage 1: Progressive Multi-Turn Requirements Discovery.
        
        Progressive Flow:
        - Round 1: AI generates 4-8 initial questions (count based on complexity)
        - User answers → AI analyzes answers
        - Round 2: AI generates 2-4 follow-up questions (if needed)
        - Continue up to 3 rounds or until AI satisfied
        
        All questions are AI-generated dynamically (no hardcoded lists).
        """
        # Extract session data
        user_input = session_data.get("initial_request", "") if session_data else ""
        round_number = session_data.get("question_round", 1) if session_data else 1
        previous_answers = session_data.get("previous_answers", {}) if session_data else {}
        questions_asked = session_data.get("questions_asked", []) if session_data else []
        
        self.logger.info(f"🔄 Stage 1 - Round {round_number} for: {user_input[:100]}...")
        
        try:
            # Round 1: Initial questions
            if round_number == 1:
                self.logger.info("🧠 Round 1: Generating initial contextual questions...")
                
                # Calculate complexity to determine question count
                complexity_score = self._calculate_complexity_score(user_input)
                target_count = self._determine_question_count(complexity_score, round_number=1)
                
                self.logger.info(f"📊 Targeting {target_count} questions based on complexity={complexity_score:.1f}")
                
                # Generate contextual questions using AI
                questions = await self._generate_contextual_questions(user_input)
                
                # Apply dynamic count (not hard cap)
                questions = questions[:target_count]
                
                self.logger.info(f"✅ Generated {len(questions)} Round 1 questions")
                
                return StageOutput(
                    stage=ConversationStage.STAGE_1_REQUIREMENTS,
                    stage_title="Requirements Discovery - Round 1",
                    stage_description="Let me understand your requirements to design the best solution:",
                    recommendations=[],
                    questions=questions,
                    chain_of_thought=f"Complexity: {complexity_score:.1f}. Analyzing: '{user_input}'. Generated {len(questions)} targeted questions covering Azure CAF domains.",
                    decisions_made=[],
                    estimated_cost="$0/month so far",
                    can_proceed=True,
                    requires_approval=True
                )
            
            # Round 2+: Analyze answers and decide next steps
            else:
                self.logger.info(f"🧠 Round {round_number}: Analyzing previous answers...")
                
                # Phase 4: Analyze answers to decide if more questions needed
                analysis = await self._analyze_stage1_answers(
                    initial_request=user_input,
                    round_number=round_number - 1,  # Just completed round
                    previous_questions=questions_asked,
                    answers=previous_answers
                )
                
                # Check if we should continue or complete Stage 1
                if not analysis.get("continue_questioning", False) or round_number > 3:
                    # Complete Stage 1 - move to Stage 2
                    self.logger.info(f"✅ Stage 1 COMPLETE after {round_number - 1} rounds")
                    self.logger.info(f"📝 Reason: {analysis.get('reason', 'Max rounds reached')}")
                    
                    # Store final answers in requirements dict
                    requirements = {
                        "initial_request": user_input,
                        "total_rounds": round_number - 1,
                        "confidence_score": analysis.get("confidence_score", 0.8),
                        "answers": previous_answers,
                        "known_requirements": analysis.get("known_requirements", []),
                        "completion_reason": analysis.get("reason", "")
                    }
                    
                    # Store in session for Stage 2
                    if session_data:
                        session_data["requirements"] = requirements
                        session_data["stage1_complete"] = True
                    
                    # Return empty questions to signal completion
                    return StageOutput(
                        stage=ConversationStage.STAGE_1_REQUIREMENTS,
                        stage_title="Requirements Discovery - Complete",
                        stage_description=f"✅ Requirements gathered after {round_number - 1} rounds. Proceeding to architecture design...",
                        recommendations=[],
                        questions=[],  # Empty = complete
                        chain_of_thought=analysis.get("reason", "Sufficient information collected"),
                        decisions_made=[f"Completed {round_number - 1} rounds of discovery"],
                        estimated_cost="$0/month so far",
                        can_proceed=True,
                        requires_approval=False  # Auto-proceed to Stage 2
                    )
                
                # Phase 5: Generate follow-up questions
                self.logger.info(f"🔍 Generating Round {round_number} follow-up questions...")
                
                complexity_score = self._calculate_complexity_score(user_input)
                
                questions = await self._generate_followup_questions(
                    initial_request=user_input,
                    round_number=round_number,
                    previous_answers=previous_answers,
                    missing_info=analysis.get("missing_info", []),
                    complexity_score=complexity_score
                )
                
                self.logger.info(f"✅ Generated {len(questions)} Round {round_number} follow-up questions")
                
                return StageOutput(
                    stage=ConversationStage.STAGE_1_REQUIREMENTS,
                    stage_title=f"Requirements Discovery - Round {round_number}",
                    stage_description=self._get_round_description(round_number),
                    recommendations=[],
                    questions=questions,
                    chain_of_thought=f"Round {round_number - 1} analysis: {analysis.get('reason', '')}. Missing: {', '.join(analysis.get('missing_info', []))}. Asking {len(questions)} follow-ups.",
                    decisions_made=[f"Completed Round {round_number - 1}", f"Identified {len(analysis.get('missing_info', []))} gaps"],
                    estimated_cost="$0/month so far",
                    can_proceed=True,
                    requires_approval=True
                )
            
        except Exception as e:
            self.logger.error(f"❌ Error generating contextual questions: {e}", exc_info=True)
            self.logger.warning("Falling back to generic questions")
            
            # Fallback to generic questions
            from src.models.schemas import ClarificationQuestion
            
            return StageOutput(
                stage=ConversationStage.STAGE_1_REQUIREMENTS,
                stage_title="Requirements Discovery",
                stage_description="Let's understand your basic requirements before making any technical decisions.",
                recommendations=[],
                questions=[
                    ClarificationQuestion(
                        question="How many concurrent users do you expect?",
                        rationale="This determines compute sizing, scalability approach, and cost estimates.",
                        options=["< 1,000", "1,000 - 10,000", "10,000 - 100,000", "> 100,000"]
                    ),
                    ClarificationQuestion(
                        question="What is your monthly budget?",
                        rationale="Budget constraints will guide our architecture choices and trade-offs.",
                        options=["< $1,000", "$1,000 - $5,000", "$5,000 - $20,000", "> $20,000"]
                    ),
                    ClarificationQuestion(
                        question="What is your target launch timeline?",
                        rationale="Timeline affects architectural complexity and MVP vs full-featured approach.",
                        options=["< 3 months", "3-6 months", "6-12 months", "> 12 months"]
                    ),
                    ClarificationQuestion(
                        question="What is your required availability SLA?",
                        rationale="Availability requirements drive redundancy, multi-region, and cost decisions.",
                        options=["99.9% (< 1 hour downtime/month)", "99.95% (< 22 min/month)", "99.99% (< 4 min/month)", "99.999% (< 26 sec/month)"]
                    )
                ],
                chain_of_thought=f"User requested: '{user_input}'. Before making any technical decisions, I need to understand the scale, budget, timeline, and availability requirements.",
                decisions_made=[],
                estimated_cost="$0/month so far",
                can_proceed=True,
                requires_approval=True
            )

    async def _execute_stage(
        self,
        stage: ConversationStage,
        session_data: Dict[str, Any]
    ) -> StageOutput:
        """Execute a specific stage and return recommendations."""
        if stage == ConversationStage.STAGE_1_REQUIREMENTS:
            # Stage 1 returns questions, not recommendations
            return await self._execute_stage_1_requirements(session_data)
        elif stage == ConversationStage.STAGE_2_COMPUTE:
            return await self._execute_stage_2_compute(session_data)
        elif stage == ConversationStage.STAGE_3_DATA:
            return await self._execute_stage_3_data(session_data)
        elif stage == ConversationStage.STAGE_4_SECURITY:
            return await self._execute_stage_4_security(session_data)
        elif stage == ConversationStage.STAGE_5_REVIEW:
            return await self._execute_stage_5_review(session_data)
        else:
            raise ValueError(f"Unknown stage: {stage}")
    
    def _get_round_description(self, round_number: int) -> str:
        """Get friendly description for each round of questioning."""
        descriptions = {
            1: "Let me understand your requirements to design the best solution:",
            2: "Based on your answers, I have a few follow-up questions to refine the design:",
            3: "Just a couple more details to ensure we cover all critical aspects:"
        }
        return descriptions.get(round_number, "Additional questions to finalize requirements:")

    async def _execute_stage_2_compute(self, session_data: Dict[str, Any]) -> StageOutput:
        """Stage 2: Compute & Scalability - AI-powered recommendations."""
        self.logger.info("🤖 Generating AI-powered compute recommendations")
        
        # Extract requirements from session data
        requirements = session_data.get("requirements", {})
        previous_decisions = session_data.get("all_stage_decisions", {})
        
        # CRITICAL: Include initial_request in requirements so AI knows the user's original requirement
        if "initial_request" in session_data and "initial_request" not in requirements:
            requirements["initial_request"] = session_data["initial_request"]
        
        try:
            # Generate AI-powered recommendations
            stage_output = await self._generate_ai_recommendations(
                stage=ConversationStage.STAGE_2_COMPUTE,
                requirements=requirements,
                previous_decisions=previous_decisions
            )
            
            self.logger.info(f"✅ AI generated {len(stage_output.recommendations)} compute recommendations")
            return stage_output
            
        except Exception as e:
            self.logger.error(f"❌ Error in AI generation, falling back to hardcoded: {e}")
            # Fallback to simple hardcoded recommendations
            return StageOutput(
                stage=ConversationStage.STAGE_2_COMPUTE,
                stage_title="Compute & Scalability",
                stage_description="Based on your requirements, here are compute options.",
                recommendations=[
                    StageRecommendation(
                        decision_name="Primary Compute Platform",
                        recommendation="Azure App Service",
                        reasoning="Choose how to run your application",
                        trade_offs=[
                            TradeOff(
                                option_name="Azure App Service",
                                pros=["Managed platform", "Auto-scaling", "Quick setup"],
                                cons=["Less control", "Platform lock-in"],
                                cost_impact="$200/month",
                                performance_impact="Good performance for most workloads",
                                recommended=True
                            ),
                            TradeOff(
                                option_name="Azure Kubernetes Service (AKS)",
                                pros=["Maximum flexibility", "Container-native"],
                                cons=["Complex setup", "Requires expertise"],
                                cost_impact="$800/month",
                                performance_impact="Excellent performance, highly scalable",
                                recommended=False
                            )
                        ],
                        alternatives=[],
                        cost_impact="$200/month",
                        dependencies=[],
                        follow_up_questions=[]
                    )
                ],
                questions=[],
                chain_of_thought="Fallback recommendations due to AI error.",
                decisions_made=[],
                estimated_cost="$200/month so far",
                can_proceed=True,
                requires_approval=True
            )

    async def _execute_stage_3_data(self, session_data: Dict[str, Any]) -> StageOutput:
        """Stage 3: Data Architecture - AI-powered recommendations."""
        self.logger.info("🤖 Generating AI-powered data architecture recommendations")
        
        # Extract requirements and previous decisions
        requirements = session_data.get("requirements", {})
        previous_decisions = session_data.get("all_stage_decisions", {})
        
        try:
            # Generate AI-powered recommendations
            stage_output = await self._generate_ai_recommendations(
                stage=ConversationStage.STAGE_3_DATA,
                requirements=requirements,
                previous_decisions=previous_decisions
            )
            
            self.logger.info(f"✅ AI generated {len(stage_output.recommendations)} data recommendations")
            return stage_output
            
        except Exception as e:
            self.logger.error(f"❌ Error in AI generation, falling back to hardcoded: {e}")
            # Fallback to simple hardcoded recommendations
        return StageOutput(
            stage=ConversationStage.STAGE_3_DATA,
            stage_title="Data Architecture",
            stage_description="Based on your application needs, here are my recommendations for data storage.",
            recommendations=[
                StageRecommendation(
                    decision_name="Primary Database",
                    recommendation="Azure SQL Database (Business Critical tier)",
                    reasoning="For an e-commerce platform, you need ACID transactions for orders, inventory, and payments. Azure SQL Database provides strong consistency, automatic backups, and high availability with 99.99% SLA.",
                    trade_offs=[
                        TradeOff(
                            option_name="Azure SQL Database (Business Critical)",
                            pros=[
                                "ACID transactions guarantee data consistency",
                                "Familiar SQL syntax and tooling",
                                "Built-in high availability (99.99% SLA)",
                                "Automatic backups and point-in-time restore",
                                "Easy integration with .NET/Java apps"
                            ],
                            cons=[
                                "More expensive than NoSQL alternatives",
                                "Vertical scaling limits (max 128 vCores)",
                                "Azure-specific (vendor lock-in)"
                            ],
                            cost_impact="$500/month (8 vCores, 200GB storage)",
                            performance_impact="Handles 10K transactions/sec",
                            recommended=True
                        ),
                        TradeOff(
                            option_name="Azure Cosmos DB (NoSQL)",
                            pros=[
                                "Unlimited horizontal scalability",
                                "Global distribution with multi-region writes",
                                "Multiple API support (SQL, MongoDB, Cassandra)",
                                "Single-digit millisecond latency"
                            ],
                            cons=[
                                "Eventually consistent (not ideal for financial transactions)",
                                "Steeper learning curve for SQL developers",
                                "Higher cost for small workloads",
                                "Complex pricing model (RU/s based)"
                            ],
                            cost_impact="$800/month (20K RU/s provisioned)",
                            performance_impact="Handles 50K+ reads/sec globally",
                            recommended=False
                        ),
                        TradeOff(
                            option_name="PostgreSQL on Azure VMs",
                            pros=[
                                "Full control over database configuration",
                                "Open-source with no licensing costs",
                                "Rich extension ecosystem (PostGIS, pgvector)",
                                "Lower cost for reserved instances"
                            ],
                            cons=[
                                "You manage OS patches, backups, HA setup",
                                "Higher operational overhead",
                                "No automatic scaling",
                                "Requires DBA expertise"
                            ],
                            cost_impact="$300/month (D4s_v3 VM + managed disks)",
                            performance_impact="Depends on your tuning",
                            recommended=False
                        )
                    ],
                    alternatives=[
                        "Azure Database for PostgreSQL - Flexible Server ($400/month)",
                        "SQL Server on Azure VM ($600/month with licensing)"
                    ],
                    cost_impact="$500/month",
                    dependencies=["Compute tier from Stage 2", "Expected transaction volume"],
                    follow_up_questions=[]
                ),
                StageRecommendation(
                    decision_name="Caching Layer",
                    recommendation="Azure Cache for Redis (Standard C1)",
                    reasoning="To reduce database load and improve response times, a caching layer is essential. Redis is industry-standard and integrates well with most application frameworks.",
                    trade_offs=[
                        TradeOff(
                            option_name="Azure Cache for Redis (Standard C1)",
                            pros=[
                                "Dramatically reduces database queries (80%+ hit rate)",
                                "Sub-millisecond response times",
                                "Supports sessions, caching, pub/sub",
                                "99.9% SLA with zone redundancy"
                            ],
                            cons=[
                                "Additional complexity in cache invalidation",
                                "Memory-based (limited by tier)",
                                "Cost scales with data size"
                            ],
                            cost_impact="$75/month (1GB cache)",
                            performance_impact="Reduces page load time by 60%",
                            recommended=True
                        ),
                        TradeOff(
                            option_name="In-Memory Caching (App-level)",
                            pros=[
                                "No additional infrastructure cost",
                                "Lowest latency (in-process)",
                                "Simple to implement"
                            ],
                            cons=[
                                "Not shared across app instances",
                                "Lost on app restart",
                                "Limited memory per instance",
                                "Cache invalidation challenges in multi-instance setup"
                            ],
                            cost_impact="$0/month (included in app)",
                            performance_impact="Good for read-heavy single instance",
                            recommended=False
                        )
                    ],
                    alternatives=["Memcached on VMs ($50/month)", "No caching (rely on CDN only)"],
                    cost_impact="$75/month",
                    dependencies=["Application architecture", "Read/write ratio"],
                    follow_up_questions=[]
                )
            ],
            chain_of_thought="E-commerce requires reliable transactional data storage. Azure SQL Database is the safest choice for financial data. Adding Redis caching will significantly improve performance and reduce database costs by handling 80% of read requests from cache.",
            decisions_made=[
                "Using relational database for ACID guarantees",
                "Adding caching layer to reduce database load",
                "Prioritizing data consistency over eventual consistency"
            ],
            estimated_cost="$775/month so far (Compute: $200 + Database: $500 + Cache: $75)",
            can_proceed=True,
            requires_approval=True
        )

    async def _execute_stage_4_security(self, session_data: Dict[str, Any]) -> StageOutput:
        """Stage 4: Security & Compliance - AI-powered recommendations."""
        self.logger.info("🤖 Generating AI-powered security recommendations")
        
        # Extract requirements and previous decisions
        requirements = session_data.get("requirements", {})
        previous_decisions = session_data.get("all_stage_decisions", {})
        
        try:
            # Generate AI-powered recommendations
            stage_output = await self._generate_ai_recommendations(
                stage=ConversationStage.STAGE_4_SECURITY,
                requirements=requirements,
                previous_decisions=previous_decisions
            )
            
            self.logger.info(f"✅ AI generated {len(stage_output.recommendations)} security recommendations")
            return stage_output
            
        except Exception as e:
            self.logger.error(f"❌ Error in AI generation, falling back to hardcoded: {e}")
            # Fallback to simple hardcoded recommendations
        return StageOutput(
            stage=ConversationStage.STAGE_4_SECURITY,
            stage_title="Security & Compliance",
            stage_description="Let's secure your architecture with industry best practices and compliance controls.",
            recommendations=[
                StageRecommendation(
                    decision_name="Secrets Management",
                    recommendation="Azure Key Vault (Standard tier)",
                    reasoning="Never store secrets in code or config files. Key Vault provides centralized, encrypted storage for API keys, connection strings, and certificates with audit logging.",
                    trade_offs=[
                        TradeOff(
                            option_name="Azure Key Vault (Standard)",
                            pros=[
                                "Centralized secrets management",
                                "Hardware-backed encryption (HSM available)",
                                "Automatic certificate rotation",
                                "Full audit trail of secret access",
                                "Integration with Azure AD and Managed Identity"
                            ],
                            cons=[
                                "Additional complexity for developers",
                                "Network latency for secret retrieval",
                                "Cost per operation (negligible for most apps)"
                            ],
                            cost_impact="$15/month (1000 operations/day)",
                            performance_impact="Adds ~50ms latency per secret retrieval",
                            recommended=True
                        ),
                        TradeOff(
                            option_name="Environment Variables Only",
                            pros=[
                                "Simple to implement",
                                "No additional cost",
                                "Fast access (in-memory)"
                            ],
                            cons=[
                                "Secrets visible in process memory",
                                "No rotation capability",
                                "No audit trail",
                                "Secrets stored in multiple places",
                                "Fails compliance audits"
                            ],
                            cost_impact="$0/month",
                            performance_impact="Fastest (in-memory)",
                            recommended=False
                        )
                    ],
                    alternatives=["HashiCorp Vault (self-managed, $200/month)"],
                    cost_impact="$15/month",
                    dependencies=["Azure AD authentication"],
                    follow_up_questions=[]
                ),
                StageRecommendation(
                    decision_name="Web Application Firewall",
                    recommendation="Azure Application Gateway with WAF v2",
                    reasoning="Protect against OWASP Top 10 vulnerabilities (SQL injection, XSS, etc.). WAF is essential for e-commerce to protect payment and customer data.",
                    trade_offs=[
                        TradeOff(
                            option_name="Application Gateway with WAF v2",
                            pros=[
                                "OWASP Top 10 protection built-in",
                                "DDoS protection included",
                                "SSL termination and certificate management",
                                "Auto-scaling up to 125 instances",
                                "Bot detection and rate limiting"
                            ],
                            cons=[
                                "Higher cost than basic load balancer",
                                "Complex configuration for custom rules",
                                "Adds ~5ms latency"
                            ],
                            cost_impact="$200/month (2 instances, 10GB processed)",
                            performance_impact="Handles 50K requests/sec, 5ms latency",
                            recommended=True
                        ),
                        TradeOff(
                            option_name="Azure Front Door with WAF",
                            pros=[
                                "Global CDN + WAF combined",
                                "Better for multi-region deployments",
                                "Advanced caching rules",
                                "Anycast routing"
                            ],
                            cons=[
                                "More expensive ($300+/month)",
                                "Overkill for single-region apps",
                                "More complex setup"
                            ],
                            cost_impact="$350/month (100GB outbound)",
                            performance_impact="Global edge locations, <10ms worldwide",
                            recommended=False
                        ),
                        TradeOff(
                            option_name="No WAF (Basic Load Balancer)",
                            pros=[
                                "Lowest cost ($20/month)",
                                "Simple setup"
                            ],
                            cons=[
                                "No protection against attacks",
                                "High risk for e-commerce applications",
                                "Will fail PCI-DSS compliance",
                                "Vulnerable to DDoS, injection attacks"
                            ],
                            cost_impact="$20/month",
                            performance_impact="Fast but insecure",
                            recommended=False
                        )
                    ],
                    alternatives=["Cloudflare WAF ($200/month)", "AWS WAF on Azure ($150/month via partnership)"],
                    cost_impact="$200/month",
                    dependencies=["Public endpoints", "SSL certificates"],
                    follow_up_questions=[]
                ),
                StageRecommendation(
                    decision_name="Identity & Access Management",
                    recommendation="Azure AD Premium P1 with MFA",
                    reasoning="Enforce multi-factor authentication for all admin access. Premium P1 adds conditional access policies (e.g., block logins from suspicious locations).",
                    trade_offs=[
                        TradeOff(
                            option_name="Azure AD Premium P1 + MFA",
                            pros=[
                                "Conditional access policies",
                                "Multi-factor authentication enforced",
                                "Privileged Identity Management",
                                "Identity Protection (risk detection)",
                                "Meets SOC 2 and ISO 27001 requirements"
                            ],
                            cons=[
                                "Per-user licensing cost",
                                "Requires user training for MFA setup"
                            ],
                            cost_impact="$60/month (10 admin users @ $6/user)",
                            performance_impact="No impact on app performance",
                            recommended=True
                        ),
                        TradeOff(
                            option_name="Azure AD Free + Basic Auth",
                            pros=[
                                "No additional cost",
                                "Simple username/password"
                            ],
                            cons=[
                                "No MFA enforcement",
                                "Vulnerable to password breaches",
                                "No conditional access",
                                "Fails compliance requirements"
                            ],
                            cost_impact="$0/month",
                            performance_impact="No impact",
                            recommended=False
                        )
                    ],
                    alternatives=["Okta ($120/month for 10 users)", "Auth0 ($100/month)"],
                    cost_impact="$60/month",
                    dependencies=["Azure subscription", "User directory"],
                    follow_up_questions=[]
                )
            ],
            chain_of_thought="E-commerce handles sensitive customer and payment data. Security is non-negotiable. Key Vault prevents credential leaks, WAF blocks attacks, and Azure AD with MFA prevents unauthorized access. These three layers form a solid security foundation.",
            decisions_made=[
                "Implementing defense-in-depth strategy",
                "Protecting secrets with encryption",
                "Enforcing MFA for all admin accounts",
                "Adding WAF to block OWASP Top 10 attacks"
            ],
            estimated_cost="$1,050/month so far (Previous: $775 + Security: $275)",
            can_proceed=True,
            requires_approval=True
        )

    async def _execute_stage_5_review(self, session_data: Dict[str, Any]) -> StageOutput:
        """Stage 5: Final Review - Show all decisions and total cost."""
        # TODO: Use actual decisions from all_stage_decisions
        # For now, return summary of placeholder decisions
        return StageOutput(
            stage=ConversationStage.STAGE_5_REVIEW,
            stage_title="Architecture Review & Final Approval",
            stage_description="Review your complete architecture design before we generate the detailed documentation.",
            recommendations=[
                StageRecommendation(
                    decision_name="Architecture Summary",
                    recommendation="Scalable Azure E-Commerce Platform",
                    reasoning="Based on your requirements for 10K-100K users with a $5K/month budget, I've designed a production-ready architecture that balances cost, performance, and security. All components are managed services to minimize operational overhead.",
                    trade_offs=[],  # No options in final review
                    alternatives=[],
                    cost_impact="$1,050/month total",
                    dependencies=[],
                    follow_up_questions=[]
                )
            ],
            chain_of_thought="This architecture provides: (1) Auto-scaling compute with App Service, (2) Reliable ACID-compliant database with Azure SQL, (3) Performance boost with Redis caching, (4) Enterprise security with Key Vault, WAF, and MFA. Total cost is well within the $5K budget, leaving room for monitoring, backups, and future growth.",
            decisions_made=[
                "✅ Compute: Azure App Service Premium P1v3 ($200/month) - Auto-scaling for 10K-100K users",
                "✅ Database: Azure SQL Database Business Critical ($500/month) - ACID transactions for e-commerce",
                "✅ Caching: Azure Cache for Redis Standard ($75/month) - 80% cache hit rate improvement",
                "✅ Secrets: Azure Key Vault ($15/month) - Encrypted storage for API keys and certificates",
                "✅ Security: Application Gateway with WAF ($200/month) - OWASP Top 10 protection",
                "✅ Identity: Azure AD Premium P1 + MFA ($60/month) - Admin access protection"
            ],
            estimated_cost="💰 Total: $1,050/month (well within $5K budget!)",
            can_proceed=True,
            requires_approval=True
        )

    async def _finalize_and_generate_architecture(
        self,
        session_id: str,
        session_data: Dict[str, Any]
    ) -> OrchestratorOutput:
        """
        All 5 stages approved - now generate the full architecture.
        
        This is where we call Architecture Agent, Cost Agent, and Documentation Agent.
        """
        workflow_start = time.time()
        self.logger.info("All stages approved - generating full architecture for session %s", session_id)
        
        initial_request = session_data.get("initial_request")
        if not initial_request:
            raise ValueError("Session data missing initial_request; cannot finalize workflow")
        
        stage_context = {
            "stage_answers": session_data.get("previous_answers", {}),
            "stage_decisions": session_data.get("all_stage_decisions", {}),
            "stages_completed": session_data.get("stages_completed", []),
            "modification_history": session_data.get("modification_history", []),
        }
        if session_data.get("requirements"):
            stage_context["stage_requirements_snapshot"] = session_data.get("requirements")
        
        requirements_output = await self._execute_requirements_stage(initial_request, stage_context)
        requirements_output.source_user_input = initial_request
        
        architecture_output = await self._execute_architecture_stage(requirements_output)
        cost_output = await self._execute_cost_stage(requirements_output, architecture_output)
        documentation_output = await self._execute_documentation_stage(
            requirements_output,
            architecture_output,
            cost_output
        )
        
        workflow_duration = time.time() - workflow_start
        self._finalize_workflow_metadata(workflow_duration, WorkflowStatus.SUCCESS)
        unique_citations = self._deduplicate_citations(self.all_citations)
        
        completed_stages_raw = session_data.get("stages_completed", [])
        stages_completed = [
            stage.value if hasattr(stage, "value") else stage
            for stage in completed_stages_raw
        ]
        
        return OrchestratorOutput(
            status=WorkflowStatus.SUCCESS,
            conversation_stage=ConversationStage.COMPLETE,
            requirements=requirements_output.model_dump(),
            architecture=architecture_output.model_dump(),
            costs=cost_output.model_dump(),
            documentation=documentation_output.model_dump(),
            citations=unique_citations,
            workflow_metadata=WorkflowMetadata(
                stages_completed=stages_completed + ["architecture", "cost", "documentation"],
                total_duration_seconds=workflow_duration,
                agents_invoked=[
                    "RequirementsAgent",
                    "ArchitectureAgent",
                    "CostAgent",
                    "DocumentationAgent",
                ],
                start_time=datetime.fromtimestamp(workflow_start),
                end_time=datetime.utcnow(),
                clarification_rounds=self.workflow_metadata.get("clarification_rounds", 0),
                requirements_diff=self.workflow_metadata.get("requirements_diff"),
                reviewer_context=self.workflow_metadata.get("reviewer_context"),
                architecture_validation_warnings=self.workflow_metadata.get(
                    "architecture_validation_warnings", []
                ),
            ),
            stages_completed=stages_completed,
            all_stage_decisions=session_data.get("all_stage_decisions", {}),
            session_id=session_id,
            awaiting_response=False,
            can_go_back=False,
            architecture_validation_warnings=self.workflow_metadata.get(
                "architecture_validation_warnings", []
            ),
        )

    async def _go_back_to_previous_stage(
        self,
        session_id: str,
        current_stage: ConversationStage,
        session_data: Dict[str, Any]
    ) -> OrchestratorOutput:
        """Handle user going back to previous stage."""
        self.logger.info(f"User wants to go back from {current_stage}")
        
        # Define stage order
        stage_order = [
            ConversationStage.STAGE_1_REQUIREMENTS,
            ConversationStage.STAGE_2_COMPUTE,
            ConversationStage.STAGE_3_DATA,
            ConversationStage.STAGE_4_SECURITY,
            ConversationStage.STAGE_5_REVIEW
        ]
        
        # Find current stage index
        try:
            current_index = stage_order.index(current_stage)
        except ValueError:
            raise ValueError(f"Unknown stage: {current_stage}")
        
        # Can't go back from first stage
        if current_index == 0:
            raise ValueError("Cannot go back from Stage 1")
        
        # Get previous stage
        previous_stage = stage_order[current_index - 1]
        
        # Remove current stage from completed stages
        stages_completed = session_data.get("stages_completed", [])
        if current_stage.value in stages_completed:
            stages_completed.remove(current_stage.value)
        if previous_stage.value in stages_completed:
            stages_completed.remove(previous_stage.value)
        
        # Re-execute previous stage to show it again
        stage_output = await self._execute_stage(previous_stage, session_data)
        
        return OrchestratorOutput(
            status=WorkflowStatus.AWAITING_STAGE_APPROVAL,
            conversation_stage=previous_stage,
            stage_output=stage_output,
            stages_completed=stages_completed,
            all_stage_decisions=session_data.get("all_stage_decisions", {}),
            session_id=session_id,
            awaiting_response=True,
            can_go_back=len(stages_completed) > 0,
            citations=self.all_citations,
            workflow_metadata=WorkflowMetadata(
                stages_completed=[s.value if hasattr(s, 'value') else s for s in stages_completed],
                total_duration_seconds=0,
                agents_invoked=[],
                start_time=datetime.utcnow(),
                end_time=None
            )
        )

    async def _show_alternatives(
        self,
        session_id: str,
        current_stage: ConversationStage,
        session_data: Dict[str, Any]
    ) -> OrchestratorOutput:
        """Show alternative options for current stage."""
        self.logger.info(f"User wants to see alternatives for {current_stage}")
        
        # Re-execute current stage with same data
        # In a real implementation, this would call the agent with a flag to show more alternatives
        stage_output = await self._execute_stage(current_stage, session_data)
        
        # Add a note in chain of thought that alternatives are being shown
        if stage_output.chain_of_thought:
            stage_output.chain_of_thought = f"📋 Showing alternative options:\n\n{stage_output.chain_of_thought}"
        else:
            stage_output.chain_of_thought = "📋 Here are alternative options for this stage. The alternatives listed in each recommendation section provide additional choices beyond the main trade-offs."
        
        return OrchestratorOutput(
            status=WorkflowStatus.AWAITING_STAGE_APPROVAL,
            conversation_stage=current_stage,
            stage_output=stage_output,
            stages_completed=session_data.get("stages_completed", []),
            all_stage_decisions=session_data.get("all_stage_decisions", {}),
            session_id=session_id,
            awaiting_response=True,
            can_go_back=len(session_data.get("stages_completed", [])) > 0,
            citations=self.all_citations,
            workflow_metadata=WorkflowMetadata(
                stages_completed=session_data.get("stages_completed", []),
                total_duration_seconds=0,
                agents_invoked=[],
                start_time=datetime.utcnow(),
                end_time=None
            )
        )
        raise NotImplementedError("Show alternatives not yet implemented")

    async def _modify_stage_recommendations(
        self,
        session_id: str,
        current_stage: ConversationStage,
        modification_request: Optional[str],
        session_data: Dict[str, Any]
    ) -> OrchestratorOutput:
        """Handle user requesting modifications to recommendations."""
        self.logger.info(f"User wants to modify {current_stage}: {modification_request}")
        
        # Extract requirements and previous decisions
        requirements = session_data.get("requirements", {})
        previous_decisions = session_data.get("all_stage_decisions", {})
        
        # Call AI with the modification request
        try:
            stage_output = await self._generate_ai_recommendations(
                stage=current_stage,
                requirements=requirements,
                previous_decisions=previous_decisions,
                modification_request=modification_request
            )
            self.logger.info(f"✅ AI generated modified recommendations for {current_stage}")
        except Exception as e:
            self.logger.error(f"❌ Error generating modified recommendations: {e}")
            # Fallback to re-executing the stage without modification
            stage_output = await self._execute_stage(current_stage, session_data)
            
            # Add user's modification request to the chain of thought
            user_feedback = modification_request or "Please provide more options or different recommendations"
            modified_thought = f"🔄 Based on your feedback: \"{user_feedback}\"\n\n"
            modified_thought += "I've reviewed the recommendations. In a full implementation, I would adjust the options based on your specific request. "
            modified_thought += "For now, please review the alternatives section in each recommendation for additional options.\n\n"
            modified_thought += stage_output.chain_of_thought or ""
            
            stage_output.chain_of_thought = modified_thought
        
        return OrchestratorOutput(
            status=WorkflowStatus.AWAITING_STAGE_APPROVAL,
            conversation_stage=current_stage,
            stage_output=stage_output,
            stages_completed=session_data.get("stages_completed", []),
            all_stage_decisions=session_data.get("all_stage_decisions", {}),
            session_id=session_id,
            awaiting_response=True,
            can_go_back=len(session_data.get("stages_completed", [])) > 0,
            citations=self.all_citations,
            workflow_metadata=WorkflowMetadata(
                stages_completed=session_data.get("stages_completed", []),
                total_duration_seconds=0,
                agents_invoked=[],
                start_time=datetime.utcnow(),
                end_time=None
            )
        )

    async def _generate_ai_recommendations(
        self,
        stage: ConversationStage,
        requirements: Dict[str, Any],
        previous_decisions: Dict[str, Any],
        modification_request: Optional[str] = None
    ) -> StageOutput:
        """
        Generate dynamic AI-powered recommendations using OpenAI GPT-5.
        
        This is the KEY method that makes recommendations truly dynamic and contextual.
        The AI analyzes the actual requirements and generates relevant options.
        """
        self.logger.info(f"🤖 Generating AI recommendations for {stage}")
        
        # Build context
        context = self._build_stage_context(requirements, previous_decisions)
        prompt = self._build_stage_prompt(stage, context, modification_request)
        
        self.logger.info(f"Calling OpenAI with prompt length: {len(prompt)} chars")
        
        try:
            from src.services.openai_client import AzureOpenAIClient
            openai_client = AzureOpenAIClient()
            
            # Build full prompt with system instructions
            full_prompt = f"{self._get_architecture_agent_instructions(stage)}\n\n{prompt}"
            
            # Call OpenAI (synchronous method, not async)
            response_text = openai_client.generate_completion(
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7
            )
            
            # Parse JSON response
            import json
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            ai_output = json.loads(response_text)
            stage_output = self._convert_ai_response_to_stage_output(ai_output, stage)
            
            self.logger.info(f"✅ Generated {len(stage_output.recommendations)} AI recommendations")
            return stage_output
            
        except Exception as e:
            self.logger.error(f"❌ Error generating AI recommendations: {e}", exc_info=True)
            self.logger.warning("⚠️  Falling back to hardcoded recommendations")
            # Return a simple fallback WITHOUT calling _execute_stage to avoid recursion
            raise
    
    def _build_stage_context(self, requirements: Dict[str, Any], previous_decisions: Dict[str, Any]) -> str:
        """Build context string from requirements and decisions."""
        context_parts = []
        
        # CRITICAL: Include initial_request if it exists (the user's original requirement text)
        if requirements.get("initial_request"):
            context_parts.append(f"**User's Original Request:**\n{requirements['initial_request']}\n")
        
        if requirements:
            context_parts.append("**User Requirements:**")
            for key, value in requirements.items():
                if key != "initial_request":  # Don't duplicate
                    context_parts.append(f"- {key}: {value}")
        
        if previous_decisions:
            context_parts.append("\n**Previous Decisions:**")
            for stage, decision in previous_decisions.items():
                context_parts.append(f"- {stage}: {decision}")
        
        return "\n".join(context_parts)
    
    def _build_stage_prompt(self, stage: ConversationStage, context: str, modification_request: Optional[str] = None) -> str:
        """Build prompt for AI to generate stage recommendations."""
        modification_text = ""
        if modification_request:
            modification_text = f"\n**User Feedback:** {modification_request}\nPlease adjust recommendations based on this feedback.\n"
        
        if stage == ConversationStage.STAGE_2_COMPUTE:
            return f"""Based on the requirements below, suggest 2-3 compute options for Azure.

{context}

{modification_text}

Consider ALL Azure compute services: App Service, AKS, VMSS, Functions, Container Instances, Batch, Spring Apps.

Respond in JSON format:
{{
  "stage_description": "Brief description",
  "recommendations": [
    {{
      "decision_name": "Primary Compute Platform",
      "description": "Choose how to run your application",
      "trade_offs": [
        {{
          "option_name": "Service name",
          "pros": ["advantage 1", "advantage 2"],
          "cons": ["disadvantage 1", "disadvantage 2"],
          "estimated_monthly_cost": 250.00,
          "recommended": true
        }}
      ]
    }}
  ],
  "chain_of_thought": "Your reasoning",
  "running_cost": 250.00
}}"""
        
        elif stage == ConversationStage.STAGE_3_DATA:
            return f"""Based on requirements and compute choice, suggest database and caching options.

{context}

{modification_text}

Consider ALL Azure data services: SQL Database, Cosmos DB, PostgreSQL/MySQL, Redis, Table Storage, Managed Instance.

Same JSON format as Stage 2."""
        
        elif stage == ConversationStage.STAGE_4_SECURITY:
            return f"""Based on all requirements and previous decisions, suggest security options.

{context}

{modification_text}

Consider: Key Vault, WAF (Application Gateway vs Front Door), Azure AD tiers, Network security, DDoS protection.

Same JSON format."""
        
        return "Generate recommendations for this stage."
    
    def _get_architecture_agent_instructions(self, stage: ConversationStage) -> str:
        """Get system instructions for Architecture Agent."""
        return """You are an expert Azure cloud architect. Your job is to analyze requirements and suggest the MOST APPROPRIATE Azure services.

DO NOT default to the same services every time. Analyze the specific requirements:
- Consider budget constraints
- Consider scale (1K users vs 1M users needs different solutions)
- Consider team expertise
- Consider operational overhead
- Consider use case (web app vs batch processing vs API vs data analytics)

Be creative and contextual. If VMSS makes more sense than App Service, suggest it. If Table Storage is sufficient instead of Cosmos DB, say so.

Always respond in valid JSON format."""
    
    def _convert_ai_response_to_stage_output(self, ai_output: Dict[str, Any], stage: ConversationStage) -> StageOutput:
        """Convert AI response to StageOutput format."""
        recommendations = []
        
        for rec_data in ai_output.get("recommendations", []):
            trade_offs = []
            for to_data in rec_data.get("trade_offs", []):
                # Convert estimated_monthly_cost to cost_impact string
                cost = to_data.get("estimated_monthly_cost", 0.0)
                cost_impact = f"${cost:.0f}/month" if cost > 0 else "$0/month"
                
                trade_offs.append(TradeOff(
                    option_name=to_data["option_name"],
                    pros=to_data.get("pros", []),
                    cons=to_data.get("cons", []),
                    cost_impact=cost_impact,
                    performance_impact=to_data.get("performance_impact", "Standard performance"),
                    recommended=to_data.get("recommended", False)
                ))
            
            # Get the recommended option for the recommendation field
            recommended_option = next((t.option_name for t in trade_offs if t.recommended), trade_offs[0].option_name if trade_offs else "No recommendation")
            
            # Calculate cost impact for this recommendation
            recommended_cost = next((to_data.get("estimated_monthly_cost", 0) for to_data in rec_data.get("trade_offs", []) if to_data.get("recommended")), 0)
            
            recommendations.append(StageRecommendation(
                decision_name=rec_data["decision_name"],
                recommendation=recommended_option,
                reasoning=rec_data.get("description", "AI-generated recommendation"),
                trade_offs=trade_offs,
                alternatives=[],
                cost_impact=f"${recommended_cost:.0f}/month",
                dependencies=[],
                follow_up_questions=[]
            ))
        
        return StageOutput(
            stage=stage,
            stage_title=stage.value.replace("_", " ").title(),
            stage_description=ai_output.get("stage_description", ""),
            recommendations=recommendations,
            questions=[],
            chain_of_thought=ai_output.get("chain_of_thought", ""),
            decisions_made=[],
            estimated_cost=f"${ai_output.get('running_cost', 0):.0f}/month so far",
            can_proceed=True,
            requires_approval=True
        )
    
    async def _generate_contextual_questions(self, initial_request: str) -> List:
        """
        Generate 5-8 DEEP, Level 400 contextual questions using AI with Bing grounding.
        
        This method:
        1. Analyzes user's request to detect services and patterns
        2. Performs deep research using Bing Search for Azure best practices
        3. Generates technical questions based on official Azure guidance
        
        Args:
            initial_request: User's original requirement text
            
        Returns:
            List of ClarificationQuestion objects with deep technical questions
        """
        from src.models.schemas import ClarificationQuestion
        
        self.logger.info("🔍 Phase 1: Analyzing requirement and detecting services...")
        
        # Phase 1: Detect what services/patterns are mentioned AND check context level
        analysis_prompt = f"""Analyze this Azure requirement and extract key information:

"{initial_request}"

**First, assess the CONTEXT LEVEL:**
- Level 100 (Foundational): Generic terms like "application", "system", "cloud native" without specifics
- Level 200 (Intermediate): Some specifics mentioned (app type, scale hints, or services)
- Level 300 (Advanced): Clear requirements with services, scale, and constraints
- Level 400 (Expert): Detailed technical requirements with architecture patterns

**Then identify:**
1. Azure services mentioned or implied (e.g., App Service, Database, Storage)
2. Architecture patterns needed (e.g., high availability, multi-region, disaster recovery)
3. Key constraints (e.g., open-source, private endpoints, compliance)
4. What's explicitly stated vs what's missing

**CRITICAL: Check if these FOUNDATIONAL items are missing:**
- Application type/purpose (what does it do?)
- Expected scale/users (how many users?)
- Data requirements (what data needs to be stored?)
- Budget constraints (cost limits?)
- Timeline (when needed?)
- Team expertise (cloud experience level?)

Return JSON:
{{
  "context_level": "100" or "200" or "300" or "400",
  "context_level_reason": "Why this level (e.g., 'Only generic term cloud-native, no specifics')",
  "detected_services": ["service1", "service2"],
  "architecture_patterns": ["pattern1", "pattern2"],
  "constraints": ["constraint1"],
  "explicit_requirements": ["req1"],
  "missing_foundational_info": ["app_type", "scale", "budget"],
  "missing_technical_info": ["replication_strategy", "failover_approach"]
}}
"""
        
        try:
            from src.services.openai_client import AzureOpenAIClient
            openai_client = AzureOpenAIClient()
            
            analysis_text = openai_client.generate_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3
            )
            
            # Parse analysis
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(analysis_text)
            
            self.logger.info(f"Detected services: {analysis.get('detected_services', [])}")
            self.logger.info(f"Architecture patterns: {analysis.get('architecture_patterns', [])}")
            
        except Exception as e:
            self.logger.error(f"Error in Phase 1 analysis: {e}")
            analysis = {
                "context_level": "100",
                "context_level_reason": "Error in analysis, assuming foundational level",
                "detected_services": [],
                "architecture_patterns": [],
                "constraints": [],
                "explicit_requirements": [],
                "missing_foundational_info": ["app_type", "scale", "budget"],
                "missing_technical_info": []
            }
        
        # Phase 2: Deep research using Bing (if available)
        self.logger.info("🔍 Phase 2: Performing deep research on Azure best practices...")
        
        research_context = ""
        try:
            from src.services.bing_search import BingSearchClient
            
            bing_client = BingSearchClient()
            
            # Search for relevant Azure documentation
            search_queries = []
            for service in analysis.get("detected_services", [])[:3]:
                search_queries.append(f"Azure {service} architecture best practices")
            
            for pattern in analysis.get("architecture_patterns", [])[:2]:
                search_queries.append(f"Azure {pattern} design patterns CAF")
            
            research_results = []
            for query in search_queries[:3]:  # Limit to 3 searches
                try:
                    results = bing_client.search(query, count=3)
                    research_results.extend(results.get("webPages", {}).get("value", [])[:2])
                except:
                    continue
            
            if research_results:
                research_context = "\n\nResearch from Azure Documentation:\n"
                for result in research_results[:5]:
                    research_context += f"- {result.get('name', '')}: {result.get('snippet', '')}\n"
                
                self.logger.info(f"✅ Gathered context from {len(research_results)} Azure docs")
        
        except Exception as e:
            self.logger.warning(f"Bing search not available: {e}. Using internal knowledge only.")
        
        # Phase 3: Generate context-aware questions based on context level
        context_level = analysis.get('context_level', '200')
        context_reason = analysis.get('context_level_reason', 'Unknown')
        
        self.logger.info(f"🧠 Phase 3: Generating questions for Context Level {context_level}")
        self.logger.info(f"📝 Reason: {context_reason}")
        
        # Choose prompt based on context level
        if context_level in ['100', '200']:
            # Level 100-200: Missing foundational info - Ask BASIC questions first
            self.logger.info("🎯 Generating FOUNDATIONAL questions (app type, scale, budget)")
            
            foundational_prompt = f"""You are an Azure Solution Architect helping a customer define their requirements.

**Customer's Request:**
"{initial_request}"

**Analysis:**
- Context Level: {context_level} (Foundational - lacks specifics)
- Reason: {context_reason}
- Missing Foundational Info: {analysis.get('missing_foundational_info', [])}

**Your Task:**
Generate 5-7 FOUNDATIONAL questions to understand the basics BEFORE diving into technical details.

**CRITICAL: Ask Level 100-200 questions, NOT Level 400!**

Focus on:
1. **Application Purpose**: What does it do? (web app, API, mobile backend, data processing, IoT)
2. **Expected Scale**: How many users/requests? (< 1K, 1K-10K, 10K-100K, > 100K)
3. **Data Requirements**: What data needs to be stored? (user data, files, analytics, real-time)
4. **Budget Constraints**: Monthly budget range? (< $500, $500-$2K, $2K-$10K, > $10K)
5. **Timeline**: When needed? (prototype, MVP in 3 months, production in 6 months)
6. **Team Expertise**: Cloud experience? (new to Azure, intermediate, experienced)
7. **Business Requirements**: SLA expectations, compliance needs, geographic regions

**EXAMPLES OF GOOD FOUNDATIONAL QUESTIONS:**
✅ "What type of application are you building? (Web application, REST API, Mobile backend, Data pipeline, Real-time processing)"
✅ "How many users do you expect in the first 6 months? This helps us right-size infrastructure and estimate costs."
✅ "What's your monthly cloud budget? (< $500 for dev/test, $500-$2K for small production, $2K-$10K for medium scale, > $10K for enterprise)"
✅ "Does your team have prior Azure experience, or should we recommend managed services with less operational overhead?"

**AVOID Level 400 questions like:**
❌ "For your microservices architecture, would you prefer native AKS service mesh (Open Service Mesh/Linkerd) for mTLS..."
❌ "What is your preferred data consistency and availability trade-off for Azure SQL Database—zone-redundant (ZRS) or geo-redundant..."

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "question": "Clear, simple question about app purpose, scale, or budget?",
      "rationale": "Why this matters for architecture design",
      "options": ["Option 1", "Option 2", "Option 3", "Need help deciding"]
    }}
  ]
}}

Generate 5-7 foundational questions. Keep it simple and focused on gathering basics."""

            final_prompt = foundational_prompt
            
        else:
            # Level 300-400: Has foundational context - Ask TECHNICAL questions
            self.logger.info("🎯 Generating TECHNICAL questions (architecture, patterns, trade-offs)")
            
            deep_domains = """
Azure Cloud Adoption Framework Deep Dive Areas:

1. Workload Architecture & Resilience:
   - RTO/RPO requirements and implications
   - Active-active vs active-passive multi-region
   - Zone redundancy vs region redundancy
   - Failover automation and split-brain handling

2. Data Architecture & Replication:
   - Database replication topology (primary-replica, multi-master)
   - Read replica strategies for scale vs HA
   - Consistency models (strong, eventual, bounded staleness)

3. Network & Security Architecture:
   - Private endpoint vs service endpoint
   - Managed identity for service-to-service auth
   - Zero-trust network principles

4. Operational Excellence:
   - Infrastructure as Code (Bicep, Terraform)
   - Monitoring baselines and SLI/SLO definition
"""
            
            technical_prompt = f"""You are a LEVEL 300-400 Azure Solution Architect.

**Customer's Request:**
"{initial_request}"

**Analysis:**
- Context Level: {context_level} (Has specifics - can ask technical questions)
- Detected Services: {analysis.get('detected_services', [])}
- Architecture Patterns: {analysis.get('architecture_patterns', [])}
- Missing Technical Info: {analysis.get('missing_technical_info', [])}

{research_context}

{deep_domains}

**Your Task:**
Generate 6-8 TECHNICAL questions about architecture, patterns, and trade-offs.

These questions should:
1. Reference specific Azure services and features
2. Explore trade-offs (cost vs resilience, consistency vs performance)
3. Ask about operational strategies (DR testing, failover automation)
4. Include technical multiple-choice options

**EXAMPLES OF GOOD TECHNICAL QUESTIONS:**
✅ "For high availability, what's your acceptable RTO/RPO? This drives active-active vs active-passive and cost: active-active costs 2x but RTO ~seconds."
✅ "For your database, do you need synchronous replication (strong consistency, higher latency) or async replication (eventual consistency, better performance)?"

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "question": "Technical question with Azure-specific terminology?",
      "rationale": "Why this matters with reference to Azure CAF/WAF",
      "options": ["Technical option 1", "Technical option 2", "Technical option 3", "Need more research"]
    }}
  ]
}}

Generate 6-8 technical questions.
1. Go beyond surface-level ("What database?") to architecture implications
2. Reference specific Azure features/patterns from CAF and Well-Architected Framework
3. Explore trade-offs (cost vs resilience, consistency vs performance)
4. Ask about operational strategies (DR testing, failover automation, monitoring)
5. Include multiple-choice options that show technical depth
6. Cite Azure best practices when relevant

EXAMPLES OF LEVEL 400 QUESTIONS:
❌ AVOID: "What SLA do you need?" (too generic)
✅ BETTER: "For your high availability requirement, what's your acceptable RTO (Recovery Time Objective) and RPO (Recovery Point Objective)? This drives decisions on active-active vs active-passive, backup frequency, and cross-region replication."

❌ AVOID: "Which database?" (too simple)
✅ BETTER: "For your open-source database with HA, do you need synchronous replication for strong consistency (higher latency, zone-redundant) or asynchronous replication for performance (eventual consistency, cross-region)?"

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "question": "Deep technical question with Azure-specific terminology?",
      "rationale": "Why this matters with reference to Azure CAF/WAF if possible",
      "options": [
        "Option 1 with technical detail",
        "Option 2 with trade-off explanation",
        "Option 3 with cost/complexity note",
        "Option 4 with 'need more research' option"
      ]
    }}
  ]
}}

Make every question demonstrate Level 400 expertise. Reference specific Azure services and features.
"""
            
            final_prompt = technical_prompt
        
        # Phase 4: Call OpenAI with the selected prompt (foundational or technical)
        try:
            response_text = openai_client.generate_completion(
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.6  # Slightly higher for more creative/detailed questions
            )
            
            # Parse JSON response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(response_text)
            
            # Convert to ClarificationQuestion objects
            questions = []
            for q_data in data.get("questions", [])[:8]:  # Max 8 questions
                questions.append(ClarificationQuestion(
                    question=q_data["question"],
                    rationale=q_data.get("rationale", "Critical for architecture design"),
                    options=q_data.get("options", [])
                ))
            
            self.logger.info(f"✅ Generated {len(questions)} Level 400 technical questions")
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generating deep questions: {e}", exc_info=True)
            raise
    
    def _calculate_complexity_score(self, initial_request: str) -> float:
        """
        Calculate complexity score (0.0-1.0) based on requirement indicators.
        
        This score determines:
        - How many questions to ask in Round 1
        - How many follow-up rounds needed
        - Level of detail required
        
        Args:
            initial_request: User's original requirement
            
        Returns:
            Float between 0.0 (simple) and 1.0 (highly complex)
        """
        score = 0.0
        request_lower = initial_request.lower()
        
        # Cloud-native / Architecture patterns (+0.3) - Moderate complexity baseline
        cloud_native_keywords = ['cloud native', 'cloud-native', 'microservices', 'containers', 'kubernetes', 
                                 'serverless', 'api gateway', 'service mesh', 'event-driven']
        if any(keyword in request_lower for keyword in cloud_native_keywords):
            score += 0.3
        
        # Generic terms that indicate need for discovery (+0.2)
        generic_keywords = ['application', 'system', 'platform', 'solution', 'architecture', 'infrastructure']
        if any(keyword in request_lower for keyword in generic_keywords) and score == 0:
            score += 0.2  # Only if no cloud-native match
        
        # Scale indicators (+0.2)
        scale_keywords = ['million', '1m', 'large scale', 'global', 'enterprise', 'thousands', 'high volume']
        if any(keyword in request_lower for keyword in scale_keywords):
            score += 0.2
        
        # HA/DR indicators (+0.2)
        ha_keywords = ['high availability', 'multi-region', 'disaster recovery', 'failover', 'redundancy', '99.9']
        if any(keyword in request_lower for keyword in ha_keywords):
            score += 0.2
        
        # Compliance/Security indicators (+0.2)
        compliance_keywords = ['hipaa', 'pci', 'sox', 'gdpr', 'compliance', 'iso', 'soc2', 'private endpoint', 'zero trust']
        if any(keyword in request_lower for keyword in compliance_keywords):
            score += 0.2
        
        # Integration/Hybrid indicators (+0.2)
        integration_keywords = ['integrate', 'hybrid', 'on-premises', 'migration', 'vpn', 'expressroute', 'third-party']
        if any(keyword in request_lower for keyword in integration_keywords):
            score += 0.2
        
        # Multiple services mentioned (+0.2)
        service_keywords = ['database', 'storage', 'compute', 'network', 'app service', 'functions', 'kubernetes', 'cosmos', 'sql']
        services_mentioned = sum(1 for keyword in service_keywords if keyword in request_lower)
        if services_mentioned >= 3:
            score += 0.2
        
        self.logger.info(f"📊 Complexity score: {score:.1f} (0.0=simple, 1.0=complex)")
        return min(score, 1.0)
    
    def _determine_question_count(self, complexity_score: float, round_number: int) -> int:
        """
        Determine how many questions to generate based on complexity and round.
        
        Logic:
        - Simple scenarios (score < 0.3): Fewer questions
        - Moderate scenarios (0.3-0.6): Medium questions
        - Complex scenarios (> 0.6): More questions
        - Follow-up rounds have fewer questions than Round 1
        
        Args:
            complexity_score: 0.0-1.0 from _calculate_complexity_score()
            round_number: 1, 2, or 3
            
        Returns:
            Number of questions to generate (AI will generate this many)
        """
        if round_number == 1:
            # Round 1: Initial questions
            if complexity_score < 0.3:
                return 4  # Simple: 4 questions
            elif complexity_score < 0.6:
                return 6  # Moderate: 6 questions
            else:
                return 8  # Complex: 8 questions
        else:
            # Round 2+: Follow-up questions (fewer)
            if complexity_score < 0.3:
                return 2  # Simple follow-ups
            elif complexity_score < 0.6:
                return 3  # Moderate follow-ups
            else:
                return 4  # Complex follow-ups
    
    async def _analyze_stage1_answers(
        self, 
        initial_request: str,
        round_number: int,
        previous_questions: List[str],
        answers: Dict[str, str]
    ) -> Dict:
        """
        Phase 4: Analyze user's answers to determine if more questions needed.
        
        This method decides:
        - What information is now known
        - What critical gaps remain
        - Should we ask follow-up questions?
        - Is the info sufficient for architecture design?
        
        Args:
            initial_request: User's original requirement
            round_number: Which round we just completed (1, 2, or 3)
            previous_questions: List of questions asked in this round
            answers: Dict of question -> answer
            
        Returns:
            Dict with:
            - continue_questioning: bool
            - reason: str explanation
            - missing_info: List[str] gaps identified
            - sufficient_for_design: bool
            - confidence_score: float 0.0-1.0
        """
        self.logger.info(f"🧠 Phase 4: Analyzing Round {round_number} answers...")
        
        from src.services.openai_client import AzureOpenAIClient
        openai_client = AzureOpenAIClient()
        
        # Build summary of Q&A
        qa_summary = ""
        for i, (q, a) in enumerate(answers.items(), 1):
            qa_summary += f"\nQ{i}: {q}\nA{i}: {a}\n"
        
        analysis_prompt = f"""You are analyzing answers from a customer discovery session.

**Original Request:**
"{initial_request}"

**Round {round_number} - Questions & Answers:**
{qa_summary}

**CRITICAL DECISION RULES (FOLLOW THESE EXACTLY):**

1. **Round 1 (Just Completed):**
   - ALWAYS continue to Round 2 (even if basics seem clear)
   - Reason: Need to drill deeper into technical requirements
   - Only exception: User explicitly provided DETAILED technical specs in original request
   
2. **Round 2 (Just Completed):**
   - Continue to Round 3 if:
     * High availability/DR requirements but RTO/RPO not specified
     * Multi-region mentioned but failover strategy unclear
     * Compliance mentioned but specific controls not discussed
     * Performance requirements vague ("fast", "scalable")
   - Stop if:
     * All major architectural decisions can be made with current info
     * Confidence score >= 0.85
   
3. **Round 3 (Just Completed):**
   - ALWAYS stop (maximum rounds reached)

**Evaluate:**
1. What SPECIFIC technical information is NOW KNOWN?
2. What ARCHITECTURAL DECISIONS still have ambiguity?
3. Would an architect ask follow-ups in real conversation?

**Examples of "Need Round 2":**
- User said "web application" but didn't specify: containerized vs PaaS, stateful vs stateless
- User said "database" but didn't specify: relational vs NoSQL, consistency requirements
- User said "users: 10,000" but didn't specify: concurrent vs total, geographic distribution
- User said "budget: $2K" but didn't specify: dev+prod or just prod, growth expectations

**Examples of "Can Stop After Round 2":**
- User answered: App Service for web tier, Azure SQL with zone-redundant HA, 10K concurrent users in US-East, $2K/month prod budget
- User answered: Static site (no backend), Azure Blob + CDN, < 1K visitors, $100/month budget

Return ONLY valid JSON:
{{
  "continue_questioning": true/false,
  "reason": "Be specific - which architectural decisions need clarification?",
  "missing_info": ["specific technical gap 1", "gap 2"],
  "sufficient_for_design": true/false,
  "confidence_score": 0.85,
  "known_requirements": ["concrete requirement 1", "req 2"]
}}

**Remember: Round 1 → Almost always continue. Round 2 → Continue if major technical gaps remain.**
"""
        
        try:
            response_text = openai_client.generate_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3
            )
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(response_text)
            
            # Apply hard limit: max 3 rounds
            if round_number >= 3:
                analysis["continue_questioning"] = False
                analysis["reason"] = "Maximum rounds (3) reached. Proceeding with available information."
            
            self.logger.info(f"📊 Analysis: Continue={analysis['continue_questioning']}, Confidence={analysis.get('confidence_score', 0):.2f}")
            self.logger.info(f"📝 Reason: {analysis['reason']}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing answers: {e}", exc_info=True)
            # Safe fallback: stop after round 1 or 2, never continue past 3
            return {
                "continue_questioning": round_number < 2,
                "reason": f"Error in analysis, using safe default (stop after round {round_number})",
                "missing_info": [],
                "sufficient_for_design": True,
                "confidence_score": 0.7
            }
    
    async def _generate_followup_questions(
        self,
        initial_request: str,
        round_number: int,
        previous_answers: Dict[str, str],
        missing_info: List[str],
        complexity_score: float
    ) -> List:
        """
        Phase 5: Generate targeted follow-up questions based on gaps.
        
        These questions:
        - Build on previous answers (reference them)
        - Address specific gaps identified
        - Are deeper/more technical than Round 1
        - Focus on operational or design implications
        
        Args:
            initial_request: User's original requirement
            round_number: Next round number (2 or 3)
            previous_answers: All answers collected so far
            missing_info: List of gaps from Phase 4 analysis
            complexity_score: 0.0-1.0 to determine question count
            
        Returns:
            List of ClarificationQuestion objects (AI-generated)
        """
        from src.models.schemas import ClarificationQuestion
        
        self.logger.info(f"🔍 Phase 5: Generating Round {round_number} follow-up questions...")
        
        from src.services.openai_client import AzureOpenAIClient
        openai_client = AzureOpenAIClient()
        
        # Determine how many follow-up questions to generate
        target_count = self._determine_question_count(complexity_score, round_number)
        
        # Build summary of what we know
        previous_qa = ""
        for q, a in previous_answers.items():
            previous_qa += f"- Q: {q}\n  A: {a}\n"
        
        followup_prompt = f"""You are generating Round {round_number} follow-up questions for Azure architecture discovery.

**Original Request:**
"{initial_request}"

**What We Know (Previous Answers):**
{previous_qa}

**Identified Gaps:**
{', '.join(missing_info)}

**Generate exactly {target_count} TARGETED follow-up questions that:**
1. Address the specific gaps identified above
2. Build on previous answers (reference them in rationale)
3. Are DEEPER than Round 1 questions (operational details, trade-offs)
4. Focus on design implications, not just facts

**Example of Good Follow-Up:**
User said "99.99% SLA" and "PostgreSQL" in Round 1
→ Round 2: "For 99.99% SLA with Azure Database for PostgreSQL, what's your acceptable RTO for failover? This determines if we need Flexible Server with zone-redundant HA (RTO ~60-120s, higher cost) vs read replicas for manual failover (RTO ~5-10min, lower cost)."

**Example of Referencing Previous Answers:**
User said "Multi-region" in Round 1
→ Round 2: "Since you need multi-region deployment, will traffic failover be DNS-based (Azure Traffic Manager, RTO ~1-2min) or connection-level (Azure Front Door, RTO ~30s)? This impacts both cost and complexity."

Return ONLY valid JSON with EXACTLY {target_count} questions:
{{
  "questions": [
    {{
      "question": "Targeted follow-up question referencing previous answers?",
      "rationale": "Why this matters given what we already know",
      "options": ["Option 1", "Option 2", "Option 3", "Need more research"]
    }}
  ]
}}

Make questions specific and technical. Reference Azure services and previous answers.
"""
        
        try:
            response_text = openai_client.generate_completion(
                messages=[{"role": "user", "content": followup_prompt}],
                temperature=0.6
            )
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(response_text)
            
            # Convert to ClarificationQuestion objects
            questions = []
            for q_data in data.get("questions", [])[:target_count]:
                questions.append(ClarificationQuestion(
                    question=q_data.get("question", ""),
                    rationale=q_data.get("rationale", "Follow-up for architecture design"),
                    options=q_data.get("options", [])
                ))
            
            self.logger.info(f"✅ Generated {len(questions)} follow-up questions for Round {round_number}")
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generating follow-up questions: {e}", exc_info=True)
            raise
