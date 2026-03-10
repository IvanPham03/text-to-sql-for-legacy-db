from typing import Any

from ..base import BaseStrategy


class SampleValueSchemaStrategy(BaseStrategy):
    """
    Strategy that includes sample values in the schema context.
    """

    name = "sample_value_schema"

    def apply(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = "Value Grounding: Use the provided sample values for each column to understand the data format and valid filter values."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
