"""HTTP API. Provider errors are returned generically without leaking secrets."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from orchestra.config import load_settings
from orchestra.core import Orchestrator
from orchestra.providers.gemini import GeminiProvider, ProviderConfigurationError


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)


class TaskResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    text: str
    duration_ms: int
    input_chars: int
    output_chars: int


def create_app(orchestrator: Orchestrator | None = None) -> FastAPI:
    app = FastAPI(title="AI ORCHESTRA", version="0.1.0")
    active_orchestrator = orchestrator
    configuration_error = False
    if active_orchestrator is None:
        try:
            active_orchestrator = Orchestrator(GeminiProvider(load_settings()))
        except ProviderConfigurationError:
            configuration_error = True

    @app.get("/health")
    def health() -> dict[str, str]:
        # Liveness only: this does not imply the external API is reachable.
        return {"status": "ok", "provider": "configured" if not configuration_error else "not_configured"}

    @app.post("/v1/tasks", response_model=TaskResponse)
    def run_task(request: TaskRequest) -> TaskResponse:
        if active_orchestrator is None:
            raise HTTPException(status_code=503, detail="Gemini provider is not configured")
        try:
            result = active_orchestrator.run(request.prompt)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            # Do not return vendor exception text, which can contain sensitive context.
            raise HTTPException(status_code=502, detail="Provider request failed") from exc
        return TaskResponse(**result.__dict__)

    return app


app = create_app()
