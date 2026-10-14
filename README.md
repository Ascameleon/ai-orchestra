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
- `GET /v1/agents` and `GET /v1/skills` list the built-in agent roles and validated skill catalog. A task may include either `"agent":"coder"` or `"skill":"audit_security"`; the registry adds role instructions and selects the corresponding task route. Both fields cannot be used together, unknown names are rejected, and the configured API key protects these endpoints when enabled.
- `GET /metrics` returns process-local request counters and budget use.
- `GET /audit` returns bounded metadata-only audit events. Prompts, completions, and credentials are not recorded. Set `ORCHESTRA_AUDIT_DB` to a local SQLite file to retain the bounded audit window across restarts; unset it to keep audit events in process memory.
- Audit writes are best-effort: if the audit store is unavailable, a completed provider result is still returned and only the exception type is logged. Check storage health separately; this avoids masking a completed (and potentially billable) provider call.
- `GET /providers/health` returns provider success/failure counts and accumulated latency; by default they are process-local. Set `ORCHESTRA_MEMORY_DB` to a local SQLite file to persist these aggregates across restarts. Only provider names, counts, and latency are stored—never prompts, completions, or credentials.
- `GET /providers/circuits` reports configured providers' circuit state (`closed`, `open`, or `half_open`) and cooldown remaining; it honors `ORCHESTRA_API_KEY` when configured.
- `orchestra.evidence.assess_evidence(...)` assesses caller-supplied evidence metadata for publication freshness, duplicate URLs, and declared source-group diversity without network access.
- `POST /v1/evidence/assess` exposes this assessment over HTTP. It accepts at most 100 evidence records, uses no provider calls, and honors `ORCHESTRA_API_KEY` when configured. `source_group` is caller-declared metadata, not independently verified.
- `POST /v1/evidence/fetch` fetches up to five user-supplied URLs from explicitly allowlisted public hosts and returns bounded visible-text snapshots with SHA-256 fingerprints. It is disabled by default; redirects, non-default ports, IP literals, private/reserved DNS answers, non-text responses, and oversized bodies are rejected. Fetching does not prove publisher authenticity or claim support and makes no model calls.
- `POST /v1/claims/verify-links` checks whether each claim references known evidence IDs, flags unlinked claims and unknown references, and returns `semantic_support_verified: false`. It does not determine whether the cited sources actually support or contradict a claim.
- `POST /v1/evidence/audit-quotes` checks whether caller-supplied quotations occur in caller-supplied source snapshots, normalizing whitespace and case, and returns SHA-256 fingerprints of the supplied text. It does not fetch websites or verify publisher authenticity or semantic support; combined text is capped at 250,000 characters.
- `POST /v1/claims/check-conflicts` flags potential conflicts only when caller-supplied assertions share the same normalized topic and have opposite explicit stances (`supports` / `opposes`). It is a deterministic review aid, not semantic contradiction detection or proof of source truth.
- `POST /v1/claims/check-numeric-consistency` compares caller-supplied structured numeric assertions and flags unequal values only when normalized metric, unit, and period match. It does not extract numbers from prose or decide which source is correct; formatting-equivalent values such as `100` and `100.0` are treated as equal.
- `POST /v1/conclusions/trace` maps each conclusion to known claim IDs and then to evidence IDs, reporting fully, partially, or untraceable conclusions. Optionally pass an `evidence_ids` registry to flag unknown evidence references; the response also identifies claims with no evidence citations. If the registry is omitted, evidence IDs cannot be checked for existence. Link presence does not prove that evidence supports a conclusion.
- `POST /v1/workflows/review` runs an opt-in three-stage draft → independent critique → final revision workflow. It returns only the final answer, not intermediate drafts or critique. Each provider attempt consumes the process call budget; if the budget runs out mid-workflow, no partial result is returned, although earlier provider calls may already have incurred charges.
- `POST /v1/workflows/plan-execute` runs an opt-in four-stage plan → execute → independent review → final synthesis workflow. The execution stage can use `task_type` routing; only the final deliverable is returned. Every provider attempt consumes the process call budget, and budget exhaustion returns no partial result.
- Provider adapters must return a non-empty `ProviderResult` with valid provider/model metadata and character counts matching the prompt and response. When an adapter declares a `name`, its result must identify that same provider. Invalid results and exceptions raised by an adapter count as failed attempts and trigger configured failover rather than being returned as success. Provider failures return a generic error and do not expose upstream exception details.

## Limits and safeguards

- `ORCHESTRA_PROVIDER`: primary provider (default `gemini`); supported values are `gemini`, `openai`, and `anthropic`.
- `ORCHESTRA_PROVIDER_FALLBACKS`: optional comma-separated ordered fallback providers, for example `openai,anthropic`. Each listed provider needs its own API key and optional SDK extra. The primary cannot be repeated; duplicates and unknown names are rejected. Each task tries providers in order and stops at the first success. OpenAI requires the optional `openai` dependency extra and `OPENAI_API_KEY`; Anthropic requires the optional `anthropic` extra and `ANTHROPIC_API_KEY`.
- `ORCHESTRA_TASK_ROUTES`: optional deterministic task routing, e.g. `code=openai,research=gemini,writing=anthropic`. Supported task types are `general`, `code`, `research`, `writing`, `analysis`, `review`, `planner`, `reviewer`, and `writer`; each target must already be configured as the primary or a fallback. A per-request `provider` overrides this policy.
- `ORCHESTRA_CIRCUIT_FAILURE_THRESHOLD`: consecutive provider failures before a circuit opens (default 3; allowed 1–20).
- `ORCHESTRA_CIRCUIT_RESET_SECONDS`: cooldown before one half-open probe (default 30; allowed 1–3600).
- `ORCHESTRA_EVIDENCE_ALLOWED_HOSTS`: comma-separated DNS hostnames allowed for evidence fetching. Exact hosts and their subdomains are accepted; IP literals and custom ports are not. Empty by default, which disables outbound evidence fetching.
- `OPENAI_MODEL`: OpenAI model name (default `gpt-4o-mini`).
- `ANTHROPIC_MODEL`: Anthropic model name (default `claude-3-5-haiku-latest`).
- `ORCHESTRA_MAX_INPUT_CHARS`: maximum prompt length (default 12000; allowed 1–100000).
- `ORCHESTRA_MAX_OUTPUT_TOKENS`: output token cap (default 1024; allowed 1–8192).
- `ORCHESTRA_MAX_REQUESTS`: maximum provider-call attempts per process, including fallbacks (default 100; allowed 1–100000).
- `ORCHESTRA_AUDIT_CAPACITY`: retained audit events (default 1000; allowed 1–10000).
- `ORCHESTRA_MEMORY_DB`: optional SQLite path for durable aggregate provider outcomes. Leave unset for process-local memory. For Docker Compose, use `/data/provider-memory.sqlite3`; `/data` is a named volume. The database stores provider names, counts, and latency only—never prompts, completions, or credentials.
- `ORCHESTRA_AUDIT_DB`: optional SQLite path for a bounded persistent audit window. For Docker Compose, use `/data/audit.sqlite3`. It stores timestamps, request IDs, provider/model names, character counts, duration, and outcome only; it never stores prompts, completions, or credentials. The audit retention capacity is controlled by `ORCHESTRA_AUDIT_CAPACITY`.
- Provider calls have a 30-second timeout; OpenAI and Anthropic SDK automatic retries are disabled to avoid hidden repeat charges. The request budget and circuit state are process-local and reset on restart. Audit events are process-local unless `ORCHESTRA_AUDIT_DB` is configured. These safeguards are not distributed rate limiting or a monetary quota. Configure provider-side quotas and billing limits before live use.
- Set `ORCHESTRA_API_KEY` to require the `X-API-Key` header on task, workflow, metrics, audit, provider-health, circuit-status, and evidence/claim endpoints. Compare keys securely; never commit the key. If unset, those endpoints are unauthenticated, so keep the server bound to loopback as shown. Do not expose it publicly without a configured key, TLS, deployment hardening, and a shared rate limiter.
- No live provider call is performed by CI. The default model is not guaranteed to be available or eligible for free-tier use.

## Container deployment

For a local, loopback-only deployment, create the environment file and set credentials before starting:

```bash
cp .env.example .env
# Edit .env and set the selected provider key and a long random ORCHESTRA_API_KEY.
# Optional persistence: set ORCHESTRA_MEMORY_DB=/data/provider-memory.sqlite3 and/or ORCHESTRA_AUDIT_DB=/data/audit.sqlite3 in .env.
docker compose up --build -d
docker compose ps
curl -H "X-API-Key: $ORCHESTRA_API_KEY" http://127.0.0.1:8000/ready
```

The Compose configuration binds only to `127.0.0.1`, runs as a non-root user, drops Linux capabilities, uses a read-only root filesystem, and has readiness/health checks. It mounts a named volume at `/data`; set `ORCHESTRA_MEMORY_DB=/data/provider-memory.sqlite3` to enable provider outcome persistence and/or `ORCHESTRA_AUDIT_DB=/data/audit.sqlite3` to enable bounded audit persistence across container restarts. Persistence is opt-in and never stores task text. Do not publish this port to the internet as-is; public deployment still requires TLS termination, managed secrets, shared rate limiting, and provider-side billing quotas. The Docker image build is validated in CI; no live model call is part of the build.

## Current scope

Implemented: typed provider contract and registry wired into startup, validated provider selection, task-aware routing, validated agent/skill registries with role-specific prompts, opt-in draft-review-revision and plan-execute-review-synthesis workflows, Gemini adapter, optional OpenAI adapter, ordered failover orchestrator with an exposed attempt count, configurable process-local provider circuit breakers with a single half-open probe, opt-in allowlisted public-URL evidence snapshots, FastAPI endpoints, input and request limits, bounded metadata-only audit trail with optional SQLite persistence, provider outcome memory with optional SQLite persistence, basic request metrics, deterministic stub-based tests, and CI packaging checks.

Not yet implemented: automatic evidence discovery, source-group verification, semantic contradiction detection, claim-to-source entailment checks, or evidence-backed responses from provider output; semantic/benchmark-driven provider routing, autonomous shell/tool execution, production identity management, distributed quotas, TLS/public ingress, or evidence of live provider connectivity. The evidence assessor is a metadata utility only and must not be treated as proof that a source is authentic or supports a claim. CI passing verifies only the checks executed by that run; it does not prove model availability, free-tier eligibility, production readiness, or performance gains.
