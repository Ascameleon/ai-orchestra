"""Grok adapter using xAI's OpenAI-compatible API endpoint."""
from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError, ProviderResult


class GrokProvider:
    name = "grok"

    def __init__(self, settings: Settings):
        if not settings.grok_api_key:
            raise ProviderConfigurationError("XAI_API_KEY is missing")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderConfigurationError(
                'Grok adapter requires the optional SDK extra: pip install -e ".[grok]"'
            ) from exc
        self._model = settings.grok_model
        self._max_input_chars = settings.max_input_chars
        self._max_output_tokens = settings.max_output_tokens
        self._client = OpenAI(
            api_key=settings.grok_api_key,
            base_url="https://api.x.ai/v1",
            timeout=30.0,
            max_retries=0,
        )

    def generate(self, prompt: str) -> ProviderResult:
        if not prompt or not prompt.strip():
            raise ValueError("prompt must not be empty")
        if len(prompt) > self._max_input_chars:
            raise ValueError(f"prompt exceeds {self._max_input_chars} characters")
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self._max_output_tokens,
            )
            choices = response.choices
            text = choices[0].message.content if choices else None
        except Exception as exc:
            raise ProviderCallError("Grok request failed or returned an invalid response") from exc
        if not isinstance(text, str) or not text.strip():
            raise ProviderCallError("Grok returned an empty response")
        return ProviderResult(self.name, self._model, text, len(prompt), len(text))
