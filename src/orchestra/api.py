"""HTTP API with bounded requests, generic provider errors, and safe metrics."""
import os
from datetime import datetime, timedelta
from hmac import compare_digest
from threading import Lock
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from orchestra.claims import ClaimRecord, assess_claim_links
from orchestra.config import load_settings
from orchestra.core import Orchestrator
from orchestra.evidence import EvidenceRecord, assess_evidence
from orchestra.guardrails import AuditEvent, AuditTrail, BudgetExceeded, CostGuard
from orchestra.providers.base import ProviderConfigurationError
from orchestra.providers.factory import build_provider_registry
from orchestra.workflows import ReviewWorkflow


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000)
    provider: str | None = Field(default=None, min_length=1, max_length=40)
    task_type: Literal["general", "code", "research", "writing", "analysis", "review", "planner", "reviewer", "writer"] = "general"


class WorkflowRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000)
    provider: str | None = Field(default=None, min_length=1, max_length=40)


class EvidenceItemRequest(BaseModel):
    evidence_id: str = Field(min_length=1, max_length=128)
    source_name: str = Field(min_length=1, max_length=256)
    source_group: str = Field(min_length=1, max_length=128)
    url: str = Field(min_length=1, max_length=2048)
    published_at: datetime | None = None
    retrieved_at: datetime | None = None


class EvidenceAssessmentRequest(BaseModel):
    evidence: list[EvidenceItemRequest] = Field(max_length=100)
    max_age_days: int = Field(default=30, ge=0, le=3650)
    minimum_independent_sources: int = Field(default=2, ge=1, le=100)


class ClaimItemRequest(BaseModel):
    claim_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=10000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)


class ClaimLinkAssessmentRequest(BaseModel):
    evidence_ids: list[str] = Field(max_length=100)
    claims: list[ClaimItemRequest] = Field(max_length=100)


class WorkflowResponse(BaseModel):
    workflow_id: str
    provider: str
    model: str
    text: str
    duration_ms: int
    input_chars: int
    output_chars: int
    provider_calls: int


class TaskResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    text: str
    duration_ms: int
    input_chars: int
    output_chars: int
    attempts: int = 1


def create_app(orchestrator: Orchestrator | None = None) -> FastAPI:
    app = FastAPI(title="AI ORCHESTRA", version="0.2.0")
    configuration_error = False
    config_error_message = "Provider is not configured"
    settings = None
    if orchestrator is None:
        try:
            settings = load_settings()
            registry = build_provider_registry(settings)
            providers = tuple(registry.get(name) for name in (settings.provider_name, *settings.provider_fallbacks))
            orchestrator = Orchestrator(providers, routes=settings.task_routes)
        except (ProviderConfigurationError, ValueError):
            configuration_error = True
            orchestrator = None

    max_input = settings.max_input_chars if settings else 12000
    request_limit = settings.max_requests_per_process if settings else 100
    audit_capacity = settings.audit_capacity if settings else 1000
    api_key = os.getenv("ORCHESTRA_API_KEY", "").strip() or None
    budget = CostGuard(request_limit)
    audit = AuditTrail(audit_capacity)
    metrics = {"succeeded": 0, "failed": 0, "rejected": 0}
    metrics_lock = Lock()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "provider": "configured" if not configuration_error else "not_configured",
        }

    @app.get("/ready")
    def readiness() -> dict[str, str]:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail=config_error_message)
        return {"status": "ready", "provider": "configured"}

    def authorize(provided_key: str | None) -> None:
        if api_key and (not provided_key or not compare_digest(provided_key, api_key)):
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

    @app.get("/metrics")
    def get_metrics(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> dict[str, int]:
        authorize(x_api_key)
        with metrics_lock:
            return {
                **metrics,
                "requests_used": budget.used,
                "requests_limit": budget.limit,
                "audit_events": len(audit.snapshot()),
            }

    @app.get("/providers/health")
    def get_provider_health(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> list[dict[str, str | int]]:
        authorize(x_api_key)
        if orchestrator is None:
            raise HTTPException(status_code=503, detail=config_error_message)
        return [
            {
                "provider": outcome.provider,
                "successes": outcome.successes,
                "failures": outcome.failures,
                "total_duration_ms": outcome.total_duration_ms,
            }
            for outcome in orchestrator.memory.snapshot()
        ]

    @app.get("/audit")
    def get_audit(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> list[dict[str, str | int | float]]:
        authorize(x_api_key)
        # Metadata only; intentionally excludes prompts, output text and credentials.
        return [
            {
                "timestamp": event.timestamp,
                "request_id": event.request_id,
                "provider": event.provider,
                "model": event.model,
                "input_chars": event.input_chars,
                "output_chars": event.output_chars,
                "duration_ms": event.duration_ms,
                "outcome": event.outcome,
            }
            for event in audit.snapshot()
        ]

    @app.post("/v1/tasks", response_model=TaskResponse)
    def run_task(
        request: TaskRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> TaskResponse:
        authorize(x_api_key)
        if orchestrator is None:
            raise HTTPException(status_code=503, detail=config_error_message)
        if len(request.prompt) > max_input:
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(status_code=413, detail="Prompt exceeds configured input limit")
        if request.provider and request.provider.strip().lower() not in orchestrator.provider_names:
            raise HTTPException(status_code=400, detail="Requested provider is not configured")
        try:
            result = orchestrator.run(
                request.prompt,
                preferred_provider=request.provider,
                task_type=request.task_type,
                before_attempt=budget.reserve,
            )
        except BudgetExceeded:
            audit.record(
                AuditEvent(
                    timestamp=AuditTrail.now(),
                    request_id=str(uuid4()),
                    provider="unknown",
                    model="unknown",
                    input_chars=len(request.prompt),
                    output_chars=0,
                    duration_ms=0,
                    outcome="rejected",
                )
            )
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(status_code=429, detail="Process provider-call budget exhausted") from None
        except Exception as exc:
            audit.record(
                AuditEvent(
                    timestamp=AuditTrail.now(),
                    request_id=str(uuid4()),
                    provider="unknown",
                    model="unknown",
                    input_chars=len(request.prompt),
                    output_chars=0,
                    duration_ms=0,
                    outcome="failure",
                )
            )
            with metrics_lock:
                metrics["failed"] += 1
            raise HTTPException(status_code=502, detail="Provider request failed") from exc

        audit.record(
            AuditEvent(
                timestamp=AuditTrail.now(),
                request_id=result.request_id,
                provider=result.provider,
                model=result.model,
                input_chars=result.input_chars,
                output_chars=result.output_chars,
                duration_ms=result.duration_ms,
                outcome="success",
            )
        )
        with metrics_lock:
            metrics["succeeded"] += 1
        return TaskResponse(**result.__dict__)


    @app.post("/v1/workflows/review", response_model=WorkflowResponse)
    def run_review_workflow(
        request: WorkflowRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> WorkflowResponse:
        authorize(x_api_key)
        if orchestrator is None:
            raise HTTPException(status_code=503, detail=config_error_message)
        if len(request.prompt) > max_input:
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(status_code=413, detail="Prompt exceeds configured input limit")
        if request.provider and request.provider.strip().lower() not in orchestrator.provider_names:
            raise HTTPException(status_code=400, detail="Requested provider is not configured")
        try:
            result = ReviewWorkflow(orchestrator, max_input_chars=max_input).run(
                request.prompt,
                preferred_provider=request.provider,
                before_attempt=budget.reserve,
            )
        except BudgetExceeded:
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(status_code=429, detail="Process provider-call budget exhausted") from None
        except Exception as exc:
            audit.record(
                AuditEvent(
                    timestamp=AuditTrail.now(),
                    request_id=str(uuid4()),
                    provider="unknown",
                    model="unknown",
                    input_chars=len(request.prompt),
                    output_chars=0,
                    duration_ms=0,
                    outcome="failure",
                )
            )
            with metrics_lock:
                metrics["failed"] += 1
            raise HTTPException(status_code=502, detail="Workflow failed; no partial result returned") from exc

        audit.record(
            AuditEvent(
                timestamp=AuditTrail.now(),
                request_id=result.workflow_id,
                provider=result.provider,
                model=result.model,
                input_chars=result.input_chars,
                output_chars=result.output_chars,
                duration_ms=result.duration_ms,
                outcome="success",
            )
        )
        with metrics_lock:
            metrics["succeeded"] += 1
        return WorkflowResponse(**result.__dict__)

    @app.post("/v1/evidence/assess")
    def assess_evidence_endpoint(
        request: EvidenceAssessmentRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, object]:
        """Assess supplied evidence metadata; never fetches URLs or calls an LLM."""
        authorize(x_api_key)
        records = []
        try:
            for item in request.evidence:
                fields = {
                    "evidence_id": item.evidence_id,
                    "source_name": item.source_name,
                    "source_group": item.source_group,
                    "url": item.url,
                    "published_at": item.published_at,
                }
                if item.retrieved_at is not None:
                    fields["retrieved_at"] = item.retrieved_at
                records.append(EvidenceRecord(**fields))
            result = assess_evidence(
                records,
                max_age=timedelta(days=request.max_age_days),
                minimum_independent_sources=request.minimum_independent_sources,
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        return result.__dict__


    @app.post("/v1/claims/verify-links")
    def verify_claim_links(
        request: ClaimLinkAssessmentRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, object]:
        """Validate claim-to-evidence IDs only; no semantic or source verification."""
        authorize(x_api_key)
        evidence_ids = [item.strip() for item in request.evidence_ids]
        if any(not item for item in evidence_ids):
            raise HTTPException(status_code=422, detail="evidence_ids must not contain empty values")
        if len(set(evidence_ids)) != len(evidence_ids):
            raise HTTPException(status_code=422, detail="evidence_ids must be unique")
        try:
            claims = [
                ClaimRecord(
                    claim_id=item.claim_id,
                    text=item.text,
                    evidence_ids=tuple(item.evidence_ids),
                )
                for item in request.claims
            ]
            result = assess_claim_links(claims, set(evidence_ids))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        return {
            "total_claims": result.total_claims,
            "linked_claims": result.linked_claims,
            "unlinked_claims": result.unlinked_claims,
            "claims_with_unknown_references": result.claims_with_unknown_references,
            "results": [item.__dict__ for item in result.results],
            "semantic_support_verified": False,
        }

    return app


app = create_app()
