# AI ORCHESTRA

AI ORCHESTRA is a modular Python foundation for executing provider-backed tasks through a small HTTP API. The current implementation includes Gemini, optional OpenAI, and optional Anthropic adapters behind a typed provider contract and settings-driven registry, request metrics, bounded metadata-only audit events, and a per-process request budget.

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

Set `GEMINI_API_KEY` for Gemini; install `python -m pip install -e ".[openai]"` for OpenAI or `python -m pip install -e ".[anthropic]"` for Anthropic. Configure the matching provider key. Never commit credentials. The app does not automatically load a `.env` file.

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

- `GET /health` reports application liveness and whether provider configuration was accepted. It does not test live provider connectivity.
- `GET /ready` returns `200` only when provider configuration and adapter construction succeeded; otherwise it returns `503`.
- `POST /v1/tasks` with JSON `{"prompt":"Explain dependency injection briefly"}` makes one request to the configured primary provider. Add `"provider":"openai"` or `"provider":"anthropic"` to explicitly prefer a configured provider for that task; only providers configured in the process are accepted. If that preferred provider fails, configured fallbacks are tried in order.
- `GET /metrics` returns process-local request counters and budget use.
- `GET /audit` returns bounded metadata-only audit events. Prompts, completions, and credentials are not recorded.
- `GET /providers/health` returns process-local provider success/failure counts and accumulated latency; it never stores prompts or completions.
- Provider failures return a generic error and do not expose upstream exception details.

## Limits and safeguards

- `ORCHESTRA_PROVIDER`: primary provider (default `gemini`); supported values are `gemini`, `openai`, and `anthropic`.
- `ORCHESTRA_PROVIDER_FALLBACKS`: optional comma-separated ordered fallback providers, for example `openai,anthropic`. Each listed provider needs its own API key and optional SDK extra. The primary cannot be repeated; duplicates and unknown names are rejected. Each task tries providers in order and stops at the first success. OpenAI requires the optional `openai` dependency extra and `OPENAI_API_KEY`; Anthropic requires the optional `anthropic` extra and `ANTHROPIC_API_KEY`.
- `OPENAI_MODEL`: OpenAI model name (default `gpt-4o-mini`).
- `ANTHROPIC_MODEL`: Anthropic model name (default `claude-3-5-haiku-latest`).
- `ORCHESTRA_MAX_INPUT_CHARS`: maximum prompt length (default 12000; allowed 1–100000).
- `ORCHESTRA_MAX_OUTPUT_TOKENS`: output token cap (default 1024; allowed 1–8192).
- `ORCHESTRA_MAX_REQUESTS`: maximum provider-call attempts per process, including fallbacks (default 100; allowed 1–100000).
- `ORCHESTRA_AUDIT_CAPACITY`: retained audit events (default 1000; allowed 1–10000).
- Provider calls have a 30-second timeout; OpenAI and Anthropic SDK automatic retries are disabled to avoid hidden repeat charges. The request budget and audit trail are process-local and reset on restart. They are not distributed rate limiting, persistent audit storage, or a monetary quota. Configure provider-side quotas and billing limits before live use.
- Set `ORCHESTRA_API_KEY` to require the `X-API-Key` header on task, metrics, and audit endpoints. Compare keys securely; never commit the key. If unset, those endpoints are unauthenticated, so keep the server bound to loopback as shown. Do not expose it publicly without a configured key, TLS, deployment hardening, and a shared rate limiter.
- No live provider call is performed by CI. The default model is not guaranteed to be available or eligible for free-tier use.

## Current scope

Implemented: typed provider contract and registry wired into startup, validated provider selection, Gemini adapter, optional OpenAI adapter, ordered failover orchestrator with an exposed attempt count, FastAPI endpoints, input and request limits, bounded metadata-only audit trail, ephemeral provider outcome memory, basic request metrics, deterministic stub-based tests, and CI packaging checks.

Not yet implemented: task-aware automatic provider routing, persistent audit storage or cross-process memory, multi-agent workflows, production authentication, distributed quotas, or evidence of live provider connectivity. CI passing verifies only the checks executed by that run; it does not prove model availability, free-tier eligibility, production readiness, or performance gains.
