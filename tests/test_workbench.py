from fastapi.testclient import TestClient

from orchestra.api import create_app
from orchestra.core import Orchestrator
from orchestra.providers.base import ProviderResult


class StubProvider:
    name = "stub"

    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult("stub", "test-model", "safe test response", len(prompt), 18)


def test_root_serves_goal_workbench():
    client = TestClient(create_app(Orchestrator(StubProvider())))
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "OBJECTIF → LIVRABLE" in response.text
    assert "review_provider" in response.text
    assert "Fournisseur de relecture indépendante" in response.text
    assert "relecture "+'"+data.review_provider+"' in response.text
    assert "/v1/workflows/plan-execute" in response.text
    assert "localStorage" not in response.text
