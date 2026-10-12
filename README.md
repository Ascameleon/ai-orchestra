# AI ORCHESTRA

Minimal, testable foundation for provider-based AI tasks. The current implementation intentionally uses one provider call per task; multi-agent workflows and automatic routing are deferred until benchmarks demonstrate value.

## Requirements

- Python 3.11 or 3.12
- Gemini API key for live provider calls (API access and quotas are separate from a Gemini consumer subscription)

## Local setup

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\\Scripts\\Activate.ps1
python -m pip install -e ".[dev]"
```

Set `GEMINI_API_KEY` in your shell or a local secret manager. Do not commit credentials. The app does not automatically load a `.env` file.

## Run tests and lint

```bash
ruff check src tests
pytest
```

These tests use a stub provider and do not call an external API or spend credits.

## Run the API

Export `GEMINI_API_KEY` and optionally `GEMINI_MODEL`, then:

```bash
uvicorn orchestra.api:app --app-dir src --host 127.0.0.1 --port 8000
```

- `GET /health` is a liveness endpoint only; it does not verify Gemini connectivity.
- `POST /v1/tasks` with JSON `{"prompt":"Explain dependency injection briefly"}` performs one Gemini API call.

## Security and cost

- Keep API keys in environment variables or a secret manager.
- Never commit secrets or include them in logs.
- This project does not configure billing, purchase credits, or enforce a monetary quota. Use provider-side quotas/budget controls where available.
- The default model is not guaranteed to be available or eligible for free-tier use. Change it to a model enabled for your account.

## Current scope and verification status

Implemented in this branch: minimal provider contract, Gemini adapter, single-call orchestrator, FastAPI endpoints, stub-based tests, and CI workflow.

Not yet proven: successful CI run, live Gemini authentication/model availability, actual free-tier eligibility, production hardening, routing, persistent audit storage, and performance/quality gains. Those require execution and evidence.
