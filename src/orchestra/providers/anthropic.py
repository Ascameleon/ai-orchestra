"""Optional Anthropic adapter with deferred SDK import and bounded input/output."""
from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError, ProviderResult


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is missing")
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ProviderConfigurationError(
                'Anthropic SDK is not installed; install the optional extra with pip install -e ".[anthropic]"'
            ) from exc
        self._model = settings.anthropic_model
        self._max_input_chars = settings.max_input_chars
        self._max_output_tokens = settings.max_output_tokens
        self._client = Anthropic(api_key=settings.anthropic_api_key)

    def generate(self, prompt: str) -> ProviderResult:
        if not prompt or not prompt.strip():
            raise ValueError("prompt must not be empty")
        if len(prompt) > self._max_input_chars:
            raise ValueError(f"prompt exceeds {self._max_input_chars} characters")
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_output_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise ProviderCallError("Anthropic request failed") from exc
        text = "\n".join(
            block.text for block in response.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", "").strip()
        )
        if not text:
            raise ProviderCallError("Anthropic returned an empty response")
        return ProviderResult(self.name, self._model, text, len(prompt), len(text))
