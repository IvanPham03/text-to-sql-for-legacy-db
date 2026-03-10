from typing import Any, Dict
from ..base import BaseStrategy

class ResultVerificationStrategy(BaseStrategy):
    """
    Strategy that checks the final answer against the query result.
    """
    name = "result_verification"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # This is usually applied AFTER execution
        prompt = context.get("prompt", "")
        instruction = "Verification: Double-check that the final business answer accurately reflects the numerical data returned by the SQL query."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
