from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers using LangChain.
    """

    def __init__(self, config: Dict[str, Any]):
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
        pass

    @abstractmethod
    async def chat(self, messages: List[Union[BaseMessage, Dict[str, str]]], **kwargs: Any) -> str:
        """
        Sends a list of messages for a chat completion.
        """
        pass

    def _convert_messages(self, messages: List[Union[BaseMessage, Dict[str, str]]]) -> List[BaseMessage]:
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
