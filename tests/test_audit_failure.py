from fastapi.testclient import TestClient

import orchestra.api as api_module
from orchestra.core import Orchestrator
from orchestra.providers.base import ProviderResult


class BrokenAuditTrail:
    def __init__(self, capacity=1000):
        pass

    def record(self, event):
        raise OSError('storage unavailable')

    def snapshot(self):
        return ()

    @staticmethod
    def now():
        return 0.0


class StubProvider:
    name = 'stub'

    def generate(self, prompt: str) -> ProviderResult:
        text = 'successful result'
        return ProviderResult(self.name, 'test-model', text, len(prompt), len(text))


def test_audit_write_failure_does_not_hide_successful_provider_response(monkeypatch):
    monkeypatch.delenv('ORCHESTRA_API_KEY', raising=False)
    monkeypatch.delenv('ORCHESTRA_AUDIT_DB', raising=False)
    monkeypatch.setattr(api_module, 'AuditTrail', BrokenAuditTrail)
    client = TestClient(api_module.create_app(Orchestrator(StubProvider())))
    response = client.post('/v1/tasks', json={'prompt': 'hello'})
    assert response.status_code == 200
    assert response.json()['text'] == 'successful result'
