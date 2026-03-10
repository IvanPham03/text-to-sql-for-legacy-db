from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers using LangChain.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the provider with configuration.
        """
        self.config = config
        self.model_name = config.get("model")
        self.llm: Any = None  # To be initialized by subclasses

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generates a text completion for a given prompt.
        """

    @abstractmethod
    async def chat(
        self, messages: list[BaseMessage | dict[str, str]], **kwargs: Any
    ) -> str:
        """
        Sends a list of messages for a chat completion.
        """

    def _convert_messages(
        self, messages: list[BaseMessage | dict[str, str]]
    ) -> list[BaseMessage]:
        """
        Helper to convert dict messages to LangChain message objects.
        """
        converted = []
        for m in messages:
            if isinstance(m, BaseMessage):
                converted.append(m)
                continue

            role = m.get("role")
            content = m.get("content", "")
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "user":
                converted.append(HumanMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
        return converted
