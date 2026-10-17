"""Provider construction and registration from validated settings."""
from orchestra.config import Settings
from orchestra.providers.anthropic import AnthropicProvider
from orchestra.providers.base import ProviderConfigurationError
from orchestra.providers.gemini import GeminiProvider
from orchestra.providers.grok import GrokProvider
from orchestra.providers.openai import OpenAIProvider
from orchestra.registry import ProviderRegistry


def _build_named_provider(name: str, settings: Settings):
    if name == "gemini":
        if not settings.gemini_api_key:
            raise ProviderConfigurationError("GEMINI_API_KEY is missing")
        return GeminiProvider(settings)
    if name == "openai":
        if not settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is missing")
        return OpenAIProvider(settings)
    if name == "anthropic":
        if not settings.anthropic_api_key:
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is missing")
        return AnthropicProvider(settings)
    if name == "grok":
        if not settings.xai_api_key:
            raise ProviderConfigurationError("XAI_API_KEY is missing")
        return GrokProvider(settings)
    raise ProviderConfigurationError(f"Unsupported ORCHESTRA_PROVIDER: {name}")


def build_provider_registry(settings: Settings) -> ProviderRegistry:
    """Build primary and explicitly configured fallback adapters without network calls."""
    registry = ProviderRegistry()
    names = (settings.provider_name, *settings.provider_fallbacks)
    for name in names:
        registry.register(name, _build_named_provider(name, settings))
    return registry
