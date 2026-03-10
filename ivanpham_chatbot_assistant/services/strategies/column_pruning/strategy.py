from typing import Any, Dict
from ..base import BaseStrategy

class ColumnPruningStrategy(BaseStrategy):
    """
    Strategy to prune irrelevant columns from the context.
    """
    name = "column_pruning"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = (
            "Column Pruning: Examine each table in the schema and "
            "discard columns that are not directly involved in the query criteria, "
            "projections, or join conditions."
        )
        
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
