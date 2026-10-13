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


def _compose_bounded_prompt(instruction: str, sections: tuple[tuple[str, str], ...], limit: int) -> str:
    """Compose a stage prompt within the provider's configured character limit.

    Keep the instruction and earlier sections first. If context must be shortened,
    truncate the last section(s), never exceed the provider adapter's input limit.
    """
    parts = [instruction]
    remaining = limit - len(instruction)
    if remaining <= 0:
        return instruction[:limit]
    for label, value in sections:
        header = f"\n\n{label}:\n"
        if remaining <= len(header):
            break
        parts.append(header)
        remaining -= len(header)
        if len(value) <= remaining:
            parts.append(value)
            remaining -= len(value)
            continue
        if remaining > 0:
            marker = "…[truncated]"
            if remaining > len(marker):
                parts.append(value[: remaining - len(marker)] + marker)
            else:
                parts.append(value[:remaining])
        break
    return "".join(parts)


class ReviewWorkflow:
    """Three-step draft, critique, and revision workflow.

    The workflow returns only the final revision. Intermediate outputs stay in
    process memory for the duration of the call and are never added to audit logs.
    """

    def __init__(self, orchestrator: Orchestrator, max_input_chars: int = 12000):
        if max_input_chars < 1:
            raise ValueError("max_input_chars must be greater than zero")
        self._orchestrator = orchestrator
        self._max_input_chars = max_input_chars

    def run(
        self,
        prompt: str,
        preferred_provider: str | None = None,
        before_attempt: Callable[[], object] | None = None,
    ) -> WorkflowResult:
        started = perf_counter()
        draft_instruction = (
            "Act as a precise planner. Create a concise, structured first draft for this task. "
            "Do not claim facts you cannot support."
        )
        draft_prompt = _compose_bounded_prompt(
            draft_instruction, (("TASK", prompt),), self._max_input_chars
        )
        draft = self._orchestrator.run(
            draft_prompt,
            preferred_provider=preferred_provider,
            task_type="planner",
            before_attempt=before_attempt,
        )
        review_instruction = (
            "Act as an independent reviewer. Identify factual gaps, contradictions, unsafe "
            "assumptions, and missing requirements in the draft. Give actionable corrections. "
            "Do not rewrite the full answer."
        )
        critique_prompt = _compose_bounded_prompt(
            review_instruction,
            (("TASK", prompt), ("DRAFT", draft.text)),
            self._max_input_chars,
        )
        critique = self._orchestrator.run(
            critique_prompt,
            preferred_provider=preferred_provider,
            task_type="reviewer",
            before_attempt=before_attempt,
        )
        final_instruction = (
            "Act as the final editor. Produce the best complete answer to the original task, "
            "applying the review corrections. Do not mention this workflow or expose internal "
            "review notes. If information is uncertain, state that clearly."
        )
        final_prompt = _compose_bounded_prompt(
            final_instruction,
            (("TASK", prompt), ("DRAFT", draft.text), ("REVIEW CORRECTIONS", critique.text)),
            self._max_input_chars,
        )
        final = self._orchestrator.run(
            final_prompt,
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
