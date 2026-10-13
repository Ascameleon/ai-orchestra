from fastapi.testclient import TestClient

from orchestra.api import create_app
from orchestra.core import Orchestrator
from orchestra.providers.base import ProviderCallError, ProviderResult


class StubProvider:
    name = "stub"

    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult("stub", "test-model", "safe test response", len(prompt), 18)


class FailingProvider:
    name = "failing"

    def generate(self, prompt: str) -> ProviderResult:
        raise ProviderCallError("sensitive upstream detail")


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
    assert second.json() == {"detail": "Process provider-call budget exhausted"}
    assert client.get("/metrics").json()["rejected"] == 1
    rejected_audit = client.get("/audit").json()[-1]
    assert rejected_audit["outcome"] == "rejected"
    assert rejected_audit["input_chars"] == len("second")
    assert "second" not in client.get("/audit").text


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
    class FailOnceThenSucceed:
        def __init__(self):
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            if self.calls == 1:
                raise ProviderCallError("primary unavailable")
            return ProviderResult("backup", "backup-model", "answer", len(prompt), 6)

    provider = FailOnceThenSucceed()
    client = TestClient(create_app(Orchestrator([provider, StubProvider()])))
    response = client.post("/v1/tasks", json={"prompt": "hello"})
    assert response.status_code == 200
    assert response.json()["provider"] == "stub"
    assert response.json()["attempts"] == 2


def test_provider_health_endpoint_reports_metadata_only(monkeypatch):
    client = TestClient(create_app(Orchestrator([FailingProvider(), StubProvider()])))
    response = client.post("/v1/tasks", json={"prompt": "private prompt"})
    assert response.status_code == 200
    health = client.get("/providers/health")
    assert health.status_code == 200
    records = {item["provider"]: item for item in health.json()}
    assert records["failing"]["failures"] == 1
    assert records["stub"]["successes"] == 1
    assert "private prompt" not in health.text
    assert "safe test response" not in health.text


def test_task_endpoint_allows_explicit_selection_of_configured_provider():
    class BackupProvider:
        name = "backup"

        def generate(self, prompt: str) -> ProviderResult:
            return ProviderResult("backup", "backup-model", "backup answer", len(prompt), 13)

    client = TestClient(create_app(Orchestrator([StubProvider(), BackupProvider()])))
    response = client.post("/v1/tasks", json={"prompt": "hello", "provider": "backup"})
    assert response.status_code == 200
    assert response.json()["provider"] == "backup"
    assert response.json()["text"] == "backup answer"
    assert response.json()["attempts"] == 1


def test_task_endpoint_rejects_unconfigured_provider_before_budget_reservation():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.post("/v1/tasks", json={"prompt": "hello", "provider": "missing"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Requested provider is not configured"}
    assert client.get("/metrics").json()["requests_used"] == 0


def test_provider_call_budget_counts_failover_attempts(monkeypatch):
    import orchestra.api as api_module

    real_guard = api_module.CostGuard

    class OneProviderCallGuard(real_guard):
        def __init__(self, max_requests):
            super().__init__(1)

    class BackupProvider:
        name = "backup"

        def __init__(self):
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return ProviderResult("backup", "test-model", "answer", len(prompt), 6)

    monkeypatch.setattr(api_module, "CostGuard", OneProviderCallGuard)
    backup = BackupProvider()
    client = TestClient(create_app(Orchestrator([FailingProvider(), backup])))
    response = client.post("/v1/tasks", json={"prompt": "hello"})
    assert response.status_code == 429
    assert response.json() == {"detail": "Process provider-call budget exhausted"}
    assert backup.calls == 0
    assert client.get("/metrics").json()["requests_used"] == 1


def test_review_workflow_endpoint_returns_final_revision_only():
    class WorkflowProvider:
        name = "workflow"

        def __init__(self):
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            text = ("draft", "review correction", "final revision")[self.calls - 1]
            return ProviderResult(self.name, "test-model", text, len(prompt), len(text))

    provider = WorkflowProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post("/v1/workflows/review", json={"prompt": "Write a plan"})
    assert response.status_code == 200
    assert response.json()["text"] == "final revision"
    assert response.json()["provider_calls"] == 3
    assert provider.calls == 3
    audit = client.get("/audit").json()[0]
    assert audit["outcome"] == "success"
    assert audit["output_chars"] == len("final revision")


def test_task_endpoint_applies_configured_task_route():
    primary = StubProvider()

    class BackupProvider:
        name = "backup"

        def generate(self, prompt: str) -> ProviderResult:
            return ProviderResult("backup", "backup-model", "routed answer", len(prompt), 13)

    client = TestClient(create_app(Orchestrator([primary, BackupProvider()], routes=(("code", "backup"),))))
    response = client.post("/v1/tasks", json={"prompt": "write a function", "task_type": "code"})
    assert response.status_code == 200
    assert response.json()["provider"] == "backup"
    assert response.json()["text"] == "routed answer"


def test_review_workflow_failure_never_returns_intermediate_drafts():
    from orchestra.providers.base import ProviderCallError

    class FailsOnFinalStep:
        name = "workflow"

        def __init__(self):
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            if self.calls == 3:
                raise ProviderCallError("hidden final-stage failure")
            text = ("private draft", "private critique")[self.calls - 1]
            return ProviderResult(self.name, "test-model", text, len(prompt), len(text))

    provider = FailsOnFinalStep()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post("/v1/workflows/review", json={"prompt": "private task"})
    assert response.status_code == 502
    assert response.json() == {"detail": "Workflow failed; no partial result returned"}
    assert "private draft" not in response.text
    assert "private critique" not in response.text
    assert provider.calls == 3


def test_api_key_protects_review_workflow(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_API_KEY", "workflow-secret")
    client = TestClient(create_app(Orchestrator(StubProvider())))
    denied = client.post("/v1/workflows/review", json={"prompt": "task"})
    assert denied.status_code == 401
    allowed = client.post(
        "/v1/workflows/review",
        json={"prompt": "task"},
        headers={"X-API-Key": "workflow-secret"},
    )
    assert allowed.status_code == 200


def test_evidence_assessment_endpoint_reports_freshness_and_source_diversity():
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    class CountingProvider(StubProvider):
        calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return super().generate(prompt)

    provider = CountingProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    payload = {
        "evidence": [
            {
                "evidence_id": "e1",
                "source_name": "Publisher One",
                "source_group": "publisher-one",
                "url": "https://one.example/report",
                "published_at": (now - timedelta(days=1)).isoformat(),
            },
            {
                "evidence_id": "e2",
                "source_name": "Publisher Two",
                "source_group": "publisher-two",
                "url": "https://two.example/report",
                "published_at": now.isoformat(),
            },
        ],
        "minimum_independent_sources": 2,
    }

    response = client.post("/v1/evidence/assess", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["total_records"] == 2
    assert body["fresh_records"] == 2
    assert body["fresh_independent_source_groups"] == ["publisher-one", "publisher-two"]
    assert body["has_enough_fresh_independent_sources"] is True
    assert provider.calls == 0
    assert client.get("/metrics").json()["requests_used"] == 0


def test_evidence_assessment_endpoint_rejects_invalid_urls_and_naive_timestamps():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    invalid_url = {
        "evidence": [
            {
                "evidence_id": "e1",
                "source_name": "Publisher One",
                "source_group": "publisher-one",
                "url": "javascript:alert(1)",
            }
        ]
    }
    response = client.post("/v1/evidence/assess", json=invalid_url)
    assert response.status_code == 422

    naive_date = {
        "evidence": [
            {
                "evidence_id": "e1",
                "source_name": "Publisher One",
                "source_group": "publisher-one",
                "url": "https://one.example/report",
                "published_at": "2026-10-12T10:00:00",
            }
        ]
    }
    response = client.post("/v1/evidence/assess", json=naive_date)
    assert response.status_code == 422
    assert "timezone-aware" in response.text


def test_evidence_assessment_endpoint_limits_payload_and_honors_api_key(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_API_KEY", "evidence-secret")
    client = TestClient(create_app(Orchestrator(StubProvider())))
    assert client.post("/v1/evidence/assess", json={"evidence": []}).status_code == 401
    headers = {"X-API-Key": "evidence-secret"}
    oversized = {"evidence": [{}] * 101}
    response = client.post("/v1/evidence/assess", json=oversized, headers=headers)
    assert response.status_code == 422



def test_claim_link_endpoint_flags_missing_and_unknown_evidence_without_provider_calls():
    class CountingProvider(StubProvider):
        calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return super().generate(prompt)

    provider = CountingProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post(
        "/v1/claims/verify-links",
        json={
            "evidence_ids": ["e1", "e2"],
            "claims": [
                {"claim_id": "c1", "text": "Cited claim", "evidence_ids": ["e1"]},
                {"claim_id": "c2", "text": "No citation", "evidence_ids": []},
                {"claim_id": "c3", "text": "Broken citation", "evidence_ids": ["unknown"]},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_claims"] == 3
    assert body["linked_claims"] == 1
    assert body["unlinked_claims"] == 2
    assert body["claims_with_unknown_references"] == 1
    assert body["semantic_support_verified"] is False
    assert body["results"][2]["unknown_evidence_ids"] == ["unknown"]
    assert provider.calls == 0
    assert client.get("/metrics").json()["requests_used"] == 0


def test_claim_link_endpoint_rejects_duplicate_evidence_ids():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.post(
        "/v1/claims/verify-links",
        json={"evidence_ids": ["e1", "e1"], "claims": []},
    )
    assert response.status_code == 422
