# AI ORCHESTRA

AI ORCHESTRA is a modular Python foundation for executing provider-backed tasks through a small HTTP API. The current implementation includes the Gemini adapter, a typed provider contract and deterministic provider registry, request metrics, bounded metadata-only audit events, and a per-process request budget.

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

## Verify locally without provider API calls

```bash
ruff check src tests
pytest
python -m build
```

The automated tests stub the provider SDK; they do not contact Gemini or spend API credits.

## Run the API

For local use, after configuring a valid API key and a model enabled for your account:

```bash
uvicorn orchestra.api:app --app-dir src --host 127.0.0.1 --port 8000
```

- `GET /health` reports application liveness and whether provider configuration was accepted. It does not test live Gemini connectivity.
- `POST /v1/tasks` with JSON `{"prompt":"Explain dependency injection briefly"}` makes one Gemini API request.
- `GET /metrics` returns process-local request counters and budget use.
- `GET /audit` returns bounded metadata-only audit events. Prompts, completions, and credentials are not recorded.
- Provider failures return a generic error and do not expose upstream exception details.

## Limits and safeguards

- `ORCHESTRA_MAX_INPUT_CHARS`: maximum prompt length (default 12000; allowed 1–100000).
- `ORCHESTRA_MAX_OUTPUT_TOKENS`: output token cap (default 1024; allowed 1–8192).
- `ORCHESTRA_MAX_REQUESTS`: maximum provider-call attempts per process (default 100; allowed 1–100000).
- `ORCHESTRA_AUDIT_CAPACITY`: retained audit events (default 1000; allowed 1–10000).
- The request budget and audit trail are process-local and reset on restart. They are not distributed rate limiting, persistent audit storage, or a monetary quota. Configure provider-side quotas and billing limits before live use.
- The API binds to loopback in the documented command. Do not expose it publicly without authentication, TLS, deployment hardening, and a shared rate limiter.
- No live provider call is performed by CI. The default model is not guaranteed to be available or eligible for free-tier use.

## Current scope

Implemented: typed provider contract and registry, Gemini adapter, single-call orchestrator, FastAPI endpoints, input and request limits, bounded metadata-only audit trail, basic request metrics, deterministic stub-based tests, and CI packaging checks.

Not yet implemented: additional live provider adapters, automatic provider routing, persistent audit storage, multi-agent workflows, production authentication, distributed quotas, or evidence of live Gemini connectivity. CI passing verifies only the checks executed by that run; it does not prove model availability, free-tier eligibility, production readiness, or performance gains.
