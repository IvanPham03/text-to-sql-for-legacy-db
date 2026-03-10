from typing import Any, Dict
from .providers.openai_provider import OpenAIProvider
from .providers.azure_openai_provider import AzureOpenAIProvider
from .providers.ollama_provider import OllamaProvider
from .providers.anthropic_provider import AnthropicProvider
from .base_llm_provider import BaseLLMProvider


class ProviderFactory:
    """
    Factory class to instantiate LangChain-based LLM providers.
    """

    @staticmethod
    def get_provider(provider_name: str, config: Dict[str, Any]) -> BaseLLMProvider:
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
