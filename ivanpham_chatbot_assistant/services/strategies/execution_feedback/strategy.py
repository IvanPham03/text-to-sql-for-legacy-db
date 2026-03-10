from typing import Any, Dict
from ..base import BaseStrategy

class ExecutionFeedbackStrategy(BaseStrategy):
    """
    Strategy that incorporates database execution errors back into the prompt.
    """
    name = "execution_feedback"

    def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = context.get("prompt", "")
        error = context.get("execution_error")
        
        if error:
            feedback = f"The previous SQL attempt failed with error: {error}. Please fix this error and try again."
            context["prompt"] = f"{prompt}\n\n{feedback}" if prompt else feedback
            
        return context
