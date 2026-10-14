import pytest

from orchestra.agents import AgentRegistry, AgentSpec, UnknownAgentRequested
from orchestra.skills import SkillRegistry, SkillSpec, UnknownSkillRequested


def test_default_agent_and_skill_catalogs_are_complete_and_consistent():
    agents = AgentRegistry()
    skills = SkillRegistry(agents)

    assert len(agents.list()) == 9
    assert len(skills.list()) == 9
    assert [item.name for item in agents.list()] == sorted(item.name for item in agents.list())
    for skill in skills.list():
        agent = agents.get(skill.agent_name)
        assert skill.task_type == agent.task_type
        assert skill.capability in agent.capabilities


def test_registry_lookups_are_case_insensitive_and_unknown_names_are_explicit():
    agents = AgentRegistry()
    skills = SkillRegistry(agents)

    assert agents.get("CODER").name == "coder"
    assert skills.get("RUN_TESTS").name == "run_tests"
    with pytest.raises(UnknownAgentRequested):
        agents.get("missing")
    with pytest.raises(UnknownSkillRequested):
        skills.get("missing")


def test_agent_registry_rejects_duplicates_and_invalid_task_types():
    agent = AgentSpec(
        "planner", "planning", "not-a-task", ("plan_task",), "description", "instruction"
    )
    with pytest.raises(ValueError, match="unsupported task type"):
        AgentRegistry([agent])
    with pytest.raises(ValueError, match="duplicate"):
        AgentRegistry([AgentRegistry().get("planner"), AgentRegistry().get("planner")])


def test_skill_registry_rejects_unknown_agents_and_capability_mismatches():
    agents = AgentRegistry()
    unknown_agent = SkillSpec(
        "new_skill", "missing", "general", "deliver", "description", "instruction"
    )
    with pytest.raises(ValueError, match="unknown agent"):
        SkillRegistry(agents, [unknown_agent])

    mismatch = SkillSpec(
        "new_skill", "coder", "code", "audit_security", "description", "instruction"
    )
    with pytest.raises(ValueError, match="does not match"):
        SkillRegistry(agents, [mismatch])


def test_registries_reject_empty_catalogs_and_empty_capabilities():
    with pytest.raises(ValueError, match="at least one agent"):
        AgentRegistry([])
    invalid_agent = AgentSpec(
        "empty", "role", "general", (), "description", "instruction"
    )
    with pytest.raises(ValueError, match="capabilities"):
        AgentRegistry([invalid_agent])
