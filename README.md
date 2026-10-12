# AI ORCHESTRA

A minimal, testable foundation for provider-based AI tasks. This branch intentionally makes one provider call per task; multi-agent workflows and automatic routing are deferred until benchmarks demonstrate value.

## Requirements

- Python 3.11 or 3.12
- A Gemini API key for live provider calls. A Gemini consumer subscription does not automatically include API quota.

## Local setup

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Set `GEMINI_API_KEY` in your shell or a local secret manager. Never commit credentials. The app does not automatically load a `.env` file.

## Verify locally (no paid API calls)

```bash
ruff check src tests
pytest
python -m build
```

The automated tests stub the provider SDK; they do not contact Gemini or spend API credits.

## Run the API

After configuring a valid API key and a model enabled for your account:

```bash
uvicorn orchestra.api:app --app-dir src --host 127.0.0.1 --port 8000
```

- `GET /health` is a liveness/configuration indicator, not a live Gemini connectivity check.
- `POST /v1/tasks` with JSON `{"prompt":"Explain dependency injection briefly"}` makes one Gemini API request.
- Provider failures are returned as a generic error; upstream exception details are not returned to clients.

## Security and cost boundaries

- Keep API keys in environment variables or a secret manager; never commit secrets or log prompts, responses, or credentials.
- This project does not configure billing, purchase credits, or enforce a monetary quota. Configure provider-side quotas and billing limits before any live use.
- No live provider call is performed by CI.
- The default model is not guaranteed to be available or eligible for free-tier use. Choose a model enabled for your account.

## Scope and verification

Implemented: provider contract, Gemini adapter, single-call orchestrator, FastAPI endpoints, deterministic stub-based tests, and CI packaging check.

CI passing proves only the checks shown in that run. It does not prove live Gemini authentication, model availability, free-tier eligibility, production hardening, multi-provider routing, persistent audit storage, or performance/quality gains. Live connectivity remains intentionally untested until explicitly authorized and configured.
