"""HTTP API with bounded requests, generic provider errors, and safe metrics."""
import logging
import os
from datetime import datetime, timedelta
from hmac import compare_digest
from threading import Lock
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from orchestra.claims import ClaimRecord, assess_claim_links
from orchestra.config import load_settings
from orchestra.core import Orchestrator
from orchestra.evidence import EvidenceRecord, assess_evidence
from orchestra.evidence_fetcher import (
    EvidenceFetcher,
    EvidenceFetchingDisabled,
    EvidenceFetchRequestError,
    EvidenceFetchUnavailable,
)
from orchestra.guardrails import (
    AuditEvent,
    AuditTrail,
    BudgetExceeded,
    CostGuard,
    RedisDailyCostGuard,
    SQLiteAuditTrail,
    SQLiteDailyCostGuard,
)
from orchestra.memory import SQLiteProviderMemory
from orchestra.numeric_consistency import NumericAssertion, screen_numeric_consistency
from orchestra.providers.base import ProviderConfigurationError
from orchestra.providers.factory import build_provider_registry
from orchestra.quotes import QuoteReference, SourceSnapshot, audit_quotes
from orchestra.semantic_support import (
    ClaimForAssessment,
    SourceForAssessment,
    build_assessment_prompt,
    parse_assessment_response,
)
from orchestra.traceability import (
    ClaimTrace,
    SourceAssertion,
    screen_potential_conflicts,
    trace_conclusions,
)
from orchestra.workflows import PlanExecuteWorkflow, ReviewWorkflow, WorkflowInputTooLong

logger = logging.getLogger(__name__)


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000)
    provider: str | None = Field(default=None, min_length=1, max_length=40)
    task_type: Literal["general", "code", "research", "writing", "analysis", "review", "planner", "reviewer", "writer"] = "general"


class WorkflowRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000)
    provider: str | None = Field(default=None, min_length=1, max_length=40)


class PlanExecuteRequest(WorkflowRequest):
    task_type: Literal["general", "code", "research", "writing", "analysis", "review", "planner", "reviewer", "writer"] = "general"
    review_provider: str | None = Field(default=None, min_length=1, max_length=40)


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


class EvidenceFetchRequest(BaseModel):
    urls: list[Annotated[str, Field(min_length=1, max_length=2048)]] = Field(min_length=1, max_length=5)


class ClaimItemRequest(BaseModel):
    claim_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=10000)
    evidence_ids: list[Annotated[str, Field(min_length=1, max_length=128)]] = Field(default_factory=list, max_length=100)


class ClaimLinkAssessmentRequest(BaseModel):
    evidence_ids: list[Annotated[str, Field(min_length=1, max_length=128)]] = Field(max_length=100)
    claims: list[ClaimItemRequest] = Field(max_length=100)


class SemanticSourceSnapshotRequest(BaseModel):
    evidence_id: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1, max_length=20000)


class SemanticClaimRequest(BaseModel):
    claim_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=4000)
    evidence_ids: list[Annotated[str, Field(min_length=1, max_length=128)]] = Field(min_length=1, max_length=10)


class SemanticSupportRequest(BaseModel):
    sources: list[SemanticSourceSnapshotRequest] = Field(min_length=1, max_length=10)
    claims: list[SemanticClaimRequest] = Field(min_length=1, max_length=10)


class SourceSnapshotRequest(BaseModel):
    evidence_id: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1, max_length=20000)


class QuoteReferenceRequest(BaseModel):
    claim_id: str = Field(min_length=1, max_length=128)
    evidence_id: str = Field(min_length=1, max_length=128)
    quote: str = Field(min_length=1, max_length=2000)


class QuoteAuditRequest(BaseModel):
    snapshots: list[SourceSnapshotRequest] = Field(max_length=100)
    quotes: list[QuoteReferenceRequest] = Field(max_length=100)


class SourceAssertionRequest(BaseModel):
    assertion_id: str = Field(min_length=1, max_length=128)
    evidence_id: str = Field(min_length=1, max_length=128)
    topic: str = Field(min_length=1, max_length=500)
    stance: Literal["supports", "opposes", "neutral"]


class ConflictScreenRequest(BaseModel):
    assertions: list[SourceAssertionRequest] = Field(max_length=100)


class NumericAssertionRequest(BaseModel):
    assertion_id: str = Field(min_length=1, max_length=128)
    claim_id: str = Field(min_length=1, max_length=128)
    evidence_id: str = Field(min_length=1, max_length=128)
    metric: str = Field(min_length=1, max_length=500)
    value: str = Field(min_length=1, max_length=100)
    unit: str = Field(min_length=1, max_length=100)
    period: str = Field(min_length=1, max_length=200)


class NumericConsistencyRequest(BaseModel):
    assertions: list[NumericAssertionRequest] = Field(max_length=100)


class ConclusionItemRequest(BaseModel):
    conclusion_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=10000)
    claim_ids: list[Annotated[str, Field(min_length=1, max_length=128)]] = Field(default_factory=list, max_length=100)


class ConclusionTraceabilityRequest(BaseModel):
    claims: list[ClaimItemRequest] = Field(max_length=100)
    conclusions: list[ConclusionItemRequest] = Field(max_length=100)
    evidence_ids: list[Annotated[str, Field(min_length=1, max_length=128)]] | None = Field(default=None, max_length=100)


class WorkflowResponse(BaseModel):
    workflow_id: str
    provider: str
    review_provider: str
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


def create_app(
    orchestrator: Orchestrator | None = None,
    evidence_fetcher: EvidenceFetcher | None = None,
) -> FastAPI:
    app = FastAPI(title="AI ORCHESTRA", version="0.2.0")
    source_fetcher = evidence_fetcher or EvidenceFetcher.from_env()
    configuration_error = False
    config_error_message = "Provider is not configured"
    settings = None
    if orchestrator is None:
        try:
            settings = load_settings()
            registry = build_provider_registry(settings)
            providers = tuple(registry.get(name) for name in (settings.provider_name, *settings.provider_fallbacks))
            memory = SQLiteProviderMemory(settings.memory_db_path) if settings.memory_db_path else None
            orchestrator = Orchestrator(
                providers,
                memory=memory,
                routes=settings.task_routes,
                circuit_failure_threshold=settings.circuit_failure_threshold,
                circuit_reset_timeout_seconds=settings.circuit_reset_seconds,
            )
        except (ProviderConfigurationError, ValueError):
            configuration_error = True
            orchestrator = None

    max_input = settings.max_input_chars if settings else 12000
    request_limit = settings.max_requests_per_process if settings else 100
    audit_capacity = settings.audit_capacity if settings else 1000
    api_key = os.getenv("ORCHESTRA_API_KEY", "").strip() or None
    auth_required_value = os.getenv("ORCHESTRA_REQUIRE_API_KEY", "false").strip().lower()
    true_values = {"1", "true", "yes", "on"}
    false_values = {"", "0", "false", "no", "off"}
    require_api_key = auth_required_value in true_values
    auth_setting_invalid = auth_required_value not in true_values | false_values
    auth_configuration_error = auth_setting_invalid or (require_api_key and not api_key)
    redis_url = os.getenv("ORCHESTRA_REDIS_URL", "").strip() or None
    budget_db_path = os.getenv("ORCHESTRA_BUDGET_DB", "").strip() or None
    if redis_url:
        budget = RedisDailyCostGuard(redis_url, request_limit)
    elif budget_db_path:
        budget = SQLiteDailyCostGuard(budget_db_path, request_limit)
    else:
        budget = CostGuard(request_limit)
    audit_db_path = os.getenv("ORCHESTRA_AUDIT_DB", "").strip() or None
    audit = SQLiteAuditTrail(audit_db_path, audit_capacity) if audit_db_path else AuditTrail(audit_capacity)

    def record_audit(event: AuditEvent) -> None:
        """Best-effort telemetry must not hide a completed provider response."""
        try:
            audit.record(event)
        except Exception as exc:  # noqa: BLE001 - audit storage must not change task outcome
            logger.warning("Audit trail write failed (%s)", type(exc).__name__)

    def close_resources() -> None:
        """Release SQLite connections when the application shuts down."""
        provider_memory = getattr(orchestrator, "memory", None)
        try:
            if provider_memory is not None and callable(getattr(provider_memory, "close", None)):
                provider_memory.close()
        finally:
            try:
                if callable(getattr(budget, "close", None)):
                    budget.close()
            finally:
                if callable(getattr(audit, "close", None)):
                    audit.close()

    app.router.on_shutdown.append(close_resources)
    metrics = {"succeeded": 0, "failed": 0, "rejected": 0}
    metrics_lock = Lock()

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def workbench() -> HTMLResponse:
        """Serve a small, stateless browser interface for the complete goal workflow."""
        return HTMLResponse(r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark light"><title>AI ORCHESTRA — Workbench</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;color:#edf2f7;background:#0c111b}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 15% 0%,#182b42 0,transparent 42%),#0c111b}
main{width:min(920px,100%);margin:auto;padding:clamp(20px,5vw,54px) 18px 48px}
header{margin-bottom:28px}.eyebrow{font-size:.75rem;letter-spacing:.16em;text-transform:uppercase;color:#7dd3fc;font-weight:750}
h1{font-size:clamp(2rem,6vw,3.5rem);letter-spacing:-.045em;margin:.45rem 0}.sub{color:#aab8ca;line-height:1.6;max-width:680px}
.panel{background:#121b29;border:1px solid #2a394b;border-radius:18px;padding:clamp(16px,3vw,28px);box-shadow:0 18px 60px #0003}
label{display:block;font-size:.9rem;font-weight:650;margin:18px 0 8px}textarea,select,input{width:100%;background:#0c1420;color:#f4f7fb;border:1px solid #34465b;border-radius:10px;padding:12px 13px;font:inherit}
textarea{min-height:180px;resize:vertical;line-height:1.55}select,input{min-height:46px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
small,.hint{color:#9eafc2;line-height:1.55}.hint{font-size:.84rem;margin-top:8px}
button{margin-top:22px;width:100%;border:0;border-radius:10px;padding:14px 18px;background:#67e8f9;color:#08202b;font-weight:800;font-size:1rem;cursor:pointer}
button:disabled{opacity:.55;cursor:wait}#status{margin-top:18px;color:#a5f3fc;white-space:pre-wrap;overflow-wrap:anywhere}
#result{display:none;margin-top:18px;padding:20px;border:1px solid #34465b;border-radius:12px;background:#0a111b;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.65}
footer{margin-top:18px;color:#8799ae;font-size:.8rem;line-height:1.55}
@media(max-width:620px){.grid{grid-template-columns:1fr;gap:0}main{padding-top:28px}}
</style></head>
<body><main>
<header><div class="eyebrow">AI ORCHESTRA · OBJECTIF → LIVRABLE</div>
<h1>Transformez votre objectif en résultat.</h1>
<p class="sub">Décrivez ce que vous voulez accomplir. L’orchestrateur planifie, exécute, fait relire le résultat puis produit une livraison finale. Les étapes intermédiaires restent cachées.</p></header>
<section class="panel">
<form id="goal-form">
<label for="prompt">Votre objectif</label>
<textarea id="prompt" name="prompt" maxlength="100000" required placeholder="Ex. : Construis un outil qui compare des voyages, définit le MVP, crée le code, ajoute les tests et documente son lancement."></textarea>
<p class="hint">Soyez concret sur le résultat attendu, les contraintes, le budget et les critères de réussite. Ne collez pas de mots de passe ni de clés secrètes dans l’objectif.</p>
<div class="grid">
<div><label for="task_type">Type de travail</label><select id="task_type">
<option value="general">Choix automatique</option><option value="research">Recherche</option><option value="analysis">Analyse</option><option value="code">Développement / code</option><option value="writing">Rédaction</option><option value="review">Audit / vérification</option></select></div>
<div><label for="provider">Fournisseur principal (facultatif)</label><select id="provider"><option value="">Configuration par défaut</option><option value="gemini">Gemini</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option></select></div>
<div><label for="review_provider">Fournisseur de relecture indépendante</label><select id="review_provider"><option value="">Même politique que l’orchestration</option><option value="gemini">Gemini</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option></select></div>
</div>
<label for="api_key">Clé API de votre instance (si requise)</label><input id="api_key" type="password" autocomplete="off" placeholder="Utilisée pour cette requête uniquement">
<p class="hint">La clé n’est pas enregistrée dans le navigateur. Elle est envoyée uniquement à cette instance via l’en-tête X-API-Key. Les appels au fournisseur peuvent être payants selon votre compte et sa configuration.</p>
<button id="run" type="submit">Lancer l’orchestration complète</button>
</form><div id="status" role="status" aria-live="polite"></div><pre id="result"></pre>
</section><footer>Interface sans stockage local. Le résultat dépend des fournisseurs configurés, de leurs limites et des outils accessibles à cette instance. Les actions externes non exécutées ne sont pas présentées comme accomplies.</footer>
</main>
<script>
(function(){
const form=document.getElementById("goal-form"),button=document.getElementById("run"),status=document.getElementById("status"),result=document.getElementById("result");
form.addEventListener("submit",async function(event){
event.preventDefault();const prompt=document.getElementById("prompt").value.trim();if(!prompt)return;
button.disabled=true;status.textContent="Orchestration en cours. Les étapes sont exécutées et relues avant la synthèse finale…";result.style.display="none";result.textContent="";
const body={prompt:prompt,task_type:document.getElementById("task_type").value};const provider=document.getElementById("provider").value;if(provider)body.provider=provider;const reviewProvider=document.getElementById("review_provider").value;if(reviewProvider)body.review_provider=reviewProvider;
const headers={"Content-Type":"application/json"};const key=document.getElementById("api_key").value;if(key)headers["X-API-Key"]=key;
try{const response=await fetch("/v1/workflows/plan-execute",{method:"POST",headers:headers,body:JSON.stringify(body)});const data=await response.json();if(!response.ok)throw new Error(data.detail||("Erreur HTTP "+response.status));
result.textContent=data.text||"Aucun livrable n’a été retourné.";result.style.display="block";status.textContent="Terminé · résultat "+data.provider+" / "+data.model+" · relecture "+data.review_provider+" · "+data.provider_calls+" appels fournisseur · "+data.duration_ms+" ms.";
}catch(error){status.textContent="Échec : "+(error&&error.message?error.message:"requête impossible")+". Vérifiez la configuration du fournisseur, l’authentification et le budget. Aucun résultat partiel n’est affiché.";}
finally{button.disabled=false;}
});
})();
</script></body></html>""")

    @app.get("/health")
    def health() -> dict[str, str]:

        return {
            "status": "ok",
            "provider": "configured" if not configuration_error else "not_configured",
        }

    @app.get("/ready")
    def readiness() -> dict[str, str]:
        if auth_configuration_error:
            raise HTTPException(status_code=503, detail="API authentication is not configured safely")
        if orchestrator is None:
            raise HTTPException(status_code=503, detail=config_error_message)
        budget_check = getattr(budget, "check_ready", None)
        if callable(budget_check):
            try:
                budget_check()
            except Exception as exc:  # noqa: BLE001 - fail readiness if quota storage is unavailable
                logger.warning("Request budget backend unavailable (%s)", type(exc).__name__)
                raise HTTPException(status_code=503, detail="Request budget backend unavailable") from None
        return {"status": "ready", "provider": "configured"}

    def authorize(provided_key: str | None) -> None:
        if auth_configuration_error:
            raise HTTPException(status_code=503, detail="API authentication is not configured safely")
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

    @app.get("/providers/configuration")
    def get_provider_configuration(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict:
        """Report provider configuration without exposing credentials or making calls."""
        authorize(x_api_key)
        if orchestrator is None:
            raise HTTPException(status_code=503, detail=config_error_message)

        return {
            "primary": settings.provider_name if settings else None,
            "fallbacks": list(settings.provider_fallbacks) if settings else [],
            "configured_providers": list(orchestrator.provider_names),
            "credentials": {
                "gemini": bool(settings and settings.gemini_api_key),
                "openai": bool(settings and settings.openai_api_key),
                "anthropic": bool(settings and settings.anthropic_api_key),
                "grok": bool(settings and settings.grok_api_key),
            },
            "models": {
                "gemini": settings.gemini_model if settings else None,
                "openai": settings.openai_model if settings else None,
                "anthropic": settings.anthropic_model if settings else None,
                "grok": settings.grok_model if settings else None,
            },
            "live_check_performed": False,
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

    @app.get("/providers/circuits")
    def get_provider_circuits(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> list[dict[str, str | int]]:
        """Report circuit state without exposing request content."""
        authorize(x_api_key)
        if orchestrator is None:
            raise HTTPException(status_code=503, detail=config_error_message)
        return [
            status.__dict__
            for status in orchestrator.circuit_breaker.snapshot(orchestrator.provider_names)
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
        except WorkflowInputTooLong as exc:
            record_audit(
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
            raise HTTPException(status_code=413, detail=str(exc)) from None
        except BudgetExceeded:
            record_audit(
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
            record_audit(
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

        record_audit(
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
        except WorkflowInputTooLong as exc:
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(status_code=413, detail=str(exc)) from None
        except BudgetExceeded:
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(status_code=429, detail="Process provider-call budget exhausted") from None
        except Exception as exc:
            record_audit(
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

        record_audit(
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


    @app.post("/v1/workflows/plan-execute", response_model=WorkflowResponse)
    def run_plan_execute_workflow(
        request: PlanExecuteRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> WorkflowResponse:
        """Plan, execute, independently review, and return only the final synthesis."""
        authorize(x_api_key)
        if orchestrator is None:
            raise HTTPException(status_code=503, detail=config_error_message)
        if len(request.prompt) > max_input:
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(status_code=413, detail="Prompt exceeds configured input limit")
        if request.provider and request.provider.strip().lower() not in orchestrator.provider_names:
            raise HTTPException(status_code=400, detail="Requested provider is not configured")
        if request.review_provider and request.review_provider.strip().lower() not in orchestrator.provider_names:
            raise HTTPException(status_code=400, detail="Requested review provider is not configured")
        try:
            result = PlanExecuteWorkflow(orchestrator, max_input_chars=max_input).run(
                request.prompt,
                preferred_provider=request.provider,
                task_type=request.task_type,
                review_provider=request.review_provider,
                before_attempt=budget.reserve,
            )
        except WorkflowInputTooLong as exc:
            record_audit(
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
            raise HTTPException(status_code=413, detail=str(exc)) from None
        except BudgetExceeded:
            record_audit(
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
            record_audit(
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

        record_audit(
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

    @app.post("/v1/evidence/fetch")
    def fetch_evidence_endpoint(
        request: EvidenceFetchRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, object]:
        """Fetch bounded visible-text snapshots from explicitly allowlisted public hosts."""
        authorize(x_api_key)
        if not source_fetcher.enabled:
            raise HTTPException(
                status_code=503,
                detail="Evidence fetching is disabled; configure ORCHESTRA_EVIDENCE_ALLOWED_HOSTS",
            )
        try:
            sources = source_fetcher.fetch_many(request.urls)
        except EvidenceFetchRequestError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        except EvidenceFetchingDisabled:
            raise HTTPException(status_code=503, detail="Evidence fetching is disabled") from None
        except EvidenceFetchUnavailable:
            raise HTTPException(
                status_code=502,
                detail="One or more sources could not be fetched safely; no partial result returned",
            ) from None
        return {
            "sources": [source.__dict__ for source in sources],
            "source_authenticity_verified": False,
            "semantic_support_verified": False,
        }

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



    @app.post("/v1/claims/assess-support")
    def assess_claim_support(
        request: SemanticSupportRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, object]:
        """Use one explicitly requested provider call to review claims against supplied snapshots."""
        authorize(x_api_key)
        if orchestrator is None:
            raise HTTPException(status_code=503, detail=config_error_message)

        source_ids = [source.evidence_id.strip() for source in request.sources]
        if any(not source_id for source_id in source_ids) or len(set(source_ids)) != len(source_ids):
            raise HTTPException(status_code=422, detail="Source evidence IDs must be non-empty and unique")
        claim_ids = [claim.claim_id.strip() for claim in request.claims]
        if any(not claim_id for claim_id in claim_ids) or len(set(claim_ids)) != len(claim_ids):
            raise HTTPException(status_code=422, detail="Claim IDs must be non-empty and unique")
        known_sources = set(source_ids)
        for claim in request.claims:
            if any(not evidence_id.strip() for evidence_id in claim.evidence_ids):
                raise HTTPException(status_code=422, detail="Claim evidence references must not be empty")
            normalized_references = tuple(evidence_id.strip() for evidence_id in claim.evidence_ids)
            if len(set(normalized_references)) != len(normalized_references):
                raise HTTPException(status_code=422, detail="Claim evidence references must be unique")
            if any(evidence_id not in known_sources for evidence_id in normalized_references):
                raise HTTPException(status_code=422, detail="Claim references an unknown source snapshot")

        claims = tuple(
            ClaimForAssessment(
                item.claim_id.strip(),
                item.text,
                tuple(evidence_id.strip() for evidence_id in item.evidence_ids),
            )
            for item in request.claims
        )
        sources = tuple(
            SourceForAssessment(item.evidence_id.strip(), item.content)
            for item in request.sources
        )
        prompt = build_assessment_prompt(claims, sources)
        if len(prompt) > max_input:
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(
                status_code=413,
                detail="Combined claim and source prompt exceeds configured input limit",
            )
        try:
            result = orchestrator.run(prompt, before_attempt=budget.reserve)
            assessments = parse_assessment_response(result.text, claims)
        except BudgetExceeded:
            with metrics_lock:
                metrics["rejected"] += 1
            raise HTTPException(status_code=429, detail="Process provider-call budget exhausted") from None
        except Exception as exc:  # noqa: BLE001 - provider output parsing is an untrusted boundary
            with metrics_lock:
                metrics["failed"] += 1
            logger.warning("Semantic claim assessment failed (%s)", type(exc).__name__)
            raise HTTPException(
                status_code=502,
                detail="Claim assessment failed; no partial result returned",
            ) from None

        record_audit(
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
        return {
            "assessment_type": "provider_assisted",
            "provider": result.provider,
            "model": result.model,
            "duration_ms": result.duration_ms,
            "provider_calls": result.attempts,
            "results": [
                {
                    "claim_id": item.claim_id,
                    "verdict": item.verdict,
                    "rationale": item.rationale,
                    "evidence_ids": list(item.evidence_ids),
                }
                for item in assessments
            ],
            "semantic_support_assessed": True,
            "semantic_support_verified": False,
            "source_authenticity_verified": False,
            "source_truth_verified": False,
        }

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
                    evidence_ids=tuple(reference.strip() for reference in item.evidence_ids),
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


    @app.post("/v1/evidence/audit-quotes")
    def audit_evidence_quotes(
        request: QuoteAuditRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, object]:
        """Check literal quote presence in caller-supplied snapshots; never fetches URLs."""
        authorize(x_api_key)
        total_chars = sum(len(item.content) for item in request.snapshots) + sum(
            len(item.quote) for item in request.quotes
        )
        if total_chars > 250000:
            raise HTTPException(status_code=413, detail="Combined source and quote text exceeds 250000 characters")
        try:
            result = audit_quotes(
                [SourceSnapshot(item.evidence_id, item.content) for item in request.snapshots],
                [QuoteReference(item.claim_id, item.evidence_id, item.quote) for item in request.quotes],
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        return {
            "total_quotes": result.total_quotes,
            "quotes_found": result.quotes_found,
            "quotes_missing": result.quotes_missing,
            "unknown_evidence_references": result.unknown_evidence_references,
            "checks": [item.__dict__ for item in result.checks],
            "semantic_support_verified": False,
            "publisher_authenticity_verified": False,
        }

    @app.post("/v1/claims/check-conflicts")
    def check_claim_conflicts(
        request: ConflictScreenRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, object]:
        """Flag opposite explicit stances on the same supplied topic; not semantic proof."""
        authorize(x_api_key)
        try:
            result = screen_potential_conflicts(
                [
                    SourceAssertion(item.assertion_id, item.evidence_id, item.topic, item.stance)
                    for item in request.assertions
                ]
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        return {
            "assertions_checked": result.assertions_checked,
            "potential_conflict_count": len(result.potential_conflicts),
            "potential_conflicts": [item.__dict__ for item in result.potential_conflicts],
            "semantic_conflict_verified": False,
            "source_truth_verified": False,
        }

    @app.post("/v1/claims/check-numeric-consistency")
    def check_numeric_consistency(
        request: NumericConsistencyRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, object]:
        """Flag unequal supplied numeric values for the same metric, unit, and period."""
        authorize(x_api_key)
        try:
            result = screen_numeric_consistency(
                [NumericAssertion(**item.model_dump()) for item in request.assertions]
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        return {
            "assertions_checked": result.assertions_checked,
            "potential_disagreement_count": result.potential_disagreement_count,
            "potential_disagreements": [item.__dict__ for item in result.potential_disagreements],
            "source_truth_verified": False,
            "semantic_conflict_verified": False,
        }

    @app.post("/v1/conclusions/trace")
    def trace_conclusion_evidence(
        request: ConclusionTraceabilityRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, object]:
        """Resolve conclusion -> claim -> evidence links without judging truth or entailment."""
        authorize(x_api_key)
        try:
            result = trace_conclusions(
                [
                    (item.conclusion_id, item.text, tuple(item.claim_ids))
                    for item in request.conclusions
                ],
                [
                    ClaimTrace(item.claim_id, tuple(reference.strip() for reference in item.evidence_ids))
                    for item in request.claims
                ],
                known_evidence_ids=request.evidence_ids,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        return {
            "conclusions_checked": result.conclusions_checked,
            "fully_traceable": result.fully_traceable,
            "partially_traceable": result.partially_traceable,
            "untraceable": result.untraceable,
            "results": [item.__dict__ for item in result.results],
            "semantic_support_verified": False,
            "source_truth_verified": False,
        }

    return app


app = create_app()
