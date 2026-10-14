# Provider circuit breaker

AI ORCHESTRA now protects each configured provider with a thread-safe circuit breaker.

## Behavior

- **Closed:** requests are allowed and consecutive failures are counted.
- **Open:** after 3 consecutive failed or invalid provider attempts, that provider is skipped for 30 seconds while ordered failover tries the next configured provider.
- **Half-open:** after the cooldown, only one recovery probe may run at a time. Success closes the circuit and clears the failure count; failure reopens it for a fresh cooldown.
- A provider skipped because its circuit is open does not consume the request-call budget or increase the reported attempt count.
- If budget reservation fails before a half-open probe starts, the probe reservation is released without counting a provider failure.

## Configuration and limits

The default `Orchestrator` settings are `circuit_failure_threshold=3` and `circuit_reset_timeout_seconds=30`. Callers that construct an `Orchestrator` directly can override either value. Circuit state is process-local and resets on restart; it is not a distributed breaker or a substitute for provider-side quotas.

The circuit snapshot exposes only provider names, state, consecutive failure counts, and retry delay. It does not store prompts, completions, or credentials.

## Verification

The circuit tests use deterministic clocks and stub providers. They cover state transitions, a single half-open probe under concurrency, fallback and attempt accounting, budget rejection, invalid limits, and telemetry write failures. No live provider calls or paid API credits are required.
