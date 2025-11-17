import pytest

from src.agents.architecture_agent import ArchitectureAgent, ServiceSelection
from src.models.schemas import (
    RequirementsOutput,
    TechnicalConstraints,
    NonFunctionalRequirements,
)


class _DummyChatAgent:
    async def run(self, *_args, **_kwargs):  # pragma: no cover - not used in tests
        raise NotImplementedError("Chat agent run should not be called during unit tests")


class _DummyAgentFrameworkClient:
    def __init__(self, *args, **kwargs):  # pragma: no cover - simple stub
        pass

    def create_agent(self, *args, **kwargs):
        return _DummyChatAgent()


@pytest.fixture
def architecture_agent(monkeypatch):
    """Return ArchitectureAgent with AgentFrameworkClient patched to a stub."""
    monkeypatch.setattr(
        "src.agents.architecture_agent.AgentFrameworkClient",
        _DummyAgentFrameworkClient,
    )
    return ArchitectureAgent()


def test_normalize_service_name_alias(architecture_agent):
    canonical, matched, note = architecture_agent._normalize_service_name("AAD")
    assert canonical == "Azure Active Directory (Entra ID)"
    assert matched is True
    assert note and "alias" in note.lower()


def test_enforce_allowed_services_filters_invalid_and_duplicates(architecture_agent):
    services = [
        ServiceSelection(
            category="compute",
            service_name="Azure functions",
            rationale="primary compute",
        ),
        ServiceSelection(
            category="database",
            service_name="Amazon RDS",
            rationale="non-azure service",
        ),
        ServiceSelection(
            category="compute",
            service_name="Azure Functions",
            rationale="duplicate entry",
        ),
    ]

    validated, warnings = architecture_agent._enforce_allowed_services(services)

    assert len(validated) == 1
    assert validated[0].service_name == "Azure Functions"
    assert any("Amazon RDS" in warning for warning in warnings)
    assert any("duplicate service 'Azure Functions'" in warning for warning in warnings)


def test_enforce_allowed_services_injects_foundational_when_empty(architecture_agent):
    services = [
        ServiceSelection(
            category="compute",
            service_name="AWS Lambda",
            rationale="non-azure placeholder",
        )
    ]

    validated, warnings = architecture_agent._enforce_allowed_services(services)

    service_names = {svc.service_name for svc in validated}
    assert {"Azure Key Vault", "Azure Monitor", "Azure Active Directory (Entra ID)"}.issubset(service_names)
    assert any("foundational" in warning for warning in warnings)


def test_select_ai_services_detects_openai_and_foundry(architecture_agent):
    requirements = RequirementsOutput(
        functional_requirements=[
            "Design an Azure OpenAI agent that summarizes uploaded PDFs",
        ],
        technical_constraints=TechnicalConstraints(
            preferred_technologies=["gpt-4o"],
        ),
    )
    requirements.source_user_input = "Need Azure OpenAI LLM-based summarization"

    services = architecture_agent._select_ai_services(requirements)
    service_names = {svc.service_name for svc in services}

    assert "Azure OpenAI Service" in service_names
    assert "Azure AI Foundry" in service_names


def test_select_ai_services_adds_document_intelligence_for_pdf(architecture_agent):
    requirements = RequirementsOutput(
        functional_requirements=["Summarize PDF and Word documents"],
    )

    services = architecture_agent._select_ai_services(requirements)
    service_names = {svc.service_name for svc in services}

    assert "Azure AI Document Intelligence" in service_names


def test_integration_services_include_apim_and_service_bus(architecture_agent):
    requirements = RequirementsOutput(
        functional_requirements=["Expose public APIs for partners with throttling"],
        implied_requirements=["Need asynchronous order processing over topics"],
    )

    services = architecture_agent._select_integration_services(requirements)
    service_names = {svc.service_name for svc in services}

    assert "Azure API Management" in service_names
    assert "Azure Service Bus" in service_names


def test_security_enhancements_added_for_sensitive_compliance(architecture_agent):
    requirements = RequirementsOutput(
        functional_requirements=["Store HIPAA data"],
        non_functional_requirements=NonFunctionalRequirements(
            compliance=["HIPAA"],
            security={"network_isolation": True, "private_admin_access": True},
        ),
    )

    services = architecture_agent._select_security_enhancements(requirements)
    service_names = {svc.service_name for svc in services}

    assert "Azure Firewall" in service_names
    assert "Azure Bastion" in service_names
    assert "Microsoft Defender for Cloud" in service_names


def test_resiliency_services_add_backup_and_site_recovery(architecture_agent):
    requirements = RequirementsOutput(
        functional_requirements=["Mission-critical workload"],
        non_functional_requirements=NonFunctionalRequirements(
            availability={"rpo_minutes": 5, "rto_minutes": 30}
        ),
    )

    services = architecture_agent._select_resiliency_services(requirements)
    service_names = {svc.service_name for svc in services}

    assert {"Azure Backup", "Azure Site Recovery"}.issubset(service_names)


def test_data_platform_services_detect_lakehouse_keywords(architecture_agent):
    requirements = RequirementsOutput(
        functional_requirements=[
            "Need data lake + lakehouse with ETL pipelines feeding a data warehouse",
        ],
        implied_requirements=["Establish enterprise data catalog for compliance"],
    )

    services = architecture_agent._select_data_platform_services(requirements)
    service_names = {svc.service_name for svc in services}

    assert {"Azure Data Factory", "Azure Synapse Analytics", "Microsoft Purview"}.issubset(service_names)


def test_streaming_services_cover_event_hubs_and_iot(architecture_agent):
    requirements = RequirementsOutput(
        functional_requirements=[
            "Process IoT device telemetry with kafka-like ingestion and stream analytics",
        ]
    )

    services = architecture_agent._select_streaming_services(requirements)
    service_names = {svc.service_name for svc in services}

    assert {"Azure Event Hubs", "Azure Stream Analytics", "Azure IoT Hub"}.issubset(service_names)


def test_search_services_detect_vector_search(architecture_agent):
    requirements = RequirementsOutput(
        functional_requirements=[
            "Provide semantic vector search over indexed documents to ground Azure OpenAI",
        ]
    )

    services = architecture_agent._select_search_services(requirements)
    service_names = {svc.service_name for svc in services}

    assert "Azure AI Search" in service_names


def test_management_services_include_app_configuration_policy_and_automation(architecture_agent):
    requirements = RequirementsOutput(
        functional_requirements=[
            "Enable feature flags and automated patching for regulated workloads",
        ],
        non_functional_requirements=NonFunctionalRequirements(
            compliance=["SOC2"],
            security={"patching": True},
        ),
    )

    services = architecture_agent._select_management_services(requirements)
    service_names = {svc.service_name for svc in services}

    assert {
        "Azure App Configuration",
        "Azure Policy",
        "Azure Automation",
    }.issubset(service_names)
