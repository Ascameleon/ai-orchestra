import httpx
import pytest

from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError
from orchestra.providers.manus import ManusProvider


def settings(**overrides):
    values = {
        "gemini_api_key": None,
        "gemini_model": "unused",
        "max_input_chars": 100,
        "max_output_tokens": 32,
        "manus_api_key": "test-manus-key",
        "manus_allow_paid_calls": True,
        "manus_allow_agent_tools": True,
        "manus_agent_profile": "lite",
        "manus_timeout_seconds": 10,
        "manus_poll_interval_seconds": 1,
    }
    values.update(overrides)
    return Settings(**values)


def test_manus_requires_explicit_paid_call_opt_in():
    with pytest.raises(ProviderConfigurationError, match="MANUS_ALLOW_PAID_CALLS"):
        ManusProvider(settings(manus_allow_paid_calls=False))
    with pytest.raises(ProviderConfigurationError, match="MANUS_API_KEY"):
        ManusProvider(settings(manus_api_key=None))


def test_manus_creates_private_lite_task_and_returns_result_without_live_calls():
    seen = []

    def handler(request):
        seen.append(request)
        assert request.headers["x-manus-api-key"] == "test-manus-key"
        if request.url.path.endswith("/task.create"):
            body = __import__("json").loads(request.content)
            assert body == {
                "message": {"content": "Summarize this source"},
                "agent_profile": "lite",
                "share_visibility": "private",
                "interactive_mode": True,
                "clear_connectors": True,
            }
            return httpx.Response(200, json={"ok": True, "task_id": "task-123"})
        if request.url.path.endswith("/task.listMessages"):
            return httpx.Response(200, json={"ok": True, "messages": [
                {"id": "event-2", "type": "status_update",
                 "status_update": {"agent_status": "stopped"}},
                {"id": "event-1", "type": "assistant_message",
                 "assistant_message": {"content": "Verified summary", "delivery_kind": "result"}},
            ]})
        if request.url.path.endswith("/task.detail"):
            return httpx.Response(200, json={"ok": True, "task": {
                "id": "task-123", "status": "stopped", "has_running_background_jobs": False
            }})
        raise AssertionError(f"Unexpected Manus endpoint: {request.url.path}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = ManusProvider(settings(), client=client).generate("Summarize this source")
    client.close()

    assert result.provider == "manus"
    assert result.model == "lite"
    assert result.text == "Verified summary"
    assert result.input_chars == len("Summarize this source")
    assert result.output_chars == len("Verified summary")
    assert [request.method for request in seen] == ["POST", "GET", "GET"]


def test_manus_never_auto_confirms_waiting_tasks():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        if request.url.path.endswith("/task.create"):
            return httpx.Response(200, json={"ok": True, "task_id": "task-waiting"})
        if request.url.path.endswith("/task.listMessages"):
            return httpx.Response(200, json={"ok": True, "messages": [
                {"type": "status_update", "status_update": {"agent_status": "waiting"}}
            ]})
        raise AssertionError("A waiting task must not be confirmed or resumed automatically")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = ManusProvider(settings(), client=client)
    with pytest.raises(ProviderCallError, match="automatic confirmation is disabled"):
        provider.generate("Prepare a draft")
    client.close()
    assert len(calls) == 2


def test_manus_keeps_polling_until_background_jobs_finish():
    detail_calls = [0]

    def handler(request):
        if request.url.path.endswith("/task.create"):
            return httpx.Response(200, json={"ok": True, "task_id": "task-background"})
        if request.url.path.endswith("/task.listMessages"):
            return httpx.Response(200, json={"ok": True, "messages": [
                {"type": "status_update", "status_update": {"agent_status": "stopped"}},
                {"type": "assistant_message", "assistant_message": {
                    "content": "Final result", "delivery_kind": "result"
                }},
            ]})
        if request.url.path.endswith("/task.detail"):
            detail_calls[0] += 1
            return httpx.Response(200, json={"ok": True, "task": {
                "status": "stopped",
                "has_running_background_jobs": detail_calls[0] == 1,
            }})
        raise AssertionError(f"Unexpected endpoint: {request.url.path}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = ManusProvider(settings(), client=client, sleeper=lambda _: None).generate("Do work")
    client.close()
    assert result.text == "Final result"
    assert detail_calls[0] == 2


def test_manus_timeout_does_not_retry_or_create_a_second_task():
    calls = []
    now = [0.0]

    def handler(request):
        calls.append(request.url.path)
        if request.url.path.endswith("/task.create"):
            return httpx.Response(200, json={"ok": True, "task_id": "task-running"})
        if request.url.path.endswith("/task.listMessages"):
            return httpx.Response(200, json={"ok": True, "messages": [
                {"type": "status_update", "status_update": {"agent_status": "running"}}
            ]})
        raise AssertionError(f"Unexpected endpoint: {request.url.path}")

    def advance(seconds):
        now[0] += seconds

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = ManusProvider(
        settings(manus_timeout_seconds=2),
        client=client,
        clock=lambda: now[0],
        sleeper=advance,
    )
    with pytest.raises(ProviderCallError, match="timed out"):
        provider.generate("Long-running task")
    client.close()
    assert calls.count("/v2/task.create") == 1
    assert calls.count("/v2/task.listMessages") == 2


def test_manus_requires_explicit_account_skills_acknowledgement():
    with pytest.raises(ProviderConfigurationError, match="MANUS_ALLOW_AGENT_TOOLS"):
        ManusProvider(settings(manus_allow_agent_tools=False))
