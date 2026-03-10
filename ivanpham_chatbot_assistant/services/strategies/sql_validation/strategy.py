from typing import Any

from ..base import BaseStrategy


class SqlValidationStrategy(BaseStrategy):
    """
    Strategy for self-validation of SQL.
    """

    name = "sql_validation"

    def apply(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = (
            "Self-Validation: Review the generated SQL for syntax errors, "
            "table join correctness, and column existence. Ensure the query "
            "exactly answers the user question without extra garbage."
        )

        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
