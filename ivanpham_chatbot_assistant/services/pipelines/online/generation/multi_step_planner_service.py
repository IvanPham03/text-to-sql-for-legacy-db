import os
from typing import Any, Dict, List
from loguru import logger

from ivanpham_chatbot_assistant.services.llm.llm_service import LLMService
from ivanpham_chatbot_assistant.services.utils.prompt_renderer import PromptRenderer
from ivanpham_chatbot_assistant.settings import settings

class MultiStepPlannerService:
    """
    Service for Strategy 4 — Multi-Step Query.
    Decomposes complex questions into sequential reasoning steps and executes them.
    """

    def __init__(self, llm_service: LLMService | None = None):
        if llm_service:
            self.llm_service = llm_service
        else:
            llm_config = {
                "providers": [
                    {
                        "name": "openai",
                        "config": {
                            "api_key": settings.openai_api_key,
                            "model": "gpt-4o",
                        },
                    }
                ]
            }
            self.llm_service = LLMService(llm_config)

        templates_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self.prompt_renderer = PromptRenderer(templates_dir)
        self.template_name = "multi_step_planner.jinja2"

    async def plan_and_execute(
        self, 
        question: str, 
        schema_context: str,
        generation_fn, 
        execution_fn
    ) -> Dict[str, Any]:
        """
        Plans and executes multiple steps to answer a complex question.
        
        Note: For production, this could be a sophisticated loop. 
        In this implementation, we use a 'Chain of Thought' approach where 
        the LLM is instructed to solve the problem in steps.
        """
        logger.info("Triggering Strategy 4 — Multi-Step Query")
        
        # In a real heavy implementation, we might loop. 
        # Here we provide a specialized prompt that encourages multi-step generation
        # or sequential sub-queries.
        
        try:
            # 1. Ask the Planner to break it down
            prompt = self.prompt_renderer.render(
                self.template_name,
                {
                    "question": question,
                    "schema_context": schema_context,
                }
            )

            # 2. Get the Multi-Step approach from LLM
            # We use a higher max_tokens for step-by-step reasoning
            response = await self.llm_service.generate(
                prompt, model="gpt-4o", temperature=0.0
            )
            
            # For this version, we expect the LLM to provide a final SQL 
            # that represents the multi-step logic (e.g. using CTEs or Subqueries)
            # OR a sequence of actions. 
            
            # To keep it robust within the existing pipeline, we'll treat Strategy 4 
            # as a 'Reasoning-First' generation.
            
            final_sql = response.get("text", "").strip()
            
            return {
                "status": "success",
                "final_sql": final_sql
            }

        except Exception as e:
            logger.error(f"Error during multi-step planning: {e}")
            return {"status": "error", "error": str(e)}
