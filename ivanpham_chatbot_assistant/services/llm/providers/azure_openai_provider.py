from typing import Any, Dict, List, Union
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from ..base_llm_provider import BaseLLMProvider


class AzureOpenAIProvider(BaseLLMProvider):
    """
    Azure OpenAI provider using LangChain's AzureChatOpenAI.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm = AzureChatOpenAI(
            azure_deployment=config["deployment_name"],
            openai_api_version=config.get("api_version", "2023-12-01-preview"),
            azure_endpoint=config["endpoint"],
            api_key=config.get("api_key"),
            temperature=config.get("temperature", 0),
            max_tokens=config.get("max_tokens"),
            timeout=config.get("timeout", 30),
            max_retries=0,
        )

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        response = await self.llm.ainvoke([HumanMessage(content=prompt)], **kwargs)
        return str(response.content)

    async def chat(self, messages: List[Union[BaseMessage, Dict[str, str]]], **kwargs: Any) -> str:
        langchain_messages = self._convert_messages(messages)
        response = await self.llm.ainvoke(langchain_messages, **kwargs)
        return str(response.content)
