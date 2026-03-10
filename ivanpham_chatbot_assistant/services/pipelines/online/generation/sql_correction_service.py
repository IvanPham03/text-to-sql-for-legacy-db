import os
import re
import time
from typing import Any, Dict, List, Optional

from loguru import logger

from ivanpham_chatbot_assistant.services.llm.llm_service import LLMService
from ivanpham_chatbot_assistant.services.utils.prompt_renderer import PromptRenderer
from ivanpham_chatbot_assistant.settings import settings


class SqlCorrectionService:
    """
    Self-correction service for Text-to-SQL generation.

    When a generated SQL query fails validation or execution, this service
    feeds the error back to the LLM and asks it to produce a corrected query.
    It supports up to MAX_ATTEMPTS retries before giving up.
    """

    MAX_ATTEMPTS = 3

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
        self.correction_template = "sql_correction.jinja2"

    async def correct(
        self,
        question: str,
        schema_context: str,
        failed_sql: str,
        error_message: str,
        strategies: List[int] | None = None,
    ) -> Dict[str, Any]:
        """
        Ask the LLM to correct a failed SQL query.

        Args:
            question: The original user question.
            schema_context: The database schema provided to the LLM.
            failed_sql: The SQL query that failed.
            error_message: The exact error from validation or execution.
            strategies: Optional list of strategy codes.

        Returns:
            Dict with status, corrected_sql, and metadata.
        """
        logger.info(
            "Requesting SQL correction from LLM.",
            error_preview=error_message[:200],
        )

        try:
            prompt = self.prompt_renderer.render(
                self.correction_template,
                {
                    "question": question,
                    "schema_context": schema_context,
                    "previous_sql": failed_sql,
                    "error_message": error_message,
                    "strategies": strategies or [],
                },
            )

            response = await self.llm_service.generate(
                prompt,
                model="gpt-4o",
                temperature=0.0,
            )

            raw_sql = response.get("text", "").strip()
            clean_sql = self._extract_sql(raw_sql)

            if not clean_sql or "SELECT" not in clean_sql.upper():
                logger.warning("LLM correction returned invalid SQL.")
                return {
                    "status": "error",
                    "corrected_sql": None,
                    "error": "Corrected SQL is empty or missing SELECT.",
                }

            logger.info("SQL correction received from LLM.")
            return {
                "status": "success",
                "corrected_sql": clean_sql,
            }

        except Exception as e:
            logger.error(f"SQL correction LLM call failed: {e}")
            return {
                "status": "error",
                "corrected_sql": None,
                "error": str(e),
            }

    async def run_correction_loop(
        self,
        question: str,
        schema_context: str,
        initial_sql: str,
        validate_fn,
        execute_fn,
        strategies: List[int] | None = None,
    ) -> Dict[str, Any]:
        """
        Run the full self-correction loop: validate → execute → correct → retry.

        Args:
            question: The original user question.
            schema_context: Schema context used for generation.
            initial_sql: The first generated SQL query.
            validate_fn: Async callable(sql) → validation result dict.
            execute_fn: Async callable(sql) → execution result dict.
            strategies: Optional list of strategy codes.

        Returns:
            Dict with final status, sql, data, and attempt history.
        """
        current_sql = initial_sql
        attempts: List[Dict[str, Any]] = []

        for attempt_num in range(1, self.MAX_ATTEMPTS + 1):
            t0 = time.perf_counter()
            attempt_record: Dict[str, Any] = {
                "attempt": attempt_num,
                "sql": current_sql,
            }

            logger.info(
                f"[self-correct] attempt {attempt_num}/{self.MAX_ATTEMPTS}",
                sql_preview=current_sql[:120],
            )

            # --- Step 1: Validate ---
            validation_result = await validate_fn(current_sql)
            is_valid = validation_result.get("is_valid", False)
            attempt_record["validation"] = validation_result

            if not is_valid:
                error_msg = validation_result.get("reason", "Unknown validation error.")
                attempt_record["error_source"] = "validation"
                attempt_record["error_message"] = error_msg
                attempt_record["latency_ms"] = round(
                    (time.perf_counter() - t0) * 1000, 2
                )
                attempts.append(attempt_record)

                logger.warning(
                    f"[self-correct] attempt {attempt_num} failed at validation.",
                    reason=error_msg,
                )

                # Try correction if not last attempt
                if attempt_num < self.MAX_ATTEMPTS:
                    correction = await self.correct(
                        question, schema_context, current_sql, error_msg, strategies=strategies
                    )
                    if correction["status"] == "success" and correction["corrected_sql"]:
                        current_sql = correction["corrected_sql"]
                    else:
                        # LLM correction itself failed, stop early
                        logger.error("[self-correct] LLM correction failed. Stopping.")
                        break
                continue

            # --- Step 2: Execute ---
            exec_result = await execute_fn(current_sql)
            attempt_record["execution"] = {
                "status": exec_result.get("status"),
            }

            if exec_result.get("status") == "error":
                error_msg = exec_result.get("message", "Unknown execution error.")
                attempt_record["error_source"] = "execution"
                attempt_record["error_message"] = error_msg
                attempt_record["latency_ms"] = round(
                    (time.perf_counter() - t0) * 1000, 2
                )
                attempts.append(attempt_record)

                logger.warning(
                    f"[self-correct] attempt {attempt_num} failed at execution.",
                    error=error_msg,
                )

                # Try correction if not last attempt
                if attempt_num < self.MAX_ATTEMPTS:
                    correction = await self.correct(
                        question, schema_context, current_sql, error_msg, strategies=strategies
                    )
                    if correction["status"] == "success" and correction["corrected_sql"]:
                        current_sql = correction["corrected_sql"]
                    else:
                        logger.error("[self-correct] LLM correction failed. Stopping.")
                        break
                continue

            # --- Success ---
            attempt_record["latency_ms"] = round(
                (time.perf_counter() - t0) * 1000, 2
            )
            attempts.append(attempt_record)

            logger.info(
                f"[self-correct] attempt {attempt_num} succeeded.",
                latency_ms=attempt_record["latency_ms"],
            )

            return {
                "status": "success",
                "sql": current_sql,
                "data": exec_result.get("data", []),
                "attempts": attempts,
                "total_attempts": attempt_num,
            }

        # --- All attempts exhausted ---
        logger.error(
            f"[self-correct] all {self.MAX_ATTEMPTS} attempts failed.",
        )
        return {
            "status": "error",
            "sql": current_sql,
            "data": [],
            "attempts": attempts,
            "total_attempts": len(attempts),
            "message": "The system could not generate a valid query after multiple attempts. Please try rephrasing your question.",
        }

    @staticmethod
    def _extract_sql(text: str) -> str:
        """Removes markdown code blocks if present."""
        sql_match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if sql_match:
            return sql_match.group(1).strip()

        generic_match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
        if generic_match:
            return generic_match.group(1).strip()

        return text.strip().rstrip(";") + ";"
