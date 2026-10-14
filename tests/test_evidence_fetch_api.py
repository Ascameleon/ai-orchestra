from fastapi.testclient import TestClient

from orchestra.api import create_app
from orchestra.core import Orchestrator
from orchestra.evidence_fetcher import EvidenceFetcher
from orchestra.providers.base import ProviderResult


class StubProvider:
    name = 'stub'

    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult(self.name, 'test-model', 'ok', len(prompt), 2)


def test_evidence_fetch_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv('ORCHESTRA_API_KEY', raising=False)
    monkeypatch.delenv('ORCHESTRA_EVIDENCE_ALLOWED_HOSTS', raising=False)
    client = TestClient(create_app(Orchestrator(StubProvider()), EvidenceFetcher()))
    response = client.post('/v1/evidence/fetch', json={'urls': ['https://example.com/article']})
    assert response.status_code == 503
