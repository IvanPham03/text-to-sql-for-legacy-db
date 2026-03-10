import os
from typing import Any, Dict

from ivanpham_chatbot_assistant.log import logger
from ivanpham_chatbot_assistant.services.llm.llm_service import LLMService
from ivanpham_chatbot_assistant.services.utils.prompt_renderer import PromptRenderer
from ivanpham_chatbot_assistant.settings import settings


class IntentDetectionService:
    """
    Classifier service to determine if a user query requires SQL generation.
    Acts as a lightweight router in the online pipeline.
    """

    def __init__(self, llm_service: LLMService | None = None):
        # Allow passing llm_service for dependency injection (e.g., in tests)
        if llm_service:
            self.llm_service = llm_service
        else:
            # Default production configuration
            llm_config = {
                "providers": [
                    {
                        "name": "openai",
                        "config": {
                            "api_key": settings.openai_api_key,
                            "model": "gpt-4o-mini",  # Lightweight and fast for routing
                        },
                    }
                ]
            }
            self.llm_service = LLMService(llm_config)

        # Initialize Prompt Renderer with local templates directory
        templates_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self.renderer = PromptRenderer(templates_dir)

    async def detect(self, question: str) -> Dict[str, Any]:
        """
        Classifies the user question intent and identifies applicable strategies.
        
        :param question: The natural language question from the user.
        :return: A dictionary containing:
            - status: "success" | "error"
            - strategies: List[int] (sorted by execution order)
            - requires_query: bool (True if strategies contain any non-zero code)
        """
        logger.info(f"Detecting intent/strategies for question: '{question}'")

        try:
            # 1. Render the intent detection prompt
            prompt = self.renderer.render(
                "intent_detection.jinja2",
                {"question": question}
            )

            # 2. Get classification from LLM
            # Use gpt-4o-mini for speed. Temperature 0 for deterministic output.
            response = await self.llm_service.generate(
                prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=20
            )

            # 3. Parse the output
            import json
            raw_output = response.get("text", "").strip()
            
            # Extract JSON array using regex if there's any conversational fluff
            import re
            match = re.search(r"(\[.*?\])", raw_output)
            if match:
                strategies = json.loads(match.group(1))
            else:
                # Fallback if no array found
                logger.warning(f"No JSON array found in intent output: '{raw_output}'")
                strategies = [1] # Default to Simple Lookup

            # 4. Enforce Production Execution Order
            # Order: 1 (lookup), 2 (aggregation), 5 (analytical), 3 (refinement), 4 (multi-step)
            order_map = {1: 1, 2: 2, 5: 3, 3: 4, 4: 5, 0: 99}
            
            # Filter valid codes and sort
            valid_strategies = [s for s in strategies if s in order_map]
            valid_strategies.sort(key=lambda x: order_map[x])

            # 5. Determine if query is needed
            requires_query = any(s != 0 for s in valid_strategies)
            
            # If [0] is present with other codes, but we need a query, remove 0
            if requires_query and 0 in valid_strategies:
                valid_strategies = [s for s in valid_strategies if s != 0]

            logger.info(f"Detected strategies: {valid_strategies}, requires_query: {requires_query}")
            
            return {
                "status": "success",
                "strategies": valid_strategies,
                "requires_query": requires_query
            }

        except Exception as e:
            logger.error(f"Error during intent detection: {e}. Falling back to default strategy.")
            return {
                "status": "error",
                "strategies": [1],
                "requires_query": True,
                "error": str(e)
            }
