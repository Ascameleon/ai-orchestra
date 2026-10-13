"""Google Gemini adapter. Never logs prompts, responses, or credentials."""
from google import genai
from google.genai import types

from orchestra.config import Settings
from orchestra.providers.base import ProviderConfigurationError, ProviderResult


class GeminiProvider:
    name = "gemini"

    def __init__(self, settings: Settings):
        if not settings.gemini_api_key:
            raise ProviderConfigurationError("GEMINI_API_KEY is missing; configure it in the local environment.")
        self._model = settings.gemini_model
        self._max_output_tokens = settings.max_output_tokens
        self._max_input_chars = settings.max_input_chars
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def generate(self, prompt: str) -> ProviderResult:
        if not prompt or not prompt.strip():
            raise ValueError("prompt must not be empty")
        if len(prompt) > self._max_input_chars:
            raise ValueError(f"prompt exceeds {self._max_input_chars} characters")
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=self._max_output_tokens),
        )
        text = response.text
        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty response")
        return ProviderResult(self.name, self._model, text, len(prompt), len(text))
