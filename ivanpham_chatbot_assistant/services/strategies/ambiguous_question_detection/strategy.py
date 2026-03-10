from typing import Any, Dict
from ..base import BaseStrategy

class AmbiguousQuestionDetectionStrategy(BaseStrategy):
    """
    Strategy to detect and clarify ambiguous questions.
    """
    name = "ambiguous_question_detection"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        instruction = (
            "Ambiguity Check: If the user's question is unclear or maps to multiple "
            "possible schema interpretations, ask for clarification instead of guessing."
        )
        context["prompt"] = f"{prompt}\n\n{instruction}" if prompt else instruction
        return context
