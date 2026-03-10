from typing import Any, Dict
from ..base import BaseStrategy

class SampleValueSchemaStrategy(BaseStrategy):
    """
    Strategy that includes sample values in the schema context.
    """
    name = "sample_value_schema"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = "Value Grounding: Use the provided sample values for each column to understand the data format and valid filter values."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
