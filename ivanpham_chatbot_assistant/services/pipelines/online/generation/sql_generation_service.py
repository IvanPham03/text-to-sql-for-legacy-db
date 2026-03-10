import re
from typing import Any, Dict, List

from loguru import logger

from ivanpham_chatbot_assistant.services.llm.llm_service import LLMService
from ivanpham_chatbot_assistant.services.utils.prompt_renderer import PromptRenderer
from ivanpham_chatbot_assistant.settings import settings


class SqlGenerationService:
    """
    Service responsible for generating SQL queries from natural language questions
    and schema context using an LLM. This is Phase 1 of the generation system.
    """

    def __init__(self, llm_service: LLMService | None = None):
        # Allow passing llm_service for dependency injection
        if llm_service:
            self.llm_service = llm_service
        else:
            # Default production configuration for SQL generation
            llm_config = {
                "providers": [
                    {
                        "name": "openai",
                        "config": {
                            "api_key": settings.openai_api_key,
                            "model": "gpt-4o",  # High quality for Text-to-SQL
                        },
                    }
                ]
            }
            self.llm_service = LLMService(llm_config)

        # Initialize Prompt Renderer with local templates directory
        import os
        templates_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self.prompt_renderer = PromptRenderer(templates_dir)
        self.template_name = "sql_generation.jinja2"

    async def execute(
        self, question: str, schema_context: str, strategies: List[int] | None = None
    ) -> Dict[str, Any]:
        """
        Generates a SQL query for a given question and schema context.

        Args:
            question: The user's natural language question.
            schema_context: Database schema context.
            strategies: Optional list of strategy codes from intent detection.
        """
        logger.info(f"Generating SQL for question: '{question}' with strategies: {strategies}")

        # SCENARIO 1 — No schema retrieved: skip LLM to avoid hallucination
        if not schema_context or not schema_context.strip():
            logger.warning(
                "No schema context available for question. Skipping SQL generation to prevent hallucination.",
                question=question,
            )
            return {
                "status": "schema_missing",
                "message": "No relevant database schema was retrieved. SQL generation skipped.",
                "generated_sql": None,
            }

        try:
            # 1. Construct the prompt using Jinja2
            prompt = self.prompt_renderer.render(
                self.template_name,
                {
                    "question": question,
                    "schema_context": schema_context,
                    "strategies": strategies or [],
                },
            )

            # 2. Call LLM
            response = await self.llm_service.generate(
                prompt, model="gpt-4o", temperature=0.0
            )

            raw_sql = response.get("text", "").strip()

            # 3. Extract SQL (clean up markdown if present)
            clean_sql = self._extract_sql(raw_sql)

            # 4. Basic validation
            if not clean_sql or "SELECT" not in clean_sql.upper():
                logger.error("Generated SQL is invalid or empty.")
                return {
                    "status": "error",
                    "error": "Generated SQL missing SELECT statement or is empty.",
                    "generated_sql": clean_sql
                }

            logger.info("SQL generation successful.")
            return {
                "status": "success",
                "generated_sql": clean_sql
            }

        except Exception as e:
            logger.error(f"Error during SQL generation: {e}")
            return {
                "status": "error",
                "error": str(e),
                "generated_sql": None
            }

    def _extract_sql(self, text: str) -> str:
        """Removes markdown code blocks if present."""
        sql_match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if sql_match:
            return sql_match.group(1).strip()
        
        # Fallback to general code block
        generic_match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
        if generic_match:
            return generic_match.group(1).strip()
            
        return text.strip().rstrip(";") + ";" # Ensure single trailing semicolon
