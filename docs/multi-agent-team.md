# Multi-agent team setup

AI ORCHESTRA already implements a four-stage workflow:

1. **Planner** — requirements, assumptions and acceptance criteria.
2. **Executor** — performs the task using its selected task type.
3. **Independent reviewer** — checks omissions, contradictions, unsafe assumptions and test gaps.
4. **Final writer** — consolidates the deliverable and labels anything unverified.

Only the final deliverable is returned. Every provider attempt consumes the configured request budget. Prompts and completions are not written to the metadata-only audit log.

## Configure role routing

Copy `.env.team.example` to `.env`. The example routes planning/research to Gemini, code to OpenAI, and independent review/final writing to Anthropic. Grok is included as an optional failover provider.

**API use is not guaranteed to be free.** Consumer subscriptions do not necessarily include API credits. Check provider billing and free quotas before enabling live calls. For a zero-spend setup, do not add live keys or submit provider-backed tasks. CI tests use fakes and do not contact model APIs.

If a provider is not configured, remove it from `ORCHESTRA_PROVIDER_FALLBACKS` and change every task route targeting it. The app fails closed rather than pretending an unavailable provider is connected.

## Use the browser workbench

1. Start the API using the README instructions.
2. Open the workbench at the instance root URL.
3. Leave the **primary provider** selector blank so `ORCHESTRA_TASK_ROUTES` selects by role/task.
4. Leave **independent review provider** blank to use the `reviewer` route, or explicitly select another configured provider.
5. Select a task type (for example Code or Research) and submit.

Selecting an explicit primary provider overrides role routing for planning, execution and final writing. Leave it blank for role-based routing.

## Security and cost controls

- Store keys only in local environment variables or a secrets manager; never commit `.env`.
- Use a long random `ORCHESTRA_API_KEY` if the API is reachable beyond localhost.
- Bind to localhost for personal testing. Public exposure requires TLS, authentication and deployment hardening.
- Every model attempt consumes the request budget, including failover and all workflow stages.
- The request budget is a call-count limit, not a monetary spending cap. Set provider-side billing limits too.
- A successful workflow proves only that configured models returned text. It does not prove external code changes, deployments or tests were executed; those require connected execution tools and independent evidence.

## Integration boundary

This profile configures providers already supported by the repository: Gemini, OpenAI, Anthropic and xAI Grok. It does not create credentials, unlock subscription-only models or connect Manus automatically. Model identifiers must match models enabled for the user's API account.
