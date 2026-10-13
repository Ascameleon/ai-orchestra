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
    assert body["attempts"] == 1


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


def test_metrics_and_audit_expose_metadata_without_prompt_or_response():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    secret_prompt = "prompt-that-must-not-be-audited"
    response = client.post("/v1/tasks", json={"prompt": secret_prompt})
    assert response.status_code == 200
    metrics = client.get("/metrics").json()
    assert metrics["succeeded"] == 1
    assert metrics["requests_used"] == 1
    audit_response = client.get("/audit")
    assert audit_response.status_code == 200
    assert secret_prompt not in audit_response.text
    assert "safe test response" not in audit_response.text
    assert audit_response.json()[0]["outcome"] == "success"


def test_configured_api_key_protects_tasks_and_audit(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_API_KEY", "test-secret-key")
    client = TestClient(create_app(Orchestrator(StubProvider())))
    denied = client.post("/v1/tasks", json={"prompt": "hello"})
    assert denied.status_code == 401
    assert client.get("/audit").status_code == 401
    allowed = client.post(
        "/v1/tasks",
        json={"prompt": "hello"},
        headers={"X-API-Key": "test-secret-key"},
    )
    assert allowed.status_code == 200
    assert client.get("/audit", headers={"X-API-Key": "test-secret-key"}).status_code == 200


def test_failed_provider_request_is_audited_without_sensitive_details():
    client = TestClient(create_app(Orchestrator(FailingProvider())))
    secret_prompt = "sensitive-user-prompt"
    response = client.post("/v1/tasks", json={"prompt": secret_prompt})
    assert response.status_code == 502
    audit_response = client.get("/audit")
    assert secret_prompt not in audit_response.text
    event = audit_response.json()[0]
    assert event["outcome"] == "failure"
    assert event["input_chars"] == len(secret_prompt)
    assert event["output_chars"] == 0


def test_request_budget_returns_429_after_limit(monkeypatch):
    import orchestra.api as api_module

    real_guard = api_module.CostGuard

    class OneRequestGuard(real_guard):
        def __init__(self, max_requests):
            super().__init__(1)

    monkeypatch.setattr(api_module, "CostGuard", OneRequestGuard)
    client = TestClient(create_app(Orchestrator(StubProvider())))
    assert client.post("/v1/tasks", json={"prompt": "first"}).status_code == 200
    second = client.post("/v1/tasks", json={"prompt": "second"})
    assert second.status_code == 429
    assert second.json() == {"detail": "Process request budget exhausted"}
    assert client.get("/metrics").json()["rejected"] == 1


def test_configured_api_key_protects_metrics_too(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_API_KEY", "another-test-key")
    client = TestClient(create_app(Orchestrator(StubProvider())))
    assert client.get("/metrics").status_code == 401
    assert client.get("/audit").status_code == 401
    headers = {"X-API-Key": "another-test-key"}
    assert client.get("/metrics", headers=headers).status_code == 200
    assert client.get("/audit", headers=headers).status_code == 200


def test_readiness_distinguishes_missing_provider_configuration(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ORCHESTRA_PROVIDER_FALLBACKS", raising=False)
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "gemini")
    import orchestra.api as api_module

    app = api_module.create_app()
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 503


def test_readiness_reports_configured_injected_orchestrator():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_task_response_reports_fallback_attempt_count():
    from orchestra.core import AllProvidersFailed

    class FailOnceThenSucceed:
        def __init__(self):
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("primary unavailable")
            return ProviderResult("backup", "backup-model", "answer", len(prompt), 6)

    provider = FailOnceThenSucceed()
    client = TestClient(create_app(Orchestrator([provider, StubProvider()])))
    response = client.post("/v1/tasks", json={"prompt": "hello"})
    assert response.status_code == 200
    assert response.json()["attempts"] == 1
