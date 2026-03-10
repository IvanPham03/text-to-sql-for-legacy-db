import time
import asyncio
from typing import Any, Dict, List, Optional, Union
from prometheus_client import Counter, Histogram

from ivanpham_chatbot_assistant.log import logger
from .provider_factory import ProviderFactory
from .base_llm_provider import BaseLLMProvider
from langchain_core.messages import BaseMessage, HumanMessage

# Prometheus Metrics
LLM_REQUESTS = Counter(
    "llm_requests_total", 
    "Total number of LLM requests", 
    ["provider", "model", "status"]
)
LLM_FAILURES = Counter(
    "llm_failures_total", 
    "Total number of LLM failures", 
    ["provider", "model", "error_type"]
)
LLM_LATENCY = Histogram(
    "llm_latency_seconds", 
    "Latency of LLM requests in seconds", 
    ["provider", "model"]
)
LLM_TOKENS = Counter(
    "llm_tokens_total", 
    "Total tokens consumed", 
    ["provider", "model", "type"]
)
LLM_COST = Counter(
    "llm_cost_total", 
    "Total estimated cost of LLM requests", 
    ["provider", "model"]
)

# Pricing Table (USD per 1M tokens)
PRICING = {
    "gpt-4o": {"prompt": 5.0, "completion": 15.0},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.6},
    "claude-3-5-sonnet-20240620": {"prompt": 3.0, "completion": 15.0},
    "claude-3-haiku-20240307": {"prompt": 0.25, "completion": 1.25},
}

class LLMService:
    """
    Production-grade LLM Gateway with Fallback, Retry, Metrics, and Cost Tracking.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM service with provider configurations.
        
        Config format:
        {
            "providers": [
                {"name": "openai", "config": {...}},
                {"name": "ollama", "config": {...}}
            ]
        }
        """
        self.provider_configs = config.get("providers", [])
        if not self.provider_configs:
             # Support legacy single-provider config if needed
             if "name" in config:
                 self.provider_configs = [config]
             else:
                raise ValueError("LLM configuration must contain at least one provider.")
        
        self.providers: List[BaseLLMProvider] = []
        for p_conf in self.provider_configs:
            provider = ProviderFactory.get_provider(p_conf["name"], p_conf["config"])
            self.providers.append(provider)

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Generates text with fallback and retry logic.
        """
        messages = [HumanMessage(content=prompt)]
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: List[Union[BaseMessage, Dict[str, str]]], **kwargs: Any) -> Dict[str, Any]:
        """
        Sends chat messages with fallback and retry logic.
        """
        last_exception = None
        
        for provider in self.providers:
            # Retry logic with exponential backoff
            for attempt in range(3):
                start_time = time.perf_counter()
                p_name = provider.config.get("name", provider.__class__.__name__)
                m_name = provider.model_name
                
                try:
                    # We access the internal LangChain model to get rich metadata if possible
                    # but we use the provider's chat method for abstraction
                    
                    # LangChain invoke returns BaseMessage which sometimes has metadata
                    # To get token usage, we might need to use specific call methods or check response
                    
                    # For this implementation, we assume we want to track metadata from the response
                    # Since we refactored providers to return str, we need to modify them to return more
                    # OR we intercept the call here if the provider exposes the llm object.
                    
                    response = await provider.llm.ainvoke(
                        provider._convert_messages(messages), 
                        **kwargs
                    )
                    
                    latency = time.perf_counter() - start_time
                    
                    # Extract usage
                    usage = self._extract_usage(response)
                    cost = self._calculate_cost(m_name, usage)
                    
                    # Metrics
                    LLM_REQUESTS.labels(provider=p_name, model=m_name, status="success").inc()
                    LLM_LATENCY.labels(provider=p_name, model=m_name).observe(latency)
                    LLM_TOKENS.labels(provider=p_name, model=m_name, type="prompt").inc(usage["prompt_tokens"])
                    LLM_TOKENS.labels(provider=p_name, model=m_name, type="completion").inc(usage["completion_tokens"])
                    LLM_COST.labels(provider=p_name, model=m_name).inc(cost)
                    
                    logger.info(
                        f"LLM request successful via {p_name}",
                        extra={
                            "provider": p_name,
                            "model": m_name,
                            "latency": latency,
                            "usage": usage,
                            "cost": cost
                        }
                    )
                    
                    return {
                        "text": str(response.content),
                        "provider": p_name,
                        "model": m_name,
                        "latency": latency,
                        "usage": usage,
                        "cost": cost
                    }

                except Exception as e:
                    LLM_FAILURES.labels(provider=p_name, model=m_name, error_type=type(e).__name__).inc()
                    logger.warning(
                        f"LLM request failed (Attempt {attempt + 1}/3) via {p_name}: {str(e)}"
                    )
                    last_exception = e
                    
                    # Exponential backoff
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                    continue
            
            # If all attempts for current provider failed, try next provider (fallback)
            logger.error(f"Provider {p_name} exhausted. Trying fallback if available.")
            
        raise RuntimeError(f"All LLM providers failed. Last error: {str(last_exception)}")

    def _extract_usage(self, response: Any) -> Dict[str, int]:
        """
        Extract token usage from LangChain response.
        """
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        metadata = getattr(response, "response_metadata", {})
        token_usage = metadata.get("token_usage")
        
        if token_usage:
            usage["prompt_tokens"] = token_usage.get("prompt_tokens", 0)
            usage["completion_tokens"] = token_usage.get("completion_tokens", 0)
            usage["total_tokens"] = token_usage.get("total_tokens", 0)
        
        # Fallback for different LangChain metadata structures (e.g. Anthropic)
        elif "usage" in metadata:
            u = metadata["usage"]
            usage["prompt_tokens"] = u.get("input_tokens", 0)
            usage["completion_tokens"] = u.get("output_tokens", 0)
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            
        return usage

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Calculate cost based on pricing table.
        """
        model_pricing = PRICING.get(model)
        if not model_pricing:
            return 0.0
        
        prompt_cost = (usage["prompt_tokens"] / 1_000_000) * model_pricing["prompt"]
        completion_cost = (usage["completion_tokens"] / 1_000_000) * model_pricing["completion"]
        
        return prompt_cost + completion_cost
