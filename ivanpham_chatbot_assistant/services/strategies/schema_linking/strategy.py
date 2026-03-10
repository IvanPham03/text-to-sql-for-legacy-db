from typing import Any, Dict
from ..base import BaseStrategy

class SchemaLinkingStrategy(BaseStrategy):
    """
    Strategy that links natural language entities to schema elements.
    In a production setting, this could use an LLM call or fuzzy matching.
    """
    name = "schema_linking"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = (
            "Schema Linking: Identify all mentioned entities in the question.\n"
            "Maps these entities to the corresponding tables and columns provided in the schema context.\n"
            "Example: 'highest sales' -> sales_table.amount, 'of each product' -> products.name"
        )
        
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
