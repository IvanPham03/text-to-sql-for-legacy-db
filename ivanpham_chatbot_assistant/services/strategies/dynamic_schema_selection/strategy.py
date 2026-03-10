from typing import Any, Dict
from ..base import BaseStrategy

class DynamicSchemaSelectionStrategy(BaseStrategy):
    """
    Strategy to dynamically filter schema based on question intent.
    """
    name = "dynamic_schema_selection"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = "Context Filtering: Only include tables and columns that have a high semantic similarity to the terms in the user question."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
