from fastapi.testclient import TestClient

from orchestra.api import create_app
from orchestra.core import Orchestrator
from orchestra.providers.base import ProviderResult


class StubProvider:
    name = 'stub'

    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult(self.name, 'model', 'ok', len(prompt), 2)


class StubFetcher:
    enabled = True

    def fetch_many(self, urls):
        return ()


def test_evidence_fetch_requires_api_key_and_disclaims_verification(monkeypatch):
    monkeypatch.setenv('ORCHESTRA_API_KEY', 'local-key')
    client = TestClient(create_app(Orchestrator(StubProvider()), StubFetcher()))
    payload = {'urls': ['https://example.com/article']}
    assert client.post('/v1/evidence/fetch', json=payload).status_code == 401
    response = client.post('/v1/evidence/fetch', json=payload, headers={'X-API-Key': 'local-key'})
    assert response.status_code == 200
    assert response.json()['source_authenticity_verified'] is False
    assert response.json()['semantic_support_verified'] is False
