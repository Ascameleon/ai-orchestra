"""Opt-in Manus API v2 task adapter.

Manus tasks may consume account credits. This adapter is disabled unless the
operator explicitly sets MANUS_ALLOW_PAID_CALLS=true.
"""
from collections.abc import Callable
from time import monotonic, sleep
from typing import Any

from orchestra.config import Settings
from orchestra.providers.base import (
    ProviderCallError,
    ProviderConfigurationError,
    ProviderResult,
)


class ManusProvider:
    name = "manus"
    _base_url = "https://api.manus.ai/v2"

    def __init__(
        self,
        settings: Settings,
        *,
        client: Any | None = None,
        clock: Callable[[], float] = monotonic,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        if not settings.manus_allow_paid_calls:
            raise ProviderConfigurationError(
                "Manus tasks may consume credits; set MANUS_ALLOW_PAID_CALLS=true to opt in"
            )
        if not settings.manus_allow_agent_tools:
            raise ProviderConfigurationError(
                "Manus API-key tasks load enabled account skills; set MANUS_ALLOW_AGENT_TOOLS=true to acknowledge"
            )
        if not settings.manus_api_key:
            raise ProviderConfigurationError("MANUS_API_KEY is missing")
        try:
            import httpx
        except ImportError as exc:
            raise ProviderConfigurationError(
                'Manus HTTP dependency is not installed; install with pip install -e ".[manus]"'
            ) from exc
        self._httpx = httpx
        self._api_key = settings.manus_api_key
        self._profile = settings.manus_agent_profile
        self._max_input_chars = settings.max_input_chars
        self._timeout_seconds = settings.manus_timeout_seconds
        self._poll_interval_seconds = settings.manus_poll_interval_seconds
        self._clock = clock
        self._sleep = sleeper
        self._client = client or httpx.Client(timeout=20.0, follow_redirects=False)

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        timeout_seconds: float = 20.0,
    ) -> dict[str, Any]:
        try:
            response = self._client.request(
                method,
                f"{self._base_url}/{endpoint}",
                headers={"x-manus-api-key": self._api_key},
                params=params,
                json=body,
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (self._httpx.HTTPError, ValueError, TypeError, OSError):
            raise ProviderCallError("Manus request failed") from None
        if not isinstance(payload, dict) or payload.get("ok") is not True:
            raise ProviderCallError("Manus returned an unsuccessful response")
        return payload

    @staticmethod
    def _status(messages: list[dict[str, Any]]) -> str | None:
        for message in messages:
            if message.get("type") == "error_message":
                raise ProviderCallError("Manus task failed")
            if message.get("type") == "status_update":
                update = message.get("status_update")
                if isinstance(update, dict):
                    status = update.get("agent_status")
                    if isinstance(status, str):
                        return status
        return None

    @staticmethod
    def _result_text(messages: list[dict[str, Any]]) -> str:
        """Return only an explicitly marked result, never progress text."""
        for message in messages:
            if message.get("type") != "assistant_message":
                continue
            assistant = message.get("assistant_message")
            if not isinstance(assistant, dict):
                continue
            content = assistant.get("content")
            if (
                assistant.get("delivery_kind") == "result"
                and isinstance(content, str)
                and content.strip()
            ):
                return content.strip()
        return ""

    def generate(self, prompt: str) -> ProviderResult:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must not be empty")
        if len(prompt) > self._max_input_chars:
            raise ValueError(f"prompt exceeds {self._max_input_chars} characters")

        deadline = self._clock() + self._timeout_seconds
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise ProviderCallError("Manus task timed out before creation")
        created = self._request(
            "POST",
            "task.create",
            body={
                "message": {"content": prompt},
                "agent_profile": self._profile,
                "share_visibility": "private",
                "interactive_mode": True,
                "clear_connectors": True,
            },
            timeout_seconds=min(20.0, remaining),
        )
        task_id = created.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ProviderCallError("Manus did not return a task ID")

        while self._clock() < deadline:
            remaining = deadline - self._clock()
            if remaining <= 0:
                break
            response = self._request(
                "GET",
                "task.listMessages",
                params={"task_id": task_id, "order": "desc", "limit": "50"},
                timeout_seconds=min(20.0, remaining),
            )
            raw_messages = response.get("messages", [])
            messages = raw_messages if isinstance(raw_messages, list) else []
            valid_messages = [m for m in messages if isinstance(m, dict)]
            status = self._status(valid_messages)

            if status == "waiting":
                raise ProviderCallError(
                    "Manus task requires user input or action confirmation; automatic confirmation is disabled"
                )
            if status == "error":
                raise ProviderCallError("Manus task failed")
            if status == "stopped":
                remaining = deadline - self._clock()
                if remaining <= 0:
                    break
                detail = self._request(
                    "GET",
                    "task.detail",
                    params={"task_id": task_id},
                    timeout_seconds=min(20.0, remaining),
                )
                task = detail.get("task")
                if not isinstance(task, dict):
                    raise ProviderCallError("Manus returned invalid task details")
                task_status = task.get("status")
                if task_status == "waiting":
                    raise ProviderCallError(
                        "Manus task requires user input or action confirmation; automatic confirmation is disabled"
                    )
                if task_status == "error":
                    raise ProviderCallError("Manus task failed")
                if task_status == "stopped" and task.get("has_running_background_jobs") is not True:
                    if self._clock() >= deadline:
                        break
                    text = self._result_text(valid_messages)
                    if not text:
                        raise ProviderCallError("Manus task stopped without an explicit text result")
                    return ProviderResult(
                        self.name, self._profile, text, len(prompt), len(text)
                    )

            remaining = deadline - self._clock()
            if remaining > 0:
                self._sleep(min(self._poll_interval_seconds, remaining))

        raise ProviderCallError(
            "Manus task timed out; the remote task may still be running"
        )
