from typing import Any, Dict
from ..base import BaseStrategy

class FormatConstraintStrategy(BaseStrategy):
    """
    Strategy to strictly enforce output format.
    """
    name = "format_constraint"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        constraint = (
            "CRITICAL: Return ONLY the raw SQL query string inside a code block. "
            "Do NOT include any conversational text, explanations, or quotes."
        )
        
        context["prompt"] = f"{prompt}\n\n{constraint}" if prompt else constraint
        return context
