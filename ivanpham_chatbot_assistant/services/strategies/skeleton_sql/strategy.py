from typing import Any

from ..base import BaseStrategy


class SkeletonSqlStrategy(BaseStrategy):
    """
    Strategy that generates a SQL skeleton before filling in details.
    """

    name = "skeleton_sql"

    def apply(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = (
            "Start by drafting a SQL skeleton (SELECT, FROM, JOIN, WHERE structures) "
            "using placeholders, then replace them with actual schema elements."
        )

        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
