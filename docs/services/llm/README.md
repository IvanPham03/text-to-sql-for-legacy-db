# LLM Service Layer

The LLM Service Layer provides a unified, production-grade interface for interacting with various Large Language Models (LLMs) using LangChain as the core abstraction.

## Features

- **Unified Interface**: Standardized `generate` and `chat` methods across all providers.
- **Provider Fallback**: Automatically switches to secondary/tertiary providers if the primary one fails.
- **Exponential Backoff**: Built-in retry logic (3 attempts) with increasing wait times for transient errors.
- **Observability**: Direct integration with Prometheus for tracking latency, errors, token usage, and cost.
- **Cost Management**: Real-time cost estimation based on model-specific pricing tables.

## Supported Providers

- **OpenAI**: Using `ChatOpenAI`.
- **Azure OpenAI**: Using `AzureChatOpenAI`.
- **Anthropic**: Using `ChatAnthropic` (Claude).
- **Ollama**: Using `ChatOllama` for local model execution.

## Configuration

Example configuration for `LLMService`:

```python
config = {
    "providers": [
        {
            "name": "openai",
            "config": {
                "model": "gpt-4o",
                "api_key": "sk-...",
                "temperature": 0
            }
        },
        {
            "name": "anthropic",
            "config": {
                "model": "claude-3-5-sonnet-20240620",
                "api_key": "sk-ant-...",
                "temperature": 0
            }
        }
    ]
}

llm = LLMService(config)
```

## Usage

```python
response = await llm.generate("What is the capital of France?")

print(response["text"])      # "Paris"
print(response["provider"])  # "openai"
print(response["cost"])      # 0.00015
```

## Metrics

Exposed via Prometheus:
- `llm_requests_total`: Labels: `provider`, `model`, `status`.
- `llm_failures_total`: Labels: `provider`, `model`, `error_type`.
- `llm_latency_seconds`: Labels: `provider`, `model`.
- `llm_tokens_total`: Labels: `provider`, `model`, `type` (prompt/completion).
- `llm_cost_total`: Labels: `provider`, `model`.
