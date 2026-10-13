import pytest

from orchestra.core import Orchestrator
from orchestra.guardrails import BudgetExceeded, CostGuard
from orchestra.providers.base import ProviderResult
from orchestra.workflows import ReviewWorkflow


class SequencedProvider:
    name = "sequence"

    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> ProviderResult:
        self.prompts.append(prompt)
        answers = ("initial draft", "fix the missing constraints", "complete revised answer")
        text = answers[len(self.prompts) - 1]
        return ProviderResult(self.name, "test-model", text, len(prompt), len(text))


def test_review_workflow_runs_draft_review_and_revision():
    provider = SequencedProvider()
    result = ReviewWorkflow(Orchestrator(provider)).run("Build a safe API")

    assert result.provider == "sequence"
    assert result.text == "complete revised answer"
    assert result.provider_calls == 3
    assert result.input_chars == len("Build a safe API")
    assert "initial draft" in provider.prompts[1]
    assert "fix the missing constraints" in provider.prompts[2]
    assert "REVIEW CORRECTIONS" in provider.prompts[2]


def test_review_workflow_stops_without_partial_result_when_budget_runs_out():
    provider = SequencedProvider()
    guard = CostGuard(2)

    with pytest.raises(BudgetExceeded):
        ReviewWorkflow(Orchestrator(provider)).run(
            "Build a safe API",
            before_attempt=guard.reserve,
        )

    assert len(provider.prompts) == 2
    assert guard.used == 2


def test_review_workflow_can_route_each_agent_to_a_different_provider():
    class RoleProvider:
        def __init__(self, name, answer):
            self.name = name
            self.answer = answer
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return ProviderResult(self.name, "test-model", self.answer, len(prompt), len(self.answer))

    planner = RoleProvider("planner", "draft")
    reviewer = RoleProvider("reviewer", "corrections")
    writer = RoleProvider("writer", "final answer")
    orchestrator = Orchestrator(
        [planner, reviewer, writer],
        routes=(("planner", "planner"), ("reviewer", "reviewer"), ("writer", "writer")),
    )
    result = ReviewWorkflow(orchestrator).run("task")

    assert result.provider == "writer"
    assert result.text == "final answer"
    assert result.provider_calls == 3
    assert (planner.calls, reviewer.calls, writer.calls) == (1, 1, 1)


def test_review_workflow_bounds_every_stage_even_with_large_outputs():
    class LargeOutputProvider:
        name = "large"

        def __init__(self):
            self.prompts = []
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.prompts.append(prompt)
            self.calls += 1
            text = "x" * 500
            return ProviderResult(self.name, "test-model", text, len(prompt), len(text))

    provider = LargeOutputProvider()
    result = ReviewWorkflow(Orchestrator(provider), max_input_chars=180).run("task " * 50)

    assert result.text == "x" * 500
    assert len(provider.prompts) == 3
    assert all(len(prompt) <= 180 for prompt in provider.prompts)
    assert "truncated" in provider.prompts[1] or "truncated" in provider.prompts[2]


def test_review_workflow_rejects_nonpositive_input_limit():
    with pytest.raises(ValueError, match="max_input_chars"):
        ReviewWorkflow(Orchestrator(SequencedProvider()), max_input_chars=0)
