"""Validated built-in agent catalog for provider-agnostic orchestration."""
import re
from collections.abc import Iterable
from dataclasses import dataclass


SUPPORTED_TASK_TYPES = frozenset(
    {"general", "code", "research", "writing", "analysis", "review", "planner", "reviewer", "writer"}
)
_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,39}$")


@dataclass(frozen=True)
class AgentSpec:
    name: str
    role: str
    task_type: str
    capabilities: tuple[str, ...]
    description: str
    instruction: str


class UnknownAgentRequested(ValueError):
    """Raised when a task names an agent that is not registered."""


DEFAULT_AGENTS = (
    AgentSpec(
        "planner", "planning", "planner", ("plan_task", "decompose", "sequence"),
        "Turns a goal into ordered steps, dependencies, and acceptance criteria.",
        "Act as the planning agent. Break the task into ordered, testable steps and state dependencies, acceptance criteria, and major risks.",
    ),
    AgentSpec(
        "researcher", "research", "research", ("research", "source_synthesis", "fact_assessment"),
        "Separates facts, assumptions, and unknowns while synthesizing available sources.",
        "Act as the research agent. Separate verified facts, assumptions, and unknowns; cite only sources actually supplied or retrieved.",
    ),
    AgentSpec(
        "coder", "coding", "code", ("write_code", "debug", "refactor"),
        "Produces implementation-ready code and focuses on correctness and maintainability.",
        "Act as the coding agent. Produce implementation-ready code, account for edge cases, and never claim tests ran without execution evidence.",
    ),
    AgentSpec(
        "reviewer", "review", "review", ("review_code", "critique", "spec_check"),
        "Reviews changes for correctness, security, and alignment with requirements.",
        "Act as an independent reviewer. Look for correctness bugs, security risks, and specification drift before recommending changes.",
    ),
    AgentSpec(
        "tester", "testing", "review", ("run_tests", "test_design", "failure_analysis"),
        "Designs deterministic tests and analyzes actual test output.",
        "Act as the testing agent. Cover success paths, boundaries, and failures; do not claim code was executed unless actual tool output proves it.",
    ),
    AgentSpec(
        "security", "security", "review", ("audit_security", "threat_model", "secret_hygiene"),
        "Audits trust boundaries, secrets, resource limits, and fail-closed behavior.",
        "Act as the security agent. Prioritize trust boundaries, secret handling, SSRF, resource limits, and fail-closed behavior.",
    ),
    AgentSpec(
        "writer", "writing", "writing", ("summarize", "draft", "rewrite"),
        "Creates clear, structured text aligned with the user's requirements.",
        "Act as the writing agent. Deliver clear, structured text that follows the requested audience, tone, and format.",
    ),
    AgentSpec(
        "critic", "critical_review", "review", ("critique", "assumption_check", "risk_analysis"),
        "Challenges assumptions and distinguishes evidence from speculation.",
        "Act as a critical agent. Challenge assumptions, identify unproven claims, and explain the most consequential risks.",
    ),
    AgentSpec(
        "deliverer", "delivery", "general", ("deliver", "completeness_check", "report_status"),
        "Checks requested requirements and reports verified completion and limitations.",
        "Act as the delivery agent. Check the requested goal and rules, report verified completion, and state remaining limitations without overstating results.",
    ),
)


class AgentRegistry:
    """Immutable name-to-agent catalog with validation at construction time."""

    def __init__(self, agents: Iterable[AgentSpec] = DEFAULT_AGENTS) -> None:
        registry: dict[str, AgentSpec] = {}
        for agent in agents:
            name = agent.name.strip().lower()
            if not _NAME.fullmatch(name):
                raise ValueError("agent names must be simple lowercase identifiers")
            if name != agent.name:
                raise ValueError("agent names must already be normalized")
            if name in registry:
                raise ValueError(f"duplicate agent name: {name}")
            if agent.task_type not in SUPPORTED_TASK_TYPES:
                raise ValueError(f"unsupported task type for agent: {name}")
            if not agent.capabilities or len(set(agent.capabilities)) != len(agent.capabilities):
                raise ValueError(f"agent capabilities must be non-empty and unique: {name}")
            if any(not capability.strip() for capability in agent.capabilities):
                raise ValueError(f"agent capabilities must not be empty: {name}")
            if not agent.role.strip() or not agent.description.strip() or not agent.instruction.strip():
                raise ValueError(f"agent metadata must not be empty: {name}")
            if len(agent.instruction) > 1000 or len(agent.description) > 500:
                raise ValueError(f"agent metadata exceeds the configured limit: {name}")
            registry[name] = agent
        if not registry:
            raise ValueError("at least one agent must be registered")
        self._agents = registry

    def get(self, name: str) -> AgentSpec:
        normalized = name.strip().lower()
        try:
            return self._agents[normalized]
        except KeyError:
            raise UnknownAgentRequested(f"unknown agent: {normalized}") from None

    def list(self) -> tuple[AgentSpec, ...]:
        return tuple(self._agents[name] for name in sorted(self._agents))
