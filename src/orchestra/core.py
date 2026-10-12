"""Minimal orchestration: one selected provider, one call, measurable output."""
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from orchestra.providers.base import Provider, ProviderResult


@dataclass(frozen=True)
class TaskResult:
    request_id: str
    provider: str
    model: str
    text: str
    duration_ms: int
    input_chars: int
    output_chars: int


class Orchestrator:
    def __init__(self, provider: Provider):
        self._provider = provider

    def run(self, prompt: str) -> TaskResult:
        request_id = str(uuid4())
        started = perf_counter()
        result: ProviderResult = self._provider.generate(prompt)
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return TaskResult(
            request_id=request_id,
            provider=result.provider,
            model=result.model,
            text=result.text,
            duration_ms=duration_ms,
            input_chars=result.input_chars,
            output_chars=result.output_chars,
        )
