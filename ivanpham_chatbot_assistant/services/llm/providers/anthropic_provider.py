from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage

from ..base_llm_provider import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider using LangChain's ChatAnthropic.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.llm = ChatAnthropic(
            model=config["model"],
            anthropic_api_key=config.get("api_key"),
            temperature=config.get("temperature", 0),
            max_tokens_to_sample=config.get("max_tokens", 2048),
            timeout=config.get("timeout", 30),
            max_retries=0,
        )

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        response = await self.llm.ainvoke([HumanMessage(content=prompt)], **kwargs)
        return str(response.content)

    async def chat(
        self, messages: list[BaseMessage | dict[str, str]], **kwargs: Any
    ) -> str:
        langchain_messages = self._convert_messages(messages)
        response = await self.llm.ainvoke(langchain_messages, **kwargs)
        return str(response.content)
