from typing import Any, Dict
from ..base import BaseStrategy

class RolePromptingStrategy(BaseStrategy):
    """
    Strategy to set the persona for the LLM.
    """
    name = "role_prompting"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        role = "You are an expert SQL engineer. Your task is to write high-quality, performant, and secure T-SQL queries for Microsoft SQL Server."
        
        context["prompt"] = f"{role}\n\n{prompt}" if prompt else role
        return context
