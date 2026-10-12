from orchestra.core import Orchestrator
from orchestra.providers.base import ProviderResult


class StubProvider:
    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult("stub", "test-model", f"answer:{prompt}", len(prompt), len(prompt) + 7)


def test_orchestrator_returns_result_and_metrics():
    result = Orchestrator(StubProvider()).run("hello")
    assert result.provider == "stub"
    assert result.model == "test-model"
    assert result.text == "answer:hello"
    assert result.input_chars == 5
    assert result.output_chars == len(result.text)
    assert result.duration_ms >= 0
    assert result.request_id


def test_each_task_gets_a_distinct_request_id():
    orchestrator = Orchestrator(StubProvider())
    assert orchestrator.run("a").request_id != orchestrator.run("b").request_id
