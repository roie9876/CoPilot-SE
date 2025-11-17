import logging
from datetime import datetime

import pytest

from src.orchestrator.master_orchestrator import MasterOrchestrator
from src.models.schemas import OrchestratorOutput, WorkflowMetadata, WorkflowStatus


def _stub_orchestrator():
    orchestrator = MasterOrchestrator.__new__(MasterOrchestrator)
    orchestrator.logger = logging.getLogger("MasterOrchestratorTest")
    orchestrator.workflow_metadata = {"architecture_validation_warnings": []}
    return orchestrator


def test_record_architecture_validation_warnings_updates_metadata_and_logs(caplog):
    orchestrator = _stub_orchestrator()
    warnings = ["Removed unsupported service 'Amazon RDS'."]

    with caplog.at_level(logging.WARNING):
        orchestrator._record_architecture_validation_warnings(warnings)

    assert orchestrator.workflow_metadata["architecture_validation_warnings"] == warnings
    assert "Amazon RDS" in caplog.text


def test_record_architecture_validation_warnings_resets_when_empty():
    orchestrator = _stub_orchestrator()
    orchestrator.workflow_metadata["architecture_validation_warnings"] = ["Old warning"]

    orchestrator._record_architecture_validation_warnings([])

    assert orchestrator.workflow_metadata["architecture_validation_warnings"] == []


def test_orchestrator_output_serializes_validation_warnings():
    metadata = WorkflowMetadata(
        stages_completed=["requirements"],
        total_duration_seconds=1.0,
        agents_invoked=["RequirementsAgent"],
        start_time=datetime.utcnow(),
        architecture_validation_warnings=["Normalized alias to canonical service name"],
    )

    output = OrchestratorOutput(
        status=WorkflowStatus.SUCCESS,
        workflow_metadata=metadata,
        architecture_validation_warnings=["Normalized alias to canonical service name"],
    )

    assert output.workflow_metadata.architecture_validation_warnings == [
        "Normalized alias to canonical service name"
    ]
    assert output.architecture_validation_warnings == [
        "Normalized alias to canonical service name"
    ]
