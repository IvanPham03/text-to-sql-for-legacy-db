from typing import Any, Dict
from ..base import BaseStrategy

class SelfConsistencyStrategy(BaseStrategy):
    """
    Strategy that generates multiple SQL variants and selects the most common one.
    """
    name = "self_consistency"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = "Consistency: Generate 3 different versions of the SQL query. Compare them and ensure the final output is the one that is logically most consistent across all versions."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
