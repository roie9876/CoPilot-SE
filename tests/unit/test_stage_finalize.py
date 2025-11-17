import logging
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.orchestrator.master_orchestrator import MasterOrchestrator
from src.models.schemas import (
    ArchitectureOutput,
    CloudPlatform,
    ConversationStage,
    CostOutput,
    DocumentationOutput,
    DocumentMetadata,
    DiagramOutput,
    RequirementsOutput,
    WellArchitectedAnalysis,
    WorkflowStatus,
)


@pytest.mark.asyncio
async def test_finalize_generates_full_workflow(monkeypatch):
    orchestrator = MasterOrchestrator.__new__(MasterOrchestrator)
    orchestrator.logger = logging.getLogger("MasterOrchestratorTest")
    orchestrator.requirements_agent = None
    orchestrator.architecture_agent = None
    orchestrator.cost_agent = None
    orchestrator.documentation_agent = None
    orchestrator.session_cache = {}
    orchestrator.kg_orchestrator = None
    orchestrator.max_retries = 0
    orchestrator.retry_delay = 0

    # Initialize baseline workflow metadata/citations/errors
    MasterOrchestrator._initialize_workflow_metadata(orchestrator)

    requirements_output = RequirementsOutput(
        target_cloud=CloudPlatform.AZURE,
        region="eastus",
        functional_requirements=["Serve traffic"],
    )

    architecture_output = ArchitectureOutput(
        target_cloud=CloudPlatform.AZURE,
        architecture_summary="Azure web app",
        architecture_diagram="graph TD; A-->B;",
        design_rationale=WellArchitectedAnalysis(
            operational_excellence="ops",
            security="sec",
            reliability="rel",
            performance_efficiency="perf",
            cost_optimization="cost",
        ),
    )
    architecture_output.validation_warnings = ["Normalized alias"]

    cost_output = CostOutput(target_cloud=CloudPlatform.AZURE, region="eastus")

    documentation_output = DocumentationOutput(
        format="markdown",
        content="# Architecture",
        diagrams=[
            DiagramOutput(
                name="overview",
                format="mermaid",
                content="graph TD;",
                description="High-level diagram",
            )
        ],
        metadata=DocumentMetadata(
            title="Azure Architecture",
            cloud_platform=CloudPlatform.AZURE,
            filename="architecture.md",
            generated_at=datetime.utcnow(),
        ),
    )

    async def fake_architecture_stage(requirements):
        orchestrator.workflow_metadata["architecture_validation_warnings"] = architecture_output.validation_warnings
        return architecture_output

    orchestrator._execute_requirements_stage = AsyncMock(return_value=requirements_output)
    orchestrator._execute_architecture_stage = AsyncMock(side_effect=fake_architecture_stage)
    orchestrator._execute_cost_stage = AsyncMock(return_value=cost_output)
    orchestrator._execute_documentation_stage = AsyncMock(return_value=documentation_output)
    orchestrator._deduplicate_citations = lambda citations: citations

    session_data = {
        "initial_request": "Build something",
        "previous_answers": {"q1": "ans"},
        "all_stage_decisions": {"stage_2_compute": ["Azure App Service"]},
        "stages_completed": ["stage_1_requirements", "stage_2_compute", "stage_3_data", "stage_4_security", "stage_5_review"],
    }

    result = await orchestrator._finalize_and_generate_architecture("session-123", session_data)

    assert result.status == WorkflowStatus.SUCCESS
    stage_value = getattr(result.conversation_stage, "value", result.conversation_stage)
    assert stage_value == ConversationStage.COMPLETE.value
    assert result.architecture_validation_warnings == ["Normalized alias"]
    assert result.all_stage_decisions == session_data["all_stage_decisions"]
    orchestrator._execute_requirements_stage.assert_awaited()
    orchestrator._execute_architecture_stage.assert_awaited()
    orchestrator._execute_cost_stage.assert_awaited()
    orchestrator._execute_documentation_stage.assert_awaited()

    args, _ = orchestrator._execute_requirements_stage.await_args
    assert args[0] == "Build something"
    assert args[1]["stage_answers"] == {"q1": "ans"}


@pytest.mark.asyncio
async def test_finalize_requires_initial_request():
    orchestrator = MasterOrchestrator.__new__(MasterOrchestrator)
    orchestrator.logger = logging.getLogger("MasterOrchestratorTest")
    MasterOrchestrator._initialize_workflow_metadata(orchestrator)

    with pytest.raises(ValueError):
        await orchestrator._finalize_and_generate_architecture("session-123", {})
