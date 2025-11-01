# Orchestration Workflow Logic

**Project:** Co-Pilot SE  
**Purpose:** Complete workflow execution logic for Master Orchestrator

---

## Overview

The Master Orchestrator coordinates a **sequential 4-stage pipeline** where each agent's output feeds into the next. The workflow is stateless, managed in-memory, and includes retry logic with exponential backoff.

**Critical Constraints:**
- ✅ Sequential execution (no parallel agent calls)
- ✅ Each stage validates previous output before proceeding
- ✅ Retry on transient failures (API timeouts, rate limits)
- ✅ Stop on validation errors or clarification needs
- ✅ Track citations across all stages

---

## Workflow Stages

```
┌─────────────────────────────────────────────────────────────┐
│                    USER REQUEST                              │
│         "Design an AWS e-commerce platform                   │
│          for 10K users with $2000 budget"                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: REQUIREMENTS EXTRACTION                            │
│  Agent: RequirementsAgent                                    │
│  Input: user_request, context                                │
│  Output: RequirementsOutput (target_cloud, functional_reqs,  │
│          non_functional_reqs, technical_constraints)         │
│                                                              │
│  SUCCESS PATH → Stage 2                                      │
│  CLARIFICATION NEEDED → Return questions to user             │
│  ERROR → Retry (max 2 attempts) or fail                     │
└────────────────┬────────────────────────────────────────────┘
                 │ requirements_output
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: ARCHITECTURE DESIGN                                │
│  Agent: ArchitectureAgent                                    │
│  Input: requirements_output, target_cloud, region            │
│  Output: ArchitectureOutput (services[], diagram,            │
│          design_rationale, citations)                        │
│                                                              │
│  SUCCESS PATH → Stage 3                                      │
│  ERROR → Retry (max 2 attempts) or fail                     │
└────────────────┬────────────────────────────────────────────┘
                 │ architecture_output
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: COST ESTIMATION                                    │
│  Agent: CostAgent                                            │
│  Input: architecture_output, target_cloud, region            │
│  Output: CostOutput (service_costs[], total_monthly_cost_*,  │
│          optimization_recommendations, sources)              │
│                                                              │
│  SUCCESS PATH → Stage 4                                      │
│  ERROR → Retry (max 2 attempts) or fail                     │
└────────────────┬────────────────────────────────────────────┘
                 │ cost_output
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 4: DOCUMENTATION GENERATION                           │
│  Agent: DocumentationAgent                                   │
│  Input: requirements_output, architecture_output,            │
│         cost_output, output_format                           │
│  Output: DocumentationOutput (content, diagrams[],           │
│          metadata)                                           │
│                                                              │
│  SUCCESS PATH → Return complete result                       │
│  ERROR → Retry (max 2 attempts) or fail                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL OUTPUT                              │
│  OrchestratorOutput:                                         │
│  - status: "success"                                         │
│  - requirements: {...}                                       │
│  - architecture: {...}                                       │
│  - costs: {...}                                              │
│  - documentation: {...}                                      │
│  - citations: [...]                                          │
│  - workflow_metadata: {...}                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Python Implementation

### Master Orchestrator Class

```python
from typing import Dict, Optional, List
from datetime import datetime
import time
import logging
from pydantic import ValidationError

from src.agents.requirements_agent import RequirementsAgent
from src.agents.architecture_agent import ArchitectureAgent
from src.agents.cost_agent import CostAgent
from src.agents.documentation_agent import DocumentationAgent
from src.models.schemas import (
    OrchestratorInput,
    OrchestratorOutput,
    WorkflowStatus,
    WorkflowMetadata,
    Citation,
)

logger = logging.getLogger(__name__)

class MasterOrchestrator:
    """
    Master Orchestrator for Co-Pilot SE workflow.
    
    Coordinates 4 specialized agents in a sequential pipeline:
    1. Requirements Agent
    2. Architecture Agent
    3. Cost Agent
    4. Documentation Agent
    """
    
    def __init__(self):
        """Initialize all agents."""
        self.requirements_agent = RequirementsAgent()
        self.architecture_agent = ArchitectureAgent()
        self.cost_agent = CostAgent()
        self.documentation_agent = DocumentationAgent()
        
        self.max_retries = 2
        self.retry_delay_base = 2  # seconds
    
    async def orchestrate(
        self, 
        input_data: OrchestratorInput
    ) -> OrchestratorOutput:
        """
        Execute complete workflow from requirements to documentation.
        
        Args:
            input_data: User request and options
            
        Returns:
            OrchestratorOutput with all agent results or clarification needs
        """
        start_time = datetime.now()
        workflow_metadata = WorkflowMetadata(
            stages_completed=[],
            total_duration_seconds=0.0,
            agents_invoked=[],
            start_time=start_time
        )
        all_citations: List[Citation] = []
        
        try:
            # ============================================================
            # STAGE 1: REQUIREMENTS EXTRACTION
            # ============================================================
            logger.info("Stage 1: Extracting requirements...")
            
            requirements_result = await self._invoke_with_retry(
                agent=self.requirements_agent,
                method_name="extract_requirements",
                input_data={
                    "user_input": input_data.user_request,
                    "context": input_data.context
                },
                stage_name="requirements_extraction"
            )
            
            if requirements_result is None:
                return self._create_error_response(
                    "Requirements extraction failed after retries",
                    workflow_metadata,
                    all_citations
                )
            
            workflow_metadata.stages_completed.append("requirements_extraction")
            workflow_metadata.agents_invoked.append("RequirementsAgent")
            
            # Check if clarification needed
            if requirements_result.get("needs_clarification", False):
                logger.info("Clarification needed from user")
                workflow_metadata.end_time = datetime.now()
                workflow_metadata.total_duration_seconds = (
                    workflow_metadata.end_time - start_time
                ).total_seconds()
                
                return OrchestratorOutput(
                    status=WorkflowStatus.NEEDS_CLARIFICATION,
                    requirements=requirements_result,
                    clarifying_questions=requirements_result.get("clarifying_questions", []),
                    ambiguities=requirements_result.get("ambiguities_detected", []),
                    citations=all_citations,
                    workflow_metadata=workflow_metadata
                )
            
            # Validate target_cloud is present
            target_cloud = requirements_result.get("target_cloud")
            if not target_cloud:
                return self._create_error_response(
                    "Could not determine target cloud platform",
                    workflow_metadata,
                    all_citations,
                    requirements=requirements_result
                )
            
            # ============================================================
            # STAGE 2: ARCHITECTURE DESIGN
            # ============================================================
            logger.info(f"Stage 2: Designing {target_cloud} architecture...")
            
            architecture_result = await self._invoke_with_retry(
                agent=self.architecture_agent,
                method_name="design_architecture",
                input_data={
                    "requirements": requirements_result,
                    "target_cloud": target_cloud,
                    "region": requirements_result.get("region", "us-east-1")
                },
                stage_name="architecture_design"
            )
            
            if architecture_result is None:
                return self._create_error_response(
                    "Architecture design failed after retries",
                    workflow_metadata,
                    all_citations,
                    requirements=requirements_result
                )
            
            workflow_metadata.stages_completed.append("architecture_design")
            workflow_metadata.agents_invoked.append("ArchitectureAgent")
            
            # Collect citations
            if "citations" in architecture_result:
                all_citations.extend(architecture_result["citations"])
            
            # ============================================================
            # STAGE 3: COST ESTIMATION
            # ============================================================
            logger.info("Stage 3: Estimating costs...")
            
            cost_result = await self._invoke_with_retry(
                agent=self.cost_agent,
                method_name="estimate_costs",
                input_data={
                    "architecture": architecture_result,
                    "target_cloud": target_cloud,
                    "region": requirements_result.get("region", "us-east-1")
                },
                stage_name="cost_estimation"
            )
            
            if cost_result is None:
                return self._create_error_response(
                    "Cost estimation failed after retries",
                    workflow_metadata,
                    all_citations,
                    requirements=requirements_result,
                    architecture=architecture_result
                )
            
            workflow_metadata.stages_completed.append("cost_estimation")
            workflow_metadata.agents_invoked.append("CostAgent")
            
            # Collect citations
            if "sources" in cost_result:
                all_citations.extend(cost_result["sources"])
            
            # ============================================================
            # STAGE 4: DOCUMENTATION GENERATION
            # ============================================================
            logger.info("Stage 4: Generating documentation...")
            
            output_format = input_data.options.get("output_format", "markdown")
            
            documentation_result = await self._invoke_with_retry(
                agent=self.documentation_agent,
                method_name="generate_documentation",
                input_data={
                    "requirements": requirements_result,
                    "architecture": architecture_result,
                    "costs": cost_result,
                    "output_format": output_format
                },
                stage_name="documentation_generation"
            )
            
            if documentation_result is None:
                return self._create_error_response(
                    "Documentation generation failed after retries",
                    workflow_metadata,
                    all_citations,
                    requirements=requirements_result,
                    architecture=architecture_result,
                    costs=cost_result
                )
            
            workflow_metadata.stages_completed.append("documentation_generation")
            workflow_metadata.agents_invoked.append("DocumentationAgent")
            
            # ============================================================
            # SUCCESS: ALL STAGES COMPLETE
            # ============================================================
            workflow_metadata.end_time = datetime.now()
            workflow_metadata.total_duration_seconds = (
                workflow_metadata.end_time - start_time
            ).total_seconds()
            
            logger.info(
                f"Workflow completed successfully in "
                f"{workflow_metadata.total_duration_seconds:.2f}s"
            )
            
            return OrchestratorOutput(
                status=WorkflowStatus.SUCCESS,
                requirements=requirements_result,
                architecture=architecture_result,
                costs=cost_result,
                documentation=documentation_result,
                citations=all_citations,
                workflow_metadata=workflow_metadata
            )
        
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return self._create_error_response(
                f"Data validation error: {str(e)}",
                workflow_metadata,
                all_citations
            )
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._create_error_response(
                f"Unexpected error: {str(e)}",
                workflow_metadata,
                all_citations
            )
    
    async def _invoke_with_retry(
        self,
        agent,
        method_name: str,
        input_data: Dict,
        stage_name: str
    ) -> Optional[Dict]:
        """
        Invoke agent method with exponential backoff retry.
        
        Args:
            agent: Agent instance
            method_name: Method name to call
            input_data: Input data dict
            stage_name: Stage name for logging
            
        Returns:
            Agent result dict or None if all retries failed
        """
        method = getattr(agent, method_name)
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"[{stage_name}] Attempt {attempt + 1}/{self.max_retries + 1}")
                
                result = await method(**input_data)
                
                logger.info(f"[{stage_name}] Success on attempt {attempt + 1}")
                return result
            
            except ValidationError as e:
                # Don't retry validation errors
                logger.error(f"[{stage_name}] Validation error: {e}")
                raise
            
            except (TimeoutError, ConnectionError) as e:
                # Retry transient errors
                if attempt < self.max_retries:
                    delay = self.retry_delay_base ** attempt
                    logger.warning(
                        f"[{stage_name}] Transient error on attempt {attempt + 1}: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"[{stage_name}] Failed after {self.max_retries + 1} attempts: {e}"
                    )
                    return None
            
            except Exception as e:
                # Log unexpected errors but don't retry
                logger.error(f"[{stage_name}] Unexpected error: {e}", exc_info=True)
                return None
        
        return None
    
    def _create_error_response(
        self,
        error_message: str,
        workflow_metadata: WorkflowMetadata,
        citations: List[Citation],
        **partial_results
    ) -> OrchestratorOutput:
        """
        Create error response with partial results.
        
        Args:
            error_message: Error description
            workflow_metadata: Workflow metadata
            citations: Collected citations
            **partial_results: Any completed agent results
            
        Returns:
            OrchestratorOutput with error status
        """
        workflow_metadata.end_time = datetime.now()
        workflow_metadata.total_duration_seconds = (
            workflow_metadata.end_time - workflow_metadata.start_time
        ).total_seconds()
        
        return OrchestratorOutput(
            status=WorkflowStatus.ERROR,
            error_message=error_message,
            errors=[{
                "stage": workflow_metadata.stages_completed[-1] if workflow_metadata.stages_completed else "initialization",
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }],
            citations=citations,
            workflow_metadata=workflow_metadata,
            **partial_results
        )
```

---

## State Management

### In-Memory State (POC)

For the POC, all state is managed **in-memory** within the orchestration execution:

```python
class WorkflowState:
    """
    Workflow execution state (in-memory for POC).
    
    For production, consider:
    - Redis for distributed state
    - Azure Table Storage for persistence
    - Cosmos DB for complex queries
    """
    
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.user_request: Optional[str] = None
        self.requirements: Optional[Dict] = None
        self.architecture: Optional[Dict] = None
        self.costs: Optional[Dict] = None
        self.documentation: Optional[Dict] = None
        self.citations: List[Citation] = []
        self.current_stage: str = "initialization"
        self.status: str = "in_progress"
        self.errors: List[Dict] = []
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Export state as dictionary."""
        return {
            "request_id": self.request_id,
            "user_request": self.user_request,
            "requirements": self.requirements,
            "architecture": self.architecture,
            "costs": self.costs,
            "documentation": self.documentation,
            "citations": [c.dict() for c in self.citations],
            "current_stage": self.current_stage,
            "status": self.status,
            "errors": self.errors,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }
```

**Note**: State is NOT persisted in POC. Each orchestration call is independent.

---

## Error Handling

### Error Types

```python
from enum import Enum

class ErrorType(str, Enum):
    """Types of errors in workflow."""
    VALIDATION_ERROR = "validation_error"
    API_ERROR = "api_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    UNKNOWN_ERROR = "unknown_error"

class WorkflowError(Exception):
    """Custom exception for workflow errors."""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType,
        stage: str,
        retryable: bool = False,
        details: Optional[Dict] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.stage = stage
        self.retryable = retryable
        self.details = details or {}
```

### Retry Logic

```python
def retry_with_exponential_backoff(
    max_retries: int = 2,
    base_delay: float = 2.0,
    max_delay: float = 60.0
):
    """
    Decorator for exponential backoff retry.
    
    Args:
        max_retries: Maximum retry attempts
        base_delay: Base delay in seconds (doubles each retry)
        max_delay: Maximum delay cap
        
    Usage:
        @retry_with_exponential_backoff(max_retries=3)
        async def call_api():
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (TimeoutError, ConnectionError, RateLimitError) as e:
                    if attempt < max_retries:
                        delay = min(base_delay ** attempt, max_delay)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} after {type(e).__name__}. "
                            f"Waiting {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Failed after {max_retries + 1} attempts")
                        raise
                except ValidationError:
                    # Don't retry validation errors
                    logger.error("Validation error - not retrying")
                    raise
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    raise
        return wrapper
    return decorator
```

---

## Citation Collection

### Tracking Sources Across Stages

```python
class CitationCollector:
    """
    Collect and deduplicate citations across all agents.
    """
    
    def __init__(self):
        self.citations: List[Citation] = []
        self._seen_urls: set = set()
    
    def add(self, citation: Citation) -> None:
        """Add citation if not already present."""
        if citation.url not in self._seen_urls:
            self.citations.append(citation)
            self._seen_urls.add(citation.url)
    
    def add_multiple(self, citations: List[Citation]) -> None:
        """Add multiple citations."""
        for citation in citations:
            self.add(citation)
    
    def get_all(self) -> List[Citation]:
        """Get all collected citations."""
        return self.citations
    
    def get_by_stage(self, stage: str) -> List[Citation]:
        """Get citations from specific stage (if tracked)."""
        # For POC, return all
        # For production, could tag citations by stage
        return self.citations
```

**Usage in Orchestrator:**

```python
citation_collector = CitationCollector()

# After architecture stage
if "citations" in architecture_result:
    citation_collector.add_multiple(
        [Citation(**c) for c in architecture_result["citations"]]
    )

# After cost stage
if "sources" in cost_result:
    citation_collector.add_multiple(
        [Citation(**c) for c in cost_result["sources"]]
    )

# Include in final output
return OrchestratorOutput(
    ...
    citations=citation_collector.get_all()
)
```

---

## Clarification Flow

### Handling Ambiguous Requests

```python
async def handle_clarification_response(
    orchestrator: MasterOrchestrator,
    original_request: str,
    clarification_answers: Dict[str, str]
) -> OrchestratorOutput:
    """
    Resume workflow after user provides clarification.
    
    Args:
        orchestrator: Orchestrator instance
        original_request: Original user request
        clarification_answers: Dict of question -> answer
        
    Returns:
        OrchestratorOutput with completed workflow
    """
    # Combine original request with clarifications
    enhanced_request = f"{original_request}\n\nAdditional Context:\n"
    for question, answer in clarification_answers.items():
        enhanced_request += f"- {question}: {answer}\n"
    
    # Re-run orchestration with enhanced context
    input_data = OrchestratorInput(
        user_request=enhanced_request,
        context={
            "is_clarification_response": True,
            "original_request": original_request,
            "clarifications": clarification_answers
        }
    )
    
    return await orchestrator.orchestrate(input_data)
```

**Example Flow:**

1. **Initial Request**: "Build a cloud solution"
2. **Orchestrator Response**: 
   ```json
   {
     "status": "needs_clarification",
     "clarifying_questions": [
       "Which cloud platform? (AWS, Azure, GCP, Oracle)",
       "What is the primary use case?",
       "Estimated user count?",
       "Monthly budget?"
     ]
   }
   ```
3. **User Provides Answers**: 
   ```json
   {
     "Which cloud platform?": "AWS",
     "What is the primary use case?": "E-commerce website",
     "Estimated user count?": "10,000 users",
     "Monthly budget?": "$2000"
   }
   ```
4. **Resume Workflow**: Call `handle_clarification_response()` → Complete workflow

---

## Performance Optimization

### Parallel Data Fetching (Within Agents)

While **agents execute sequentially**, each agent can fetch data in parallel:

```python
import asyncio

async def fetch_data_in_parallel(urls: List[str]) -> List[Dict]:
    """
    Fetch multiple URLs concurrently (within an agent).
    
    Usage:
        # Inside ArchitectureAgent.design_architecture()
        doc_urls = [
            "https://aws.amazon.com/ec2/pricing/",
            "https://aws.amazon.com/s3/pricing/",
            "https://aws.amazon.com/rds/pricing/"
        ]
        results = await fetch_data_in_parallel(doc_urls)
    """
    async def fetch_one(url: str) -> Dict:
        # Use Bing Search API or direct HTTP request
        result = await bing_search_client.search(url)
        return {"url": url, "data": result}
    
    tasks = [fetch_one(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Caching (Future Enhancement)

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_agent_call(agent_name: str, input_hash: str) -> Optional[Dict]:
    """
    Cache agent results (for production).
    
    Note: NOT implemented in POC (stateless requirement).
    """
    # For production:
    # - Use Redis for distributed cache
    # - Cache key: hash(agent_name + input_data)
    # - TTL: 1 hour
    pass
```

---

## Testing Workflow

### Integration Test Example

```python
import pytest
from src.orchestrator.master_orchestrator import MasterOrchestrator
from src.models.schemas import OrchestratorInput

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_workflow_aws_ecommerce():
    """Test complete workflow for AWS e-commerce use case."""
    orchestrator = MasterOrchestrator()
    
    input_data = OrchestratorInput(
        user_request="Design an AWS e-commerce platform for 10,000 users with $2000 monthly budget. Team knows Python and React.",
        context=None,
        options={
            "generate_documentation": True,
            "output_format": "markdown"
        }
    )
    
    result = await orchestrator.orchestrate(input_data)
    
    # Assertions
    assert result.status == "success"
    assert result.requirements is not None
    assert result.requirements["target_cloud"] == "aws"
    assert result.architecture is not None
    assert len(result.architecture["services"]) > 0
    assert result.costs is not None
    assert result.costs["total_monthly_cost_medium"] <= 2500  # ±30% tolerance
    assert result.documentation is not None
    assert len(result.citations) > 0
    
    # Workflow metadata checks
    assert "requirements_extraction" in result.workflow_metadata.stages_completed
    assert "architecture_design" in result.workflow_metadata.stages_completed
    assert "cost_estimation" in result.workflow_metadata.stages_completed
    assert "documentation_generation" in result.workflow_metadata.stages_completed
    assert result.workflow_metadata.total_duration_seconds > 0

@pytest.mark.asyncio
async def test_workflow_with_clarification():
    """Test workflow when clarification is needed."""
    orchestrator = MasterOrchestrator()
    
    input_data = OrchestratorInput(
        user_request="Build a cloud solution",  # Ambiguous
        context=None
    )
    
    result = await orchestrator.orchestrate(input_data)
    
    # Should request clarification
    assert result.status == "needs_clarification"
    assert len(result.clarifying_questions) > 0
    assert result.requirements is not None
    assert result.requirements["needs_clarification"] is True
```

---

**Last Updated**: November 1, 2025  
**Next**: See `.copilot/data-sources.md` for online data retrieval patterns
