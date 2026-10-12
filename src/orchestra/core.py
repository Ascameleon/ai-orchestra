"""Minimal orchestration: one selected provider, one call, measurable output."""
from time import perf_counter
from uuid import uuid4

from orchestra.providers.base import Provider, ProviderResult


class TaskResult:
    def __init__(self, request_id: str, provider: str, model: str, text: str, duration_ms: int, input_chars: int, output_chars: int):
        self.request_id = request_id
        self.provider = provider
        self.model = model
        self.text = text
        self.duration_ms = duration_ms
        self.input_chars = input_chars
        self.output_chars = output_chars


class Orchestrator:
    def __init__(self, provider: Provider):
        self._provider = provider

    def run(self, prompt: str) -> TaskResult:
        request_id = str(uuid4())
        started = perf_counter()
        result: ProviderResult = self._provider.generate(prompt)
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return TaskResult(request_id, result.provider, result.model, result.text, duration_ms, result.input_chars, result.output_chars)
