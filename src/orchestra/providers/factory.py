"""Provider construction and registration from validated settings."""
from orchestra.config import Settings
from orchestra.providers.anthropic import AnthropicProvider
from orchestra.providers.base import ProviderConfigurationError
from orchestra.providers.deepseek import DeepSeekProvider
from orchestra.providers.gemini import GeminiProvider
from orchestra.providers.freellmapi import FreeLLMAPIProvider
from orchestra.providers.grok import GrokProvider
from orchestra.providers.kimi import KimiProvider
from orchestra.providers.manus import ManusProvider
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
    if name == "kimi":
        if not settings.kimi_api_key:
            raise ProviderConfigurationError("KIMI_API_KEY or MOONSHOT_API_KEY is missing")
        return KimiProvider(settings)
    if name == "deepseek":
        if not settings.deepseek_api_key:
            raise ProviderConfigurationError("DEEPSEEK_API_KEY is missing")
        return DeepSeekProvider(settings)
    if name == "freellmapi":
        if not settings.freellmapi_api_key:
            raise ProviderConfigurationError("FREELLMAPI_API_KEY is missing")
        return FreeLLMAPIProvider(settings)
    if name == "manus":
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
        return ManusProvider(settings)
    raise ProviderConfigurationError(f"Unsupported ORCHESTRA_PROVIDER: {name}")


def build_provider_registry(settings: Settings) -> ProviderRegistry:
    """Build primary and explicitly configured fallback adapters without network calls."""
    registry = ProviderRegistry()
    names = (settings.provider_name, *settings.provider_fallbacks)
    for name in names:
        registry.register(name, _build_named_provider(name, settings))
    return registry
