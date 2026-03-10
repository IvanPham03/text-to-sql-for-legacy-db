from typing import Any, Dict
from ..base import BaseStrategy

class SchemaDescriptionStrategy(BaseStrategy):
    """
    Strategy that leverages table/column descriptions in the context.
    """
    name = "schema_description"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = "Semantic Context: Pay close attention to the descriptions provided for each table and column to understand their business meaning and relationships."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
