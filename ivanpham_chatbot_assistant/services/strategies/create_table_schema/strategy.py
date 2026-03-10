from typing import Any, Dict
from ..base import BaseStrategy

class CreateTableSchemaStrategy(BaseStrategy):
    """
    Strategy that formats the schema using CREATE TABLE DDL statements.
    """
    name = "create_table_schema"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Logic to transform context['schema'] into DDL strings would go here
        # For now, we add an instruction to use this format
        prompt = context.get("prompt", "")
        instruction = "Represent the schema using standard SQL CREATE TABLE statements including data types and constraints."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
