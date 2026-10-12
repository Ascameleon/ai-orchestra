from fastapi.testclient import TestClient

from orchestra.api import create_app
from orchestra.core import Orchestrator
from orchestra.providers.base import ProviderResult


class StubProvider:
    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult("stub", "test-model", "safe test response", len(prompt), 18)


class FailingProvider:
    def generate(self, prompt: str) -> ProviderResult:
        raise RuntimeError("sensitive upstream detail")


class InvalidRequestProvider:
    def generate(self, prompt: str) -> ProviderResult:
        raise ValueError("sensitive request payload from SDK")


def test_health_is_liveness_only():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    assert client.get("/health").json()["status"] == "ok"


def test_task_endpoint_uses_provider():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.post("/v1/tasks", json={"prompt": "hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "safe test response"
    assert body["provider"] == "stub"


def test_task_endpoint_rejects_empty_prompt():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    assert client.post("/v1/tasks", json={"prompt": ""}).status_code == 422


def test_task_endpoint_does_not_leak_provider_exception():
    client = TestClient(create_app(Orchestrator(FailingProvider())))
    response = client.post("/v1/tasks", json={"prompt": "hello"})
    assert response.status_code == 502
    assert response.json() == {"detail": "Provider request failed"}
    assert "sensitive upstream detail" not in response.text


def test_task_endpoint_does_not_leak_provider_value_error():
    client = TestClient(create_app(Orchestrator(InvalidRequestProvider())))
    response = client.post("/v1/tasks", json={"prompt": "hello"})
    assert response.status_code == 502
    assert response.json() == {"detail": "Provider request failed"}
    assert "sensitive request payload" not in response.text
