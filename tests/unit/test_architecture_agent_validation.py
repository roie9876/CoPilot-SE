import pytest

from src.agents.architecture_agent import ArchitectureAgent, ServiceSelection


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
