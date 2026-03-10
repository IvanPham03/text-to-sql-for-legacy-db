from typing import Any

from ..base import BaseStrategy


class ChainOfThoughtStrategy(BaseStrategy):
    """
    Strategy that encourages the model to think step-by-step before generating SQL.
    """

    name = "chain_of_thought"

    def apply(self, context: dict[str, Any]) -> dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = (
            "Let's think step by step to solve the question.\n"
            "1. Identify the entities and their corresponding tables/columns.\n"
            "2. Determine the necessary joins and relations.\n"
            "3. Define the filtering conditions (WHERE clause).\n"
            "4. Define the aggregation or ordering (GROUP BY/ORDER BY).\n"
            "5. Finally, construct the SQL query."
        )

        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
