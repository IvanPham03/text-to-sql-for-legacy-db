from typing import Any

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage

from ..base_llm_provider import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider using LangChain's ChatOllama.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.llm = ChatOllama(
            model=config["model"],
            base_url=config.get("endpoint", "http://localhost:11434"),
            temperature=config.get("temperature", 0),
            timeout=config.get("timeout", 60),
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
