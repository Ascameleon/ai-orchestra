"""FreeLLMAPI adapter using its OpenAI-compatible chat endpoint."""
from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError, ProviderResult


class FreeLLMAPIProvider:
    name = "freellmapi"

    def __init__(self, settings: Settings):
        if not settings.freellmapi_api_key:
            raise ProviderConfigurationError("FREELLMAPI_API_KEY is missing")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderConfigurationError(
                'OpenAI SDK is not installed; install the optional extra with pip install -e ".[openai]"'
            ) from exc
        self._model = settings.freellmapi_model
        self._max_input_chars = settings.max_input_chars
        self._max_output_tokens = settings.max_output_tokens
        self._client = OpenAI(
            api_key=settings.freellmapi_api_key,
            base_url=settings.freellmapi_base_url,
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
        except Exception as exc:
            raise ProviderCallError("FreeLLMAPI request failed") from exc
        try:
            choices = response.choices
            text = choices[0].message.content if choices else None
        except Exception as exc:
            raise ProviderCallError("FreeLLMAPI returned an invalid response") from exc
        if not isinstance(text, str) or not text.strip():
            raise ProviderCallError("FreeLLMAPI returned an empty response")
        return ProviderResult(self.name, self._model, text, len(prompt), len(text))
