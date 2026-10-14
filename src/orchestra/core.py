"""Provider orchestration with explicit, bounded failover."""
from collections.abc import Callable
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
        routes: tuple[tuple[str, str], ...] = (),
    ):
        providers = (provider,) if not isinstance(provider, (tuple, list)) else tuple(provider)
        if not providers:
            raise ValueError("at least one provider must be configured")
        self._providers = providers
        self.memory = memory or ProviderMemory()
        self._task_routes = dict(routes)

    @staticmethod
    def _provider_name(provider: Provider) -> str:
        return str(getattr(provider, "name", provider.__class__.__name__)).strip().lower()

    @property
    def provider_names(self) -> tuple[str, ...]:
        return tuple(self._provider_name(provider) for provider in self._providers)

    @staticmethod
    def _validate_result(
        result: object, prompt: str, expected_provider: str | None = None
    ) -> ProviderResult:
        """Reject malformed or misattributed adapter results before accepting success."""
        if not isinstance(result, ProviderResult):
            raise ProviderCallError("Provider returned an invalid result")
        if (
            not isinstance(result.provider, str)
            or not result.provider.strip()
            or (expected_provider is not None and result.provider.strip().lower() != expected_provider)
            or not isinstance(result.model, str)
            or not result.model.strip()
            or not isinstance(result.text, str)
            or not result.text.strip()
        ):
            raise ProviderCallError("Provider returned incomplete result metadata or empty text")
        if (
            type(result.input_chars) is not int
            or type(result.output_chars) is not int
            or result.input_chars != len(prompt)
            or result.output_chars != len(result.text)
        ):
            raise ProviderCallError("Provider returned inconsistent result metrics")
        return result

    def run(
        self,
        prompt: str,
        preferred_provider: str | None = None,
        task_type: str = "general",
        before_attempt: Callable[[], object] | None = None,
    ) -> TaskResult:
        request_id = str(uuid4())
        started = perf_counter()
        providers = self._providers
        if task_type not in {"general", "code", "research", "writing", "analysis", "review", "planner", "reviewer", "writer"}:
            raise ValueError("unsupported task type")
        routed_provider = preferred_provider or self._task_routes.get(task_type)
        if routed_provider is not None:
            preferred = routed_provider.strip().lower()
            matches = [provider for provider in self._providers if self._provider_name(provider) == preferred]
            if not matches:
                raise UnknownProviderRequested(f"provider is not configured: {preferred}")
            providers = (matches[0], *(provider for provider in self._providers if provider is not matches[0]))
        last_error: Exception | None = None
        for index, provider in enumerate(providers, start=1):
            if before_attempt is not None:
                before_attempt()
            provider_started = perf_counter()
            provider_name = self._provider_name(provider)
            expected_provider = (
                provider_name if isinstance(getattr(provider, "name", None), str) else None
            )
            try:
                result = self._validate_result(
                    provider.generate(prompt), prompt, expected_provider=expected_provider
                )
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
            except Exception as exc:  # noqa: BLE001 - isolate failures at the provider boundary
                provider_duration = max(0, int((perf_counter() - provider_started) * 1000))
                self.memory.record(provider_name, succeeded=False, duration_ms=provider_duration)
                last_error = exc
        raise AllProvidersFailed("all configured providers failed") from last_error
