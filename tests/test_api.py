import sqlite3

from fastapi.testclient import TestClient

from orchestra.api import create_app
from orchestra.core import Orchestrator
from orchestra.memory import SQLiteProviderMemory
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



def test_quote_audit_endpoint_checks_snapshot_without_provider_calls():
    class CountingProvider(StubProvider):
        calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return super().generate(prompt)

    provider = CountingProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post(
        "/v1/evidence/audit-quotes",
        json={
            "snapshots": [{"evidence_id": "e1", "content": "Official report states: growth reached 12 percent."}],
            "quotes": [
                {"claim_id": "c1", "evidence_id": "e1", "quote": "GROWTH reached 12   percent."},
                {"claim_id": "c2", "evidence_id": "e1", "quote": "growth reached 21 percent"},
                {"claim_id": "c3", "evidence_id": "missing", "quote": "any quote"},
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quotes_found"] == 1
    assert body["quotes_missing"] == 2
    assert body["unknown_evidence_references"] == 1
    assert body["checks"][0]["source_sha256"]
    assert body["semantic_support_verified"] is False
    assert body["publisher_authenticity_verified"] is False
    assert provider.calls == 0
    assert client.get("/metrics").json()["requests_used"] == 0


def test_quote_audit_endpoint_rejects_excessive_combined_text():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.post(
        "/v1/evidence/audit-quotes",
        json={
            "snapshots": [{"evidence_id": "e1", "content": "x" * 20000}] * 13,
            "quotes": [],
        },
    )
    assert response.status_code == 413


def test_conflict_screen_endpoint_reports_potential_conflicts_without_provider_calls():
    class CountingProvider(StubProvider):
        calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return super().generate(prompt)

    provider = CountingProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post(
        "/v1/claims/check-conflicts",
        json={
            "assertions": [
                {"assertion_id": "a1", "evidence_id": "e1", "topic": "inflation rate", "stance": "supports"},
                {"assertion_id": "a2", "evidence_id": "e2", "topic": " Inflation   Rate ", "stance": "opposes"},
                {"assertion_id": "a3", "evidence_id": "e3", "topic": "employment", "stance": "opposes"},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["potential_conflict_count"] == 1
    assert body["potential_conflicts"][0]["evidence_a"] == "e1"
    assert body["potential_conflicts"][0]["evidence_b"] == "e2"
    assert body["semantic_conflict_verified"] is False
    assert body["source_truth_verified"] is False
    assert provider.calls == 0
    assert client.get("/metrics").json()["requests_used"] == 0


def test_conclusion_trace_endpoint_maps_claims_to_evidence_and_reports_missing_links():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.post(
        "/v1/conclusions/trace",
        json={
            "claims": [
                {"claim_id": "c1", "text": "Claim one", "evidence_ids": ["e1", "e2"]},
                {"claim_id": "c2", "text": "Claim two", "evidence_ids": ["e2"]},
            ],
            "conclusions": [
                {"conclusion_id": "d1", "text": "Conclusion with references", "claim_ids": ["c1", "c2"]},
                {"conclusion_id": "d2", "text": "Conclusion with a gap", "claim_ids": ["c1", "unknown"]},
                {"conclusion_id": "d3", "text": "Conclusion without references", "claim_ids": []},
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["fully_traceable"] == 1
    assert body["partially_traceable"] == 1
    assert body["untraceable"] == 1
    assert body["results"][0]["evidence_ids"] == ["e1", "e2"]
    assert body["results"][1]["missing_claim_ids"] == ["unknown"]
    assert body["semantic_support_verified"] is False
    assert body["source_truth_verified"] is False
    assert client.get("/metrics").json()["requests_used"] == 0


def test_conflict_screen_endpoint_rejects_duplicate_assertion_ids():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.post(
        "/v1/claims/check-conflicts",
        json={
            "assertions": [
                {"assertion_id": "a1", "evidence_id": "e1", "topic": "topic", "stance": "supports"},
                {"assertion_id": "a1", "evidence_id": "e2", "topic": "topic", "stance": "opposes"},
            ]
        },
    )
    assert response.status_code == 422


def test_conclusion_trace_endpoint_flags_unknown_evidence_and_empty_claim_citations():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.post(
        "/v1/conclusions/trace",
        json={
            "evidence_ids": ["e1", "e2"],
            "claims": [
                {"claim_id": "c1", "text": "Known citation", "evidence_ids": ["e1", "missing-evidence"]},
                {"claim_id": "c2", "text": "No citation", "evidence_ids": []},
            ],
            "conclusions": [
                {"conclusion_id": "d1", "text": "Conclusion", "claim_ids": ["c1", "c2"]}
            ],
        },
    )
    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["traceability_status"] == "partially_traceable"
    assert item["unknown_evidence_ids"] == ["missing-evidence"]
    assert item["claims_without_evidence"] == ["c2"]
    assert response.json()["semantic_support_verified"] is False
    assert client.get("/metrics").json()["requests_used"] == 0


def test_conclusion_trace_endpoint_rejects_duplicate_evidence_registry_ids():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.post(
        "/v1/conclusions/trace",
        json={"evidence_ids": ["e1", "e1"], "claims": [], "conclusions": []},
    )
    assert response.status_code == 422


def test_numeric_consistency_endpoint_flags_disagreement_without_provider_calls():
    class CountingProvider(StubProvider):
        calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return super().generate(prompt)

    provider = CountingProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post(
        "/v1/claims/check-numeric-consistency",
        json={
            "assertions": [
                {"assertion_id": "a1", "claim_id": "c1", "evidence_id": "e1", "metric": "GDP growth", "value": "2.5", "unit": "%", "period": "2025"},
                {"assertion_id": "a2", "claim_id": "c2", "evidence_id": "e2", "metric": " gdp growth ", "value": "3", "unit": "%", "period": "2025"},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["potential_disagreement_count"] == 1
    assert body["potential_disagreements"][0]["value_a"] == "2.5"
    assert body["potential_disagreements"][0]["value_b"] == "3"
    assert body["source_truth_verified"] is False
    assert body["semantic_conflict_verified"] is False
    assert provider.calls == 0
    assert client.get("/metrics").json()["requests_used"] == 0


def test_numeric_consistency_endpoint_rejects_invalid_numbers():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.post(
        "/v1/claims/check-numeric-consistency",
        json={"assertions": [{"assertion_id": "a1", "claim_id": "c1", "evidence_id": "e1", "metric": "rate", "value": "NaN", "unit": "%", "period": "2025"}]},
    )
    assert response.status_code == 422


def test_plan_execute_workflow_endpoint_returns_final_synthesis_only():
    class FourStageProvider:
        name = "four-stage"

        def __init__(self):
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            text = ("plan", "execution draft", "review corrections", "final deliverable")[self.calls - 1]
            return ProviderResult(self.name, "test-model", text, len(prompt), len(text))

    provider = FourStageProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post(
        "/v1/workflows/plan-execute",
        json={"prompt": "Build and test an API", "task_type": "code"},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "final deliverable"
    assert response.json()["provider_calls"] == 4
    assert provider.calls == 4
    audit = client.get("/audit").json()[0]
    assert audit["outcome"] == "success"
    assert audit["output_chars"] == len("final deliverable")
    assert "execution draft" not in client.get("/audit").text


def test_plan_execute_endpoint_returns_no_partial_result_when_budget_exhausted(monkeypatch):
    import orchestra.api as api_module
    real_guard = api_module.CostGuard

    class ThreeCallGuard(real_guard):
        def __init__(self, max_requests):
            super().__init__(3)

    class FourStageProvider:
        name = "four-stage"

        def __init__(self):
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return ProviderResult(self.name, "test-model", f"stage {self.calls}", len(prompt), len(f"stage {self.calls}"))

    monkeypatch.setattr(api_module, "CostGuard", ThreeCallGuard)
    provider = FourStageProvider()
    client = TestClient(create_app(Orchestrator(provider)))

    response = client.post("/v1/workflows/plan-execute", json={"prompt": "do the work"})

    assert response.status_code == 429
    assert response.json() == {"detail": "Process provider-call budget exhausted"}
    assert provider.calls == 3
    assert client.get("/metrics").json()["rejected"] == 1
    assert client.get("/audit").json()[-1]["outcome"] == "rejected"


def test_application_shutdown_closes_persistent_provider_memory(tmp_path):
    memory = SQLiteProviderMemory(str(tmp_path / "provider-memory.sqlite3"))
    app = create_app(Orchestrator(StubProvider(), memory=memory))

    with TestClient(app):
        pass

    try:
        memory.snapshot()
    except sqlite3.ProgrammingError:
        pass
    else:
        raise AssertionError("provider memory connection should be closed on shutdown")


def test_api_can_restore_persistent_audit_events_after_app_recreation(monkeypatch, tmp_path):
    database = tmp_path / "api-audit.sqlite3"
    monkeypatch.setenv("ORCHESTRA_AUDIT_DB", str(database))
    first_client = TestClient(create_app(Orchestrator(StubProvider())))
    response = first_client.post("/v1/tasks", json={"prompt": "private prompt"})
    assert response.status_code == 200
    assert first_client.get("/audit").json()[0]["request_id"] == response.json()["request_id"]
    first_client.close()

    second_client = TestClient(create_app(Orchestrator(StubProvider())))
    events = second_client.get("/audit").json()
    assert len(events) == 1
    assert events[0]["provider"] == "stub"
    assert events[0]["outcome"] == "success"
    assert "private prompt" not in str(events)
    second_client.close()


def test_semantic_claim_support_assessment_uses_one_provider_call_and_limits_citations():
    import json

    class AssessmentProvider:
        name = "assessment"

        def __init__(self):
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            text = json.dumps({
                "results": [{
                    "claim_id": "c1",
                    "verdict": "supported",
                    "rationale": "The supplied snapshot directly states the claim.",
                    "evidence_ids": ["e1"],
                }]
            })
            return ProviderResult(self.name, "test-model", text, len(prompt), len(text))

    provider = AssessmentProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post(
        "/v1/claims/assess-support",
        json={
            "sources": [{"evidence_id": "e1", "content": "The report says the sky is blue."}],
            "claims": [{"claim_id": "c1", "text": "The sky is blue.", "evidence_ids": ["e1"]}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["verdict"] == "supported"
    assert body["results"][0]["evidence_ids"] == ["e1"]
    assert body["semantic_support_assessed"] is True
    assert body["semantic_support_verified"] is False
    assert body["source_authenticity_verified"] is False
    assert provider.calls == 1
    assert client.get("/metrics").json()["requests_used"] == 1
    assert "The sky is blue" not in client.get("/audit").text


def test_semantic_claim_support_rejects_unknown_source_without_provider_call():
    class CountingProvider(StubProvider):
        calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return super().generate(prompt)

    provider = CountingProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post(
        "/v1/claims/assess-support",
        json={
            "sources": [{"evidence_id": "e1", "content": "source text"}],
            "claims": [{"claim_id": "c1", "text": "claim text", "evidence_ids": ["unknown"]}],
        },
    )
    assert response.status_code == 422
    assert provider.calls == 0
    assert client.get("/metrics").json()["requests_used"] == 0


def test_semantic_claim_support_rejects_invalid_model_output_without_partial_result():
    class InvalidAssessmentProvider:
        name = "invalid-assessment"

        def generate(self, prompt: str) -> ProviderResult:
            text = '{"results":[{"claim_id":"c1","verdict":"supported","rationale":"yes","evidence_ids":["other"]}]}'
            return ProviderResult(self.name, "test-model", text, len(prompt), len(text))

    client = TestClient(create_app(Orchestrator(InvalidAssessmentProvider())))
    response = client.post(
        "/v1/claims/assess-support",
        json={
            "sources": [{"evidence_id": "e1", "content": "source text"}],
            "claims": [{"claim_id": "c1", "text": "claim text", "evidence_ids": ["e1"]}],
        },
    )
    assert response.status_code == 502
    assert response.json() == {"detail": "Claim assessment failed; no partial result returned"}
    assert "other" not in response.text


def test_semantic_claim_support_honors_api_key(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_API_KEY", "semantic-secret")
    client = TestClient(create_app(Orchestrator(StubProvider())))
    payload = {
        "sources": [{"evidence_id": "e1", "content": "source text"}],
        "claims": [{"claim_id": "c1", "text": "claim text", "evidence_ids": ["e1"]}],
    }
    assert client.post("/v1/claims/assess-support", json=payload).status_code == 401
    authorized = client.post(
        "/v1/claims/assess-support",
        json=payload,
        headers={"X-API-Key": "semantic-secret"},
    )
    assert authorized.status_code == 502  # StubProvider intentionally returns non-JSON.



def test_semantic_claim_support_rejects_oversized_prompt_without_provider_call():
    class CountingProvider(StubProvider):
        calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return super().generate(prompt)

    provider = CountingProvider()
    client = TestClient(create_app(Orchestrator(provider)))
    response = client.post(
        "/v1/claims/assess-support",
        json={
            "sources": [{"evidence_id": "e1", "content": "x" * 15000}],
            "claims": [{"claim_id": "c1", "text": "claim", "evidence_ids": ["e1"]}],
        },
    )
    assert response.status_code == 413
    assert provider.calls == 0
    assert client.get("/metrics").json()["requests_used"] == 0


def test_api_persists_daily_budget_across_app_restarts(monkeypatch, tmp_path):
    database = tmp_path / "request-budget.sqlite3"
    monkeypatch.setenv("ORCHESTRA_BUDGET_DB", str(database))

    with TestClient(create_app(Orchestrator(StubProvider()))) as first_client:
        response = first_client.post("/v1/tasks", json={"prompt": "first request"})
        assert response.status_code == 200
        assert first_client.get("/metrics").json()["requests_used"] == 1

    with TestClient(create_app(Orchestrator(StubProvider()))) as second_client:
        metrics = second_client.get("/metrics").json()
        assert metrics["requests_used"] == 1
        response = second_client.post("/v1/tasks", json={"prompt": "second request"})
        assert response.status_code == 200
        assert second_client.get("/metrics").json()["requests_used"] == 2
