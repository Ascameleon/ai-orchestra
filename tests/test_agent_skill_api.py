from fastapi.testclient import TestClient

from orchestra.api import create_app
from orchestra.core import Orchestrator
from orchestra.providers.base import ProviderResult


class RecordingProvider:
    def __init__(self, name: str):
        self.name = name
        self.prompts = []

    def generate(self, prompt: str) -> ProviderResult:
        self.prompts.append(prompt)
        text = "ok"
        return ProviderResult(self.name, "test-model", text, len(prompt), len(text))


def test_agent_and_skill_catalogs_are_exposed_and_route_tasks():
    coder = RecordingProvider("code-provider")
    researcher = RecordingProvider("research-provider")
    orchestrator = Orchestrator(
        [coder, researcher],
        routes=(("code", "code-provider"), ("research", "research-provider")),
    )
    client = TestClient(create_app(orchestrator))

    agents = client.get("/v1/agents")
    skills = client.get("/v1/skills")
    assert agents.status_code == 200
    assert len(agents.json()) == 9
    assert any(agent["name"] == "coder" for agent in agents.json())
    assert skills.status_code == 200
    assert len(skills.json()) == 9
    assert any(skill["name"] == "run_tests" for skill in skills.json())

    response = client.post("/v1/tasks", json={"prompt": "fix this bug", "agent": "coder"})
    assert response.status_code == 200
    assert response.json()["provider"] == "code-provider"
    assert "Act as the coding agent" in coder.prompts[-1]
    assert "fix this bug" in coder.prompts[-1]

    response = client.post("/v1/tasks", json={"prompt": "find relevant sources", "skill": "research"})
    assert response.status_code == 200
    assert response.json()["provider"] == "research-provider"
    assert "Skill: research" in researcher.prompts[-1]
    assert "find relevant sources" in researcher.prompts[-1]


def test_unknown_or_conflicting_agent_skill_selection_is_rejected_before_provider_call():
    provider = RecordingProvider("stub")
    client = TestClient(create_app(Orchestrator(provider)))
    payloads = [
        {"prompt": "task", "agent": "unknown"},
        {"prompt": "task", "skill": "unknown"},
        {"prompt": "task", "agent": "coder", "skill": "write_code"},
        {"prompt": "task", "agent": "coder", "task_type": "research"},
    ]

    for payload in payloads:
        assert client.post("/v1/tasks", json=payload).status_code == 422
    assert provider.prompts == []


def test_agent_and_skill_catalogs_honor_api_key(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_API_KEY", "local-key")
    client = TestClient(create_app(Orchestrator(RecordingProvider("stub"))))

    assert client.get("/v1/agents").status_code == 401
    assert client.get("/v1/skills").status_code == 401
    headers = {"X-API-Key": "local-key"}
    assert client.get("/v1/agents", headers=headers).status_code == 200
    assert client.get("/v1/skills", headers=headers).status_code == 200
