from typing import Any, Dict
from ..base import BaseStrategy

class SchemaPruningStrategy(BaseStrategy):
    """
    Strategy to prune irrelevant tables from the schema context.
    """
    name = "schema_pruning"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = "Table Pruning: Discard all tables that are not necessary for answering the user's question to reduce noise and context window usage."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
