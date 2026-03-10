from typing import Any

from ..base import BaseStrategy


class ForeignKeyLinkingStrategy(BaseStrategy):
    """
    Strategy that emphasizes foreign key relationships for joins.
    """

    name = "foreign_key_linking"

    def apply(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = "Relationship Awareness: Strictly use the provided foreign key constraints to determine join paths. Do not attempt joins on columns without established relationships unless necessary."
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
