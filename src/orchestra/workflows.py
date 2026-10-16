"""Opt-in, bounded multi-step workflows with no persisted task content."""
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from orchestra.core import Orchestrator


class WorkflowInputTooLong(ValueError):
    """Raised when the original task cannot fit without silently truncating it."""


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
        if prompt not in draft_prompt:
            raise WorkflowInputTooLong(
                "Original task exceeds the workflow input limit; shorten it or raise the configured limit"
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


class PlanExecuteWorkflow:
    """Four-step plan, execute, review, and final synthesis workflow.

    Only the final synthesis is returned. Every stage is bounded, routes by its
    role unless a caller explicitly prefers one configured provider, and charges
    each provider attempt to the caller-supplied request budget.
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
        task_type: str = "general",
        before_attempt: Callable[[], object] | None = None,
    ) -> WorkflowResult:
        started = perf_counter()
        plan_prompt = _compose_bounded_prompt(
            "Act as a planner. Produce a concise, ordered plan with requirements, "
            "acceptance criteria, and material assumptions. Do not execute the task yet.",
            (("ORIGINAL TASK", prompt),),
            self._max_input_chars,
        )
        if prompt not in plan_prompt:
            raise WorkflowInputTooLong(
                "Original task exceeds the workflow input limit; shorten it or raise the configured limit"
            )
        plan = self._orchestrator.run(
            plan_prompt,
            preferred_provider=preferred_provider,
            task_type="planner",
            before_attempt=before_attempt,
        )

        execution_prompt = _compose_bounded_prompt(
            "Execute the original task using the plan. Produce a complete working draft "
            "or result, state uncertainty honestly, and do not invent completed actions.",
            (("ORIGINAL TASK", prompt), ("PLAN", plan.text)),
            self._max_input_chars,
        )
        execution = self._orchestrator.run(
            execution_prompt,
            preferred_provider=preferred_provider,
            task_type=task_type,
            before_attempt=before_attempt,
        )

        review_prompt = _compose_bounded_prompt(
            "Act as an independent reviewer. Check the task requirements against the plan "
            "and result; identify omissions, contradictions, unsafe assumptions, and test gaps. "
            "Return actionable corrections only.",
            (
                ("ORIGINAL TASK", prompt),
                ("PLAN", plan.text),
                ("EXECUTION RESULT", execution.text),
            ),
            self._max_input_chars,
        )
        review = self._orchestrator.run(
            review_prompt,
            preferred_provider=preferred_provider,
            task_type="reviewer",
            before_attempt=before_attempt,
        )

        final_prompt = _compose_bounded_prompt(
            "Produce the final complete deliverable for the original task, incorporating "
            "the review corrections. Do not mention internal workflow stages or expose review "
            "notes. Clearly label anything that remains unverified or incomplete.",
            (
                ("ORIGINAL TASK", prompt),
                ("PLAN", plan.text),
                ("EXECUTION RESULT", execution.text),
                ("REVIEW CORRECTIONS", review.text),
            ),
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
            provider_calls=plan.attempts + execution.attempts + review.attempts + final.attempts,
        )
