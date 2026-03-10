from typing import Any

from .base import BaseStrategy


class StrategyManager:
    """
    Orchestrator for applying multiple Text-to-SQL strategies sequentially.
    """

    def __init__(self, strategies: list[BaseStrategy]):
        self.strategies = strategies

    def apply_all(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Sequentially apply all configured strategies.
        """
        for strategy in self.strategies:
            context = strategy.apply(context)
        return context
