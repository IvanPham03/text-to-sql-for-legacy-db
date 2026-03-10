import json
import os
import re
from typing import Any

from loguru import logger

from ivanpham_chatbot_assistant.services.llm.llm_service import LLMService
from ivanpham_chatbot_assistant.services.utils.prompt_renderer import PromptRenderer
from ivanpham_chatbot_assistant.settings import settings


class AnswerGenerationService:
    """
    Final step in the Text-to-SQL pipeline.
    Translates structured SQL results into natural language answers.
    """

    MAX_ROWS_FOR_LLM = 20

    # Value Normalization Map: raw database codes → human-readable labels
    # This reduces LLM hallucination by providing pre-cleaned values.
    # Add entries as needed for your domain.
    VALUE_NORMALIZATION_MAP: dict[str, str] = {
        "CAR FOR RENT": "Car rental service",
        "BUSINESS TRAVEL SERVICE": "Business travel service",
        "AIR TICKET": "Air ticket booking",
        "CRUISE": "Cruise tour",
        "HOTEL BOOKING": "Hotel booking service",
        "VISA SERVICE": "Visa processing service",
        "TRAVEL INSURANCE": "Travel insurance service",
    }

    def __init__(self, llm_service: LLMService | None = None):
        # Default production configuration for Answer Generation
        if llm_service:
            self.llm_service = llm_service
        else:
            llm_config = {
                "providers": [
                    {
                        "name": "openai",
                        "config": {
                            "api_key": settings.openai_api_key,
                            "model": "gpt-4o-mini",  # Fast & cost-effective for summarization
                        },
                    }
                ]
            }
            self.llm_service = LLMService(llm_config)

        # Initialize Prompt Renderer with local templates directory
        templates_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self.prompt_renderer = PromptRenderer(templates_dir)
        self.template_name = "answer_generation.jinja2"

    @staticmethod
    def _detect_language(text: str) -> str:
        """Simple heuristic to detect the language of the user's question."""
        # Vietnamese detection: look for common diacritical characters
        if re.search(
            r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
            text,
            re.IGNORECASE,
        ):
            return "Vietnamese"
        # Japanese detection: Hiragana, Katakana, or CJK
        if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", text):
            return "Japanese"
        # Korean detection: Hangul
        if re.search(r"[\uac00-\ud7af\u1100-\u11ff]", text):
            return "Korean"
        # Chinese detection: CJK without Japanese kana
        if re.search(r"[\u4e00-\u9fff]", text) and not re.search(
            r"[\u3040-\u30ff]", text
        ):
            return "Chinese"
        return "English"

    def _normalize_values(
        self, sql_result: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Pre-process raw database values into human-readable labels.

        Applies two transformations:
        1. Dictionary lookup: exact match against VALUE_NORMALIZATION_MAP.
        2. Title-case fallback: if a string value is ALL CAPS and not in the map,
           convert it to title case for readability.
        """
        if not self.VALUE_NORMALIZATION_MAP and not sql_result:
            return sql_result

        normalized = []
        for row in sql_result:
            new_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    upper_val = value.strip().upper()
                    if upper_val in self.VALUE_NORMALIZATION_MAP:
                        new_row[key] = self.VALUE_NORMALIZATION_MAP[upper_val]
                    elif (
                        value == value.upper()
                        and len(value) > 2
                        and value.isalpha() is False
                    ):
                        # ALL-CAPS string not in map → title-case fallback
                        new_row[key] = value.strip().title()
                    else:
                        new_row[key] = value
                else:
                    new_row[key] = value
            normalized.append(new_row)
        return normalized

    async def generate(
        self,
        question: str,
        sql_result: list[dict[str, Any]],
        language: str | None = None,
    ) -> dict[str, Any]:
        """
        Generates a natural language answer from a question and its SQL results.
        """
        logger.info(f"Generating answer for question: '{question}'")

        # Auto-detect language if not provided
        if not language:
            language = self._detect_language(question)
            logger.debug(f"Auto-detected language: {language}")

        try:
            # 1. Handle empty results proactively
            if not sql_result:
                logger.info("SQL result is empty. Returning default empty message.")
                return {
                    "status": "success",
                    "answer": "No data was found matching your request.",
                }

            # 2. Value Normalization (code → readable label)
            normalized_result = self._normalize_values(sql_result)

            # 3. Truncate result for LLM context optimization
            summarized = False
            if len(normalized_result) > self.MAX_ROWS_FOR_LLM:
                truncated_result = normalized_result[: self.MAX_ROWS_FOR_LLM]
                summarized = True
                result_str = (
                    json.dumps(truncated_result, indent=2, ensure_ascii=False)
                    + f"\n\n(Note: Showing first {self.MAX_ROWS_FOR_LLM} of {len(sql_result)} total rows)"
                )
            else:
                result_str = json.dumps(normalized_result, indent=2, ensure_ascii=False)

            # 3. Render prompt
            prompt = self.prompt_renderer.render(
                self.template_name,
                {"question": question, "sql_result": result_str, "language": language},
            )

            # 4. Get response from LLM
            response = await self.llm_service.generate(
                prompt,
                temperature=0.3,  # Slight creativity for natural phrasing
            )

            answer = response.get("text", "").strip()

            logger.info("Answer generation successful.")
            return {"status": "success", "answer": answer, "is_summarized": summarized}

        except Exception as e:
            logger.error(f"Error during answer generation: {e}")
            return {
                "status": "error",
                "error": str(e),
                "answer": "Sorry, I encountered an error while processing the data results.",
            }
