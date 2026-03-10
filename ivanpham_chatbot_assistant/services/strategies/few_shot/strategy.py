from typing import Any, Dict
from ..base import BaseStrategy

class FewShotStrategy(BaseStrategy):
    """
    Strategy that prepends few-shot examples to the prompt.
    """
    name = "few_shot"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        examples = context.get("examples", [])
        question = context.get("question", "")

        if not examples:
            return context

        example_str = "\n\n".join([
            f"Question: {ex['question']}\nSQL: {ex['sql']}" 
            for ex in examples
        ])

        prompt = context.get("prompt", "")
        context["prompt"] = f"{example_str}\n\nQuestion: {question}\nSQL:" if not prompt else f"{prompt}\n\n{example_str}\n\nQuestion: {question}\nSQL:"
        return context
