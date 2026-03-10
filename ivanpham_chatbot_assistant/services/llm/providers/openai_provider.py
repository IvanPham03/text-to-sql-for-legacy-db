from typing import Any, Dict, List, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from ..base_llm_provider import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider using LangChain's ChatOpenAI.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm = ChatOpenAI(
            model=config["model"],
            temperature=config.get("temperature", 0),
            api_key=config.get("api_key"),
            max_tokens=config.get("max_tokens"),
            timeout=config.get("timeout", 30),
            max_retries=0, # Retries handled by LLMService
        )

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        response = await self.llm.ainvoke([HumanMessage(content=prompt)], **kwargs)
        return str(response.content)

    async def chat(self, messages: List[Union[BaseMessage, Dict[str, str]]], **kwargs: Any) -> str:
        langchain_messages = self._convert_messages(messages)
        response = await self.llm.ainvoke(langchain_messages, **kwargs)
        return str(response.content)
