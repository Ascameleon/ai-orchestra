"""Opt-in, bounded multi-step workflows with no persisted task content."""
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from orchestra.core import Orchestrator


@dataclass(frozen=True)
class WorkflowResult:
    workflow_id: str
    provider: str
    model: str
    text: str
    duration_ms: int
    input_chars: int
    output_chars: int
    provider_calls: int


class ReviewWorkflow:
    """Three-step draft, critique, and revision workflow.

    The workflow returns only the final revision. Intermediate outputs stay in
    process memory for the duration of the call and are never added to audit logs.
    """

    def __init__(self, orchestrator: Orchestrator):
        self._orchestrator = orchestrator

    def run(
        self,
        prompt: str,
        preferred_provider: str | None = None,
        before_attempt: Callable[[], object] | None = None,
    ) -> WorkflowResult:
        started = perf_counter()
        draft = self._orchestrator.run(
            "Act as a precise planner. Create a concise, structured first draft for this task. "
            "Do not claim facts you cannot support.\n\nTASK:\n" + prompt,
            preferred_provider=preferred_provider,
            task_type="planner",
            before_attempt=before_attempt,
        )
        critique = self._orchestrator.run(
            "Act as an independent reviewer. Identify factual gaps, contradictions, unsafe "
            "assumptions, and missing requirements in the draft. Give actionable corrections. "
            "Do not rewrite the full answer.\n\nTASK:\n" + prompt + "\n\nDRAFT:\n" + draft.text,
            preferred_provider=preferred_provider,
            task_type="reviewer",
            before_attempt=before_attempt,
        )
        final = self._orchestrator.run(
            "Act as the final editor. Produce the best complete answer to the original task, "
            "applying the review corrections. Do not mention this workflow or expose internal "
            "review notes. If information is uncertain, state that clearly.\n\nTASK:\n"
            + prompt + "\n\nDRAFT:\n" + draft.text + "\n\nREVIEW CORRECTIONS:\n" + critique.text,
            preferred_provider=preferred_provider,
            task_type="writer",
            before_attempt=before_attempt,
        )
        return WorkflowResult(
            workflow_id=str(uuid4()),
            provider=final.provider,
            model=final.model,
            text=final.text,
            duration_ms=max(0, int((perf_counter() - started) * 1000)),
            input_chars=len(prompt),
            output_chars=len(final.text),
            provider_calls=draft.attempts + critique.attempts + final.attempts,
        )
