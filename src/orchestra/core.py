"""Provider orchestration with explicit, bounded failover."""
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from orchestra.providers.base import Provider, ProviderCallError, ProviderResult


@dataclass(frozen=True)
class TaskResult:
    request_id: str
    provider: str
    model: str
    text: str
    duration_ms: int
    input_chars: int
    output_chars: int
    attempts: int = 1


class AllProvidersFailed(RuntimeError):
    """Raised when every configured provider fails for a task."""


class Orchestrator:
    def __init__(self, provider: Provider | tuple[Provider, ...] | list[Provider]):
        providers = (provider,) if not isinstance(provider, (tuple, list)) else tuple(provider)
        if not providers:
            raise ValueError("at least one provider must be configured")
        self._providers = providers

    def run(self, prompt: str) -> TaskResult:
        request_id = str(uuid4())
        started = perf_counter()
        last_error: Exception | None = None
        for index, provider in enumerate(self._providers, start=1):
            try:
                result: ProviderResult = provider.generate(prompt)
                duration_ms = max(0, int((perf_counter() - started) * 1000))
                return TaskResult(
                    request_id=request_id,
                    provider=result.provider,
                    model=result.model,
                    text=result.text,
                    duration_ms=duration_ms,
                    input_chars=result.input_chars,
                    output_chars=result.output_chars,
                    attempts=index,
                )
            except (ProviderCallError, RuntimeError, TimeoutError, OSError) as exc:
                last_error = exc
        raise AllProvidersFailed("all configured providers failed") from last_error
