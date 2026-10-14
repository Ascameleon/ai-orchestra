"""Validated skill catalog bound to registered agent capabilities."""
import re
from collections.abc import Iterable
from dataclasses import dataclass

from orchestra.agents import AgentRegistry, UnknownAgentRequested

_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,39}$")


@dataclass(frozen=True)
class SkillSpec:
    name: str
    agent_name: str
    task_type: str
    capability: str
    description: str
    instruction: str


class UnknownSkillRequested(ValueError):
    """Raised when a task names a skill that is not registered."""


DEFAULT_SKILLS = (
    SkillSpec(
        "plan_task", "planner", "planner", "plan_task",
        "Create an ordered, testable plan from a goal.",
        "Return numbered steps, dependencies, acceptance criteria, and risks.",
    ),
    SkillSpec(
        "research", "researcher", "research", "research",
        "Synthesize available information and identify unknowns.",
        "Separate verified facts, assumptions, and unknowns; cite only supplied or retrieved sources.",
    ),
    SkillSpec(
        "write_code", "coder", "code", "write_code",
        "Implement or refactor code against explicit requirements.",
        "Provide implementation-ready code and explain edge cases; do not claim tests ran without execution evidence.",
    ),
    SkillSpec(
        "review_code", "reviewer", "review", "review_code",
        "Review code for correctness, security, and specification drift.",
        "Prioritize concrete defects, reproducible evidence, and actionable fixes.",
    ),
    SkillSpec(
        "run_tests", "tester", "review", "run_tests",
        "Design tests or analyze provided test output.",
        "Propose deterministic tests for success, boundary, and failure cases; never imply that you executed code unless actual tool output confirms it.",
    ),
    SkillSpec(
        "audit_security", "security", "review", "audit_security",
        "Audit trust boundaries, secret hygiene, and resource limits.",
        "Check input validation, authentication, SSRF, secrets, and fail-closed behavior; distinguish confirmed defects from hypotheses.",
    ),
    SkillSpec(
        "summarize", "writer", "writing", "summarize",
        "Produce a concise, faithful summary of supplied material.",
        "Preserve important qualifications and do not introduce unsupported facts.",
    ),
    SkillSpec(
        "critique", "critic", "review", "critique",
        "Challenge assumptions and identify consequential risks.",
        "State the strongest counterarguments, missing evidence, and practical failure modes.",
    ),
    SkillSpec(
        "deliver", "deliverer", "general", "deliver",
        "Audit a deliverable against its stated goal and rules.",
        "Report what is verified, what remains incomplete, and any spec drift; do not overstate completion.",
    ),
)


class SkillRegistry:
    """Immutable skill catalog whose entries must map to real agent capabilities."""

    def __init__(
        self,
        agents: AgentRegistry,
        skills: Iterable[SkillSpec] = DEFAULT_SKILLS,
    ) -> None:
        registry: dict[str, SkillSpec] = {}
        for skill in skills:
            name = skill.name.strip().lower()
            if not _NAME.fullmatch(name) or name != skill.name:
                raise ValueError("skill names must be normalized lowercase identifiers")
            if name in registry:
                raise ValueError(f"duplicate skill name: {name}")
            try:
                agent = agents.get(skill.agent_name)
            except UnknownAgentRequested:
                raise ValueError(f"skill references an unknown agent: {name}") from None
            if skill.task_type != agent.task_type or skill.capability not in agent.capabilities:
                raise ValueError(f"skill does not match its agent capability: {name}")
            if not skill.description.strip() or not skill.instruction.strip():
                raise ValueError(f"skill metadata must not be empty: {name}")
            if len(skill.instruction) > 1000 or len(skill.description) > 500:
                raise ValueError(f"skill metadata exceeds the configured limit: {name}")
            registry[name] = skill
        if not registry:
            raise ValueError("at least one skill must be registered")
        self._skills = registry

    def get(self, name: str) -> SkillSpec:
        normalized = name.strip().lower()
        try:
            return self._skills[normalized]
        except KeyError:
            raise UnknownSkillRequested(f"unknown skill: {normalized}") from None

    def list(self) -> tuple[SkillSpec, ...]:
        return tuple(self._skills[name] for name in sorted(self._skills))
