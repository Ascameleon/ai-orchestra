# Deployment runbook

This repository provides a Docker Compose deployment baseline for a **single host**. It is not a managed cloud deployment and does not provide TLS, distributed quotas, multi-replica coordination, or live provider validation by itself.

## 1. Prepare secrets

1. Install Docker Engine and the Docker Compose plugin on the target host.
2. Copy `.env.production.example` to `.env.production`.
3. Replace `ORCHESTRA_API_KEY` with a unique, long random secret and set the API key for the selected provider.
4. Keep `.env.production` out of version control and restrict access to it. Do not paste secrets into issue reports or logs.

The API key protects task, workflow, metrics, audit, provider-health/circuit, and evidence/claim endpoints. The Compose port is bound to loopback by default. Do not expose the port directly to the public internet.

## 2. Build and start

From the repository root:

```bash
docker compose --env-file .env.production -f compose.production.yml config --quiet
docker compose --env-file .env.production -f compose.production.yml build --pull
docker compose --env-file .env.production -f compose.production.yml up -d
docker compose --env-file .env.production -f compose.production.yml ps
```

The configuration check validates Compose interpolation, not provider credentials. The readiness check confirms adapter configuration and construction, **not** that a remote provider accepts the key or model.

## 3. Verify local readiness and API-key enforcement

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/ready
curl --fail -H "X-API-Key: $ORCHESTRA_API_KEY" http://127.0.0.1:8000/providers/circuits
```

For the shell commands above, load `ORCHESTRA_API_KEY` into your shell securely before running them. Do not put a real secret directly in shell history.

Perform a live provider smoke test only after confirming the selected provider key, model access, quota, and expected small API cost. Example request:

```bash
curl --fail -H "X-API-Key: $ORCHESTRA_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Reply with exactly: ORCHESTRA_OK"}' \
  http://127.0.0.1:8000/v1/tasks
```

A successful `/health` or `/ready` response is not a substitute for this live test. Provider calls may incur charges.

## 4. Operations

```bash
docker compose --env-file .env.production -f compose.production.yml logs --tail=100 orchestra
docker compose --env-file .env.production -f compose.production.yml restart orchestra
docker compose --env-file .env.production -f compose.production.yml down
```

The named `orchestra-data` volume stores bounded audit metadata and provider outcome aggregates. Back it up according to your retention policy. It must not be assumed to contain prompts or completions.

## 5. Before public production traffic

- Terminate TLS at a maintained reverse proxy or managed ingress and configure authentication/rate limits there as appropriate.
- Keep API credentials in the host's secret manager or protected environment file; rotate them after suspected exposure.
- Add external monitoring, backups, log retention, and an alerting path.
- The request budget and circuit breaker are process-local; they are not global quotas across multiple replicas.
- Run the test suite and dependency audit on the exact commit being deployed.
- Run a controlled live smoke test with an explicitly budgeted provider key before accepting traffic.
