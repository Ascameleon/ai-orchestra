"""Optional OpenAI adapter. SDK import and network calls are deferred until configured use."""
from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError, ProviderResult


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is missing")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderConfigurationError(
                'OpenAI SDK is not installed; install the optional extra with pip install -e ".[openai]"'
            ) from exc
        self._model = settings.openai_model
        self._max_input_chars = settings.max_input_chars
        self._max_output_tokens = settings.max_output_tokens
        self._client = OpenAI(api_key=settings.openai_api_key, timeout=30.0, max_retries=0)

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
        except Exception as exc:
            raise ProviderCallError("OpenAI request failed") from exc
        text = response.choices[0].message.content
        if not text or not text.strip():
            raise ProviderCallError("OpenAI returned an empty response")
        return ProviderResult(self.name, self._model, text, len(prompt), len(text))
