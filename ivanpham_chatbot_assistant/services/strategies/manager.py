from typing import Any, Dict, List
from .base import BaseStrategy


class StrategyManager:
    """
    Orchestrator for applying multiple Text-to-SQL strategies sequentially.
    """

    def __init__(self, strategies: List[BaseStrategy]):
        self.strategies = strategies

    def apply_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sequentially apply all configured strategies.
        """
        for strategy in self.strategies:
            context = strategy.apply(context)
        return context
