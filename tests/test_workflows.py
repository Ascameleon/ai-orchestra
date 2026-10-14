import pytest

from orchestra.core import Orchestrator
from orchestra.guardrails import BudgetExceeded, CostGuard
from orchestra.providers.base import ProviderResult
from orchestra.workflows import PlanExecuteWorkflow, ReviewWorkflow


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
    result = ReviewWorkflow(Orchestrator(provider), max_input_chars=400).run("task " * 50)

    assert result.text == "x" * 500
    assert len(provider.prompts) == 3
    assert all(len(prompt) <= 400 for prompt in provider.prompts)
    assert "truncated" in provider.prompts[1] or "truncated" in provider.prompts[2]


def test_review_workflow_rejects_nonpositive_input_limit():
    with pytest.raises(ValueError, match="max_input_chars"):
        ReviewWorkflow(Orchestrator(SequencedProvider()), max_input_chars=0)


class FourStageProvider:
    name = "four-stage"

    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> ProviderResult:
        self.prompts.append(prompt)
        answers = ("plan steps", "executed result", "fix missing test", "complete final deliverable")
        text = answers[len(self.prompts) - 1]
        return ProviderResult(self.name, "test-model", text, len(prompt), len(text))


def test_plan_execute_workflow_returns_only_final_synthesis():
    provider = FourStageProvider()
    result = PlanExecuteWorkflow(Orchestrator(provider)).run("Build a safe API", task_type="code")

    assert result.provider == "four-stage"
    assert result.text == "complete final deliverable"
    assert result.provider_calls == 4
    assert result.input_chars == len("Build a safe API")
    assert "plan steps" in provider.prompts[1]
    assert "executed result" in provider.prompts[2]
    assert "fix missing test" in provider.prompts[3]
    assert "REVIEW CORRECTIONS" in provider.prompts[3]


def test_plan_execute_workflow_routes_each_stage_by_role():
    class RoleProvider:
        def __init__(self, name, answer):
            self.name = name
            self.answer = answer
            self.calls = 0

        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            return ProviderResult(self.name, "test-model", self.answer, len(prompt), len(self.answer))

    planner = RoleProvider("planner", "plan")
    coder = RoleProvider("coder", "execution")
    reviewer = RoleProvider("reviewer", "corrections")
    writer = RoleProvider("writer", "final")
    orchestrator = Orchestrator(
        [planner, coder, reviewer, writer],
        routes=(("planner", "planner"), ("code", "coder"), ("reviewer", "reviewer"), ("writer", "writer")),
    )

    result = PlanExecuteWorkflow(orchestrator).run("Implement and test", task_type="code")

    assert result.provider == "writer"
    assert result.text == "final"
    assert result.provider_calls == 4
    assert (planner.calls, coder.calls, reviewer.calls, writer.calls) == (1, 1, 1, 1)


def test_plan_execute_workflow_returns_no_partial_result_when_budget_exhausts():
    provider = FourStageProvider()
    guard = CostGuard(3)

    with pytest.raises(BudgetExceeded):
        PlanExecuteWorkflow(Orchestrator(provider)).run("Implement safely", before_attempt=guard.reserve)

    assert len(provider.prompts) == 3
    assert guard.used == 3


def test_plan_execute_workflow_bounds_every_stage():
    provider = FourStageProvider()
    workflow = PlanExecuteWorkflow(Orchestrator(provider), max_input_chars=400)

    workflow.run("large task " * 100)

    assert len(provider.prompts) == 4
    assert all(len(prompt) <= 400 for prompt in provider.prompts)
