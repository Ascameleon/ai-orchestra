from fastapi.testclient import TestClient

from orchestra.api import create_app
from orchestra.core import Orchestrator
from orchestra.providers.base import ProviderResult


class StubProvider:
    name = 'stub'
    def generate(self, prompt: str) -> ProviderResult:
        text = 'answer'
        return ProviderResult(self.name, 'test-model', text, len(prompt), len(text))


def test_provider_circuit_status_requires_configured_api_key(monkeypatch):
    monkeypatch.setenv('ORCHESTRA_API_KEY', 'test-secret')
    client = TestClient(create_app(Orchestrator(StubProvider())))
    assert client.get('/providers/circuits').status_code == 401
    response = client.get('/providers/circuits', headers={'X-API-Key': 'test-secret'})
    assert response.status_code == 200
    assert response.json() == [{
        'provider': 'stub',
        'state': 'closed',
        'consecutive_failures': 0,
        'retry_after_seconds': 0,
    }]


def test_provider_circuit_status_reports_open_circuit(monkeypatch):
    monkeypatch.delenv('ORCHESTRA_API_KEY', raising=False)
    orchestrator = Orchestrator(StubProvider(), circuit_failure_threshold=1)
    orchestrator.circuit_breaker.record_failure('stub')
    response = TestClient(create_app(orchestrator)).get('/providers/circuits')
    assert response.status_code == 200
    assert response.json()[0]['state'] == 'open'
    assert response.json()[0]['consecutive_failures'] == 1
    assert response.json()[0]['retry_after_seconds'] >= 1
