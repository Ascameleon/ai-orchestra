"""Provider construction and registration from validated settings."""
from orchestra.config import Settings
from orchestra.providers.gemini import GeminiProvider, ProviderConfigurationError
from orchestra.providers.openai import OpenAIProvider
from orchestra.registry import ProviderRegistry


def build_provider_registry(settings: Settings) -> ProviderRegistry:
    """Build only providers explicitly configured for this process.

    Adapters are added here as optional integrations become available. No
    network request is made during registry construction.
    """
    registry = ProviderRegistry()
    if settings.provider_name == "gemini":
        if not settings.gemini_api_key:
            raise ProviderConfigurationError("GEMINI_API_KEY is missing")
        registry.register("gemini", GeminiProvider(settings))
        return registry
    if settings.provider_name == "openai":
        if not settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is missing")
        registry.register("openai", OpenAIProvider(settings))
        return registry
    raise ProviderConfigurationError(
        f"Unsupported ORCHESTRA_PROVIDER: {settings.provider_name}"
    )
