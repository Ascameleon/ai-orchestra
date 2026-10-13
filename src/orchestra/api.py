"""HTTP API with bounded requests, generic provider errors, and safe metrics."""
import os
from hmac import compare_digest
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from orchestra.config import load_settings
from orchestra.core import Orchestrator, UnknownProviderRequested
from orchestra.guardrails import AuditEvent, AuditTrail, BudgetExceeded, CostGuard
from orchestra.providers.base import ProviderConfigurationError
from orchestra.providers.factory import build_provider_registry


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000)
    provider: str | None = Field(default=None, min_length=1, max_length=40)


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
            orchestrator = Orchestrator(providers)
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
            budget.reserve()
        except BudgetExceeded:
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(status_code=429, detail="Process request budget exhausted") from None

        try:
            result = orchestrator.run(request.prompt, preferred_provider=request.provider)
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

    return app


app = create_app()
