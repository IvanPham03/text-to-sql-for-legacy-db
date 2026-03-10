from abc import ABC, abstractmethod
from typing import Any


class BaseStrategy(ABC):
    """
    Abstract base class for all Text-to-SQL strategies.
    Each strategy should implement the apply method to modify the context.
    """

    name: str

    @abstractmethod
    def apply(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Apply the strategy logic to the given context.
        """
        raise NotImplementedError
