"""
Basic smoke tests for Co-Pilot SE agents.

These tests verify that core components can be imported and initialized.
"""

import pytest


def test_can_import_models():
    """Test that we can import Pydantic models."""
    from src.models.schemas import (
        CloudPlatform,
        IndustryVertical,
        WorkflowStatus,
        ErrorType,
        RequirementsInput,
    )
    
    assert CloudPlatform.AZURE == "azure"
    assert IndustryVertical.HEALTHCARE == "healthcare"


def test_requirements_input_validation():
    """Test RequirementsInput model validation."""
    from src.models.schemas import RequirementsInput
    
    # Valid input
    valid_input = RequirementsInput(
        user_input="Build an Azure web app",
        context=None
    )
    assert valid_input.user_input == "Build an Azure web app"
    
    # Minimum length input (10+ characters required)
    min_input = RequirementsInput(
        user_input="Build app on Azure",
        context=None
    )
    assert len(min_input.user_input) >= 10


def test_cloud_platform_enum():
    """Test CloudPlatform enum values."""
    from src.models.schemas import CloudPlatform
    
    assert CloudPlatform.AZURE.value == "azure"
    assert CloudPlatform.AWS.value == "aws"
    assert CloudPlatform.GCP.value == "gcp"
    assert CloudPlatform.ORACLE.value == "oracle"


def test_industry_vertical_enum():
    """Test IndustryVertical enum values."""
    from src.models.schemas import IndustryVertical
    
    assert IndustryVertical.HEALTHCARE.value == "healthcare"
    assert IndustryVertical.FINANCE.value == "finance"
    assert IndustryVertical.RETAIL.value == "retail"


def test_workflow_status_enum():
    """Test WorkflowStatus enum values."""
    from src.models.schemas import WorkflowStatus
    
    assert WorkflowStatus.SUCCESS.value == "success"
    assert WorkflowStatus.ERROR.value == "error"
    assert WorkflowStatus.IN_PROGRESS.value == "in_progress"
