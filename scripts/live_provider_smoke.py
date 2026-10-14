"""Explicit, one-call-per-provider live smoke test.

This script contacts configured provider APIs and may incur charges. It is never
run by default CI; invoke it only when live credentials and billing limits are ready.
"""
import json
import sys
from time import perf_counter

from orchestra.config import load_settings
from orchestra.core import Orchestrator
from orchestra.providers.factory import build_provider_registry


def main() -> int:
    settings = load_settings()
    registry = build_provider_registry(settings)
    names = (settings.provider_name, *settings.provider_fallbacks)
    prompt = "Reply with a short acknowledgement that AI ORCHESTRA live connectivity works."
    results = []
    failed = False

    for name in names:
        provider = registry.get(name)
        started = perf_counter()
        try:
            # Call the adapter directly: a failed provider must not trigger paid
            # failover calls to other providers during this diagnostic.
            result = provider.generate(prompt)
            Orchestrator._validate_result(result, prompt, expected_provider=name)
            results.append({
                "provider": name,
                "model": result.model,
                "status": "passed",
                "duration_ms": round((perf_counter() - started) * 1000),
                "output_chars": len(result.text),
            })
        except Exception as exc:  # noqa: BLE001 - report no prompts, outputs, keys or SDK messages
            failed = True
            results.append({
                "provider": name,
                "status": "failed",
                "error_type": type(exc).__name__,
            })

    print(json.dumps({"live_provider_smoke_test": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
