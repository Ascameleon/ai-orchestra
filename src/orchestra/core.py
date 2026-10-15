"""Provider orchestration with explicit, bounded failover."""
import logging
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from orchestra.agents import AgentRegistry
from orchestra.circuit import ProviderCircuitBreaker
from orchestra.memory import ProviderMemory
from orchestra.providers.base import Provider, ProviderCallError, ProviderResult
from orchestra.skills import SkillRegistry

logger = logging.getLogger(__name__)


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
        circuit_breaker: ProviderCircuitBreaker | None = None,
        circuit_failure_threshold: int = 3,
        circuit_reset_timeout_seconds: float = 30.0,
        agent_registry: AgentRegistry | None = None,
        skill_registry: SkillRegistry | None = None,
    ):
        providers = (provider,) if not isinstance(provider, (tuple, list)) else tuple(provider)
        if not providers:
            raise ValueError("at least one provider must be configured")
        provider_names = tuple(self._provider_name(item) for item in providers)
        if any(not name for name in provider_names):
            raise ValueError("provider names must not be empty")
        if len(set(provider_names)) != len(provider_names):
            raise ValueError("provider names must be unique after normalization")
        self._providers = providers
        self.memory = memory or ProviderMemory()
        self._task_routes = dict(routes)
        self.circuit_breaker = circuit_breaker or ProviderCircuitBreaker(
            failure_threshold=circuit_failure_threshold,
            reset_timeout_seconds=circuit_reset_timeout_seconds,
        )
        self.agent_registry = agent_registry or AgentRegistry()
        self.skill_registry = skill_registry or SkillRegistry(self.agent_registry)

    @staticmethod
    def _provider_name(provider: Provider) -> str:
        raw_name = getattr(provider, "name", None)
        if raw_name is None:
            raw_name = provider.__class__.__name__
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError("provider name must be a non-empty string")
        return raw_name.strip().lower()

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

    def _record_outcome(self, provider_name: str, *, succeeded: bool, duration_ms: int) -> None:
        """Record aggregate telemetry without changing task success or failover semantics."""
        try:
            self.memory.record(provider_name, succeeded=succeeded, duration_ms=duration_ms)
        except Exception as exc:  # noqa: BLE001 - telemetry must not alter task semantics
            logger.warning(
                "Provider outcome memory write failed for %s (%s)",
                provider_name,
                type(exc).__name__,
            )

    def run(
        self,
        prompt: str,
        preferred_provider: str | None = None,
        task_type: str = "general",
        before_attempt: Callable[[], object] | None = None,
    ) -> TaskResult:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if not isinstance(task_type, str) or task_type not in {
            "general", "code", "research", "writing", "analysis",
            "review", "planner", "reviewer", "writer",
        }:
            raise ValueError("unsupported task type")
        if preferred_provider is not None and (
            not isinstance(preferred_provider, str) or not preferred_provider.strip()
        ):
            raise ValueError("preferred_provider must be a non-empty string when provided")

        request_id = str(uuid4())
        started = perf_counter()
        providers = self._providers
        routed_provider = preferred_provider or self._task_routes.get(task_type)
        if routed_provider is not None:
            preferred = routed_provider.strip().lower()
            matches = [provider for provider in self._providers if self._provider_name(provider) == preferred]
            if not matches:
                raise UnknownProviderRequested(f"provider is not configured: {preferred}")
            providers = (matches[0], *(provider for provider in self._providers if provider is not matches[0]))
        last_error: Exception | None = None
        attempt_count = 0
        for provider in providers:
            provider_name = self._provider_name(provider)
            if not self.circuit_breaker.allow_request(provider_name):
                continue
            if before_attempt is not None:
                try:
                    before_attempt()
                except Exception:
                    self.circuit_breaker.abandon_request(provider_name)
                    raise
            attempt_count += 1
            provider_started = perf_counter()
            # _provider_name already falls back to the adapter class name when
            # no explicit name is declared, so always validate attribution against it.
            expected_provider = provider_name
            try:
                result = self._validate_result(
                    provider.generate(prompt), prompt, expected_provider=expected_provider
                )
            except Exception as exc:  # noqa: BLE001 - isolate failures at the provider boundary
                provider_duration = max(0, int((perf_counter() - provider_started) * 1000))
                self._record_outcome(provider_name, succeeded=False, duration_ms=provider_duration)
                self.circuit_breaker.record_failure(provider_name)
                last_error = exc
                continue

            provider_duration = max(0, int((perf_counter() - provider_started) * 1000))
            self._record_outcome(provider_name, succeeded=True, duration_ms=provider_duration)
            self.circuit_breaker.record_success(provider_name)
            duration_ms = max(0, int((perf_counter() - started) * 1000))
            return TaskResult(
                request_id=request_id,
                provider=result.provider,
                model=result.model,
                text=result.text,
                duration_ms=duration_ms,
                input_chars=result.input_chars,
                output_chars=result.output_chars,
                attempts=attempt_count,
            )
        raise AllProvidersFailed("all configured providers failed or are temporarily unavailable") from last_error
