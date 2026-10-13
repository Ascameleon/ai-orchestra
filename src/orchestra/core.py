"""Provider orchestration with explicit, bounded failover."""
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from orchestra.memory import ProviderMemory
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


class UnknownProviderRequested(ValueError):
    """Raised when a task explicitly requests an unconfigured provider."""


class AllProvidersFailed(RuntimeError):
    """Raised when every configured provider fails for a task."""


class Orchestrator:
    def __init__(
        self,
        provider: Provider | tuple[Provider, ...] | list[Provider],
        memory: ProviderMemory | None = None,
    ):
        providers = (provider,) if not isinstance(provider, (tuple, list)) else tuple(provider)
        if not providers:
            raise ValueError("at least one provider must be configured")
        self._providers = providers
        self.memory = memory or ProviderMemory()

    @staticmethod
    def _provider_name(provider: Provider) -> str:
        return str(getattr(provider, "name", provider.__class__.__name__)).strip().lower()

    @property
    def provider_names(self) -> tuple[str, ...]:
        return tuple(self._provider_name(provider) for provider in self._providers)

    def run(self, prompt: str, preferred_provider: str | None = None) -> TaskResult:
        request_id = str(uuid4())
        started = perf_counter()
        providers = self._providers
        if preferred_provider is not None:
            preferred = preferred_provider.strip().lower()
            matches = [provider for provider in self._providers if self._provider_name(provider) == preferred]
            if not matches:
                raise UnknownProviderRequested(f"provider is not configured: {preferred}")
            providers = (matches[0], *(provider for provider in self._providers if provider is not matches[0]))
        last_error: Exception | None = None
        for index, provider in enumerate(providers, start=1):
            provider_started = perf_counter()
            provider_name = getattr(provider, "name", provider.__class__.__name__).lower()
            try:
                result: ProviderResult = provider.generate(prompt)
                provider_duration = max(0, int((perf_counter() - provider_started) * 1000))
                self.memory.record(provider_name, succeeded=True, duration_ms=provider_duration)
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
            except (ProviderCallError, TimeoutError, OSError) as exc:
                provider_duration = max(0, int((perf_counter() - provider_started) * 1000))
                self.memory.record(provider_name, succeeded=False, duration_ms=provider_duration)
                last_error = exc
        raise AllProvidersFailed("all configured providers failed") from last_error
