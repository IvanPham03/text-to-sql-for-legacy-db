from typing import Any, Dict
from ..base import BaseStrategy

class NegativePromptingStrategy(BaseStrategy):
    """
    Strategy that lists common mistakes to avoid.
    """
    name = "negative_prompting"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        negatives = (
            "Avoid common mistakes:\n"
            "- Do not use LIMIT for SQL Server (use TOP).\n"
            "- Do not use double quotes for string literals.\n"
            "- Do not use non-standard functions if standard ones exist.\n"
            "- Do not return extra columns not requested by the user."
        )
        context["prompt"] = f"{prompt}\n\n{negatives}" if prompt else negatives
        return context
