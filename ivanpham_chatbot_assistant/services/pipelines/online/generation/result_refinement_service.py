import os
from typing import Any, Dict, List
from loguru import logger

from ivanpham_chatbot_assistant.services.llm.llm_service import LLMService
from ivanpham_chatbot_assistant.services.utils.prompt_renderer import PromptRenderer
from ivanpham_chatbot_assistant.settings import settings

class ResultRefinementService:
    """
    Service for Strategy 3 — Refinement.
    Improves query results by retrieving additional context if the initial result is 'thin'.
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
        self.template_name = "result_refinement.jinja2"

    async def should_refine(self, data: List[Dict[str, Any]], columns: List[str]) -> bool:
        """
        Determines if the result needs refinement.
        Refinement is needed if the result has very few columns or appears to be just identifiers.
        """
        if not data:
            return False
            
        # If we only have 1 or 2 columns, it's likely 'thin'
        if len(columns) <= 2:
            # Check if columns look like IDs or codes
            id_keywords = ["id", "code", "phone", "email", "key"]
            is_id_only = all(any(k in col.lower() for k in id_keywords) for col in columns)
            if is_id_only:
                return True
                
        return False

    async def refine(
        self, 
        question: str, 
        schema_context: str, 
        initial_sql: str, 
        initial_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates and executes a refinement query to add context to the initial results.
        """
        logger.info("Triggering Strategy 3 — Result Refinement")
        
        try:
            # 1. Generate Refinement Instructions/SQL
            prompt = self.prompt_renderer.render(
                self.template_name,
                {
                    "question": question,
                    "schema_context": schema_context,
                    "initial_sql": initial_sql,
                    "initial_data": initial_data[:5], # Send a sample
                }
            )

            response = await self.llm_service.generate(
                prompt, model="gpt-4o", temperature=0.0
            )
            
            # The LLM should return a NEW SQL query that is richer
            refined_sql = response.get("text", "").strip()
            
            return {
                "status": "success",
                "refined_sql": refined_sql
            }

        except Exception as e:
            logger.error(f"Error during result refinement: {e}")
            return {"status": "error", "error": str(e)}
