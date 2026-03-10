from typing import Any

from ..base import BaseStrategy


class LeastToMostStrategy(BaseStrategy):
    """
    Strategy that decomposes complex questions into smaller sub-queries.
    """

    name = "least_to_most"

    def apply(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = "Decomposition: Break the user's question into simpler sub-questions. Solve each sub-part individually, then combine them into the final SQL query."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
