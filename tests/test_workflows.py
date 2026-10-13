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
    assert "review notes" in provider.prompts[2]


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
