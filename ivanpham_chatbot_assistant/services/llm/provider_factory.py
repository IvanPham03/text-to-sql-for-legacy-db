from typing import Any

from .base_llm_provider import BaseLLMProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.azure_openai_provider import AzureOpenAIProvider
from .providers.ollama_provider import OllamaProvider
from .providers.openai_provider import OpenAIProvider


class ProviderFactory:
    """
    Factory class to instantiate LangChain-based LLM providers.
    """

    @staticmethod
    def get_provider(provider_name: str, config: dict[str, Any]) -> BaseLLMProvider:
        """
        Instantiates and returns a LangChain-based LLM provider.
        """
        provider_name = provider_name.lower()

        if provider_name == "openai":
            return OpenAIProvider(config)

        if provider_name == "azure":
            return AzureOpenAIProvider(config)

        if provider_name == "ollama":
            return OllamaProvider(config)

        if provider_name == "anthropic":
            return AnthropicProvider(config)

        raise ValueError(f"Unsupported LLM provider for LangChain: {provider_name}")
