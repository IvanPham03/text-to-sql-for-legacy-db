import time
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger

from ivanpham_chatbot_assistant.db.session import session_factory
from ivanpham_chatbot_assistant.services.pipelines.online.answer.answer_generation_service import (
    AnswerGenerationService,
)
from ivanpham_chatbot_assistant.services.pipelines.online.execution.sql_execution_service import (
    SqlExecutionService,
)
from ivanpham_chatbot_assistant.services.pipelines.online.generation.multi_step_planner_service import (
    MultiStepPlannerService,
)
from ivanpham_chatbot_assistant.services.pipelines.online.generation.result_refinement_service import (
    ResultRefinementService,
)
from ivanpham_chatbot_assistant.services.pipelines.online.generation.sql_correction_service import (
    SqlCorrectionService,
)
from ivanpham_chatbot_assistant.services.pipelines.online.generation.sql_generation_service import (
    SqlGenerationService,
)
from ivanpham_chatbot_assistant.services.pipelines.online.intent.intent_detection_service import (
    IntentDetectionService,
)
from ivanpham_chatbot_assistant.services.pipelines.online.retrieval.schema_retrieval_service import (
    SchemaRetrievalService,
)
from ivanpham_chatbot_assistant.services.pipelines.online.validation.sql_validation_service import (
    SqlValidationService,
)
from ivanpham_chatbot_assistant.settings import settings
from ivanpham_chatbot_assistant.web.schemas.query_schema import (
    AskRequest,
    AskResponseData,
)


class OnlinePipeline:
    """
    Orchestrator for the Online Text-to-SQL Pipeline.
    Coordinates all services from Intent Detection to Answer Generation.
    """

    def __init__(self):
        # Initialize services
        self.intent_service = IntentDetectionService()
        self.retrieval_service = SchemaRetrievalService()
        self.generation_service = SqlGenerationService()
        self.refinement_service = ResultRefinementService()
        self.planner_service = MultiStepPlannerService()
        self.validation_service = SqlValidationService(session_factory)

        # Source DB config from settings
        source_db_config = {
            "db_type": "sqlserver",  # Defaulting to SQL server based on .env drivers
            "host": settings.sql_source_host,
            "port": settings.sql_source_port,
            "user": settings.sql_source_user,
            "password": settings.sql_source_pass,
            "database": settings.sql_source_base,
            # Handle specific drivers if needed
            "driver": settings.sql_source_driver,
        }
        self.execution_service = SqlExecutionService(source_db_config)
        self.correction_service = SqlCorrectionService()
        self.answer_service = AnswerGenerationService()

    async def ask_question(self, request: AskRequest) -> AskResponseData:
        """
        Orchestrates the full pipeline flow.
        """
        question = request.question
        pipeline_t0 = time.perf_counter()
        logger.info("[pipeline] start", question=question)

        # 1. Intent Detection
        t0 = time.perf_counter()
        intent_result = await self.intent_service.detect(question)
        logger.debug(
            "[step] intent_detection",
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )

        if not intent_result.get("requires_query", True):
            logger.info(
                f"Intent detected as non-query (strategies: {intent_result.get('strategies')}). Generating direct answer."
            )
            t0 = time.perf_counter()
            answer_result = await self.answer_service.generate(question, [])
            logger.debug(
                "[step] answer_generation",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )
            logger.info(
                "[pipeline] done",
                total_ms=round((time.perf_counter() - pipeline_t0) * 1000, 2),
            )
            return AskResponseData(
                answer=answer_result.get("answer", "I'm not sure how to answer that."),
                sql=None,
                columns=None,
                rows=None,
                row_count=0,
                latency=round(time.perf_counter() - pipeline_t0, 4),
            )

        # 2. Schema Retrieval
        logger.info(
            f"Intent requires query (strategies: {intent_result.get('strategies')}). Retrieving schema context."
        )
        t0 = time.perf_counter()
        retrieval_result = await self.retrieval_service.execute(question)
        logger.debug(
            "[step] schema_retrieval",
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )
        retrieved_schema = retrieval_result.get("retrieved_schema", {})

        schema_context = ""
        database_name = retrieved_schema.get("database")
        if database_name:
            schema_context += f"Database: {database_name}\n\n"

        for table in retrieved_schema.get("tables", []):
            schema_context += f"Table: {table.get('table')}\nColumns:\n"
            for col in table.get("columns", []):
                col_type = col.get("type", "unknown")
                flags = []
                if col.get("pk"):
                    flags.append("PK")
                if col.get("fk"):
                    flags.append("FK")

                type_str = col_type if not flags else f"{col_type}, {', '.join(flags)}"
                schema_context += f"- {col.get('name')} ({type_str})\n"
            schema_context += "\n"

        # 3. SQL Generation
        t0 = time.perf_counter()
        strategies = intent_result.get("strategies", [])

        if 4 in strategies:
            logger.info(
                "Complex query detected. Applying Strategy 4: Multi-Step Planning."
            )
            gen_result = await self.planner_service.plan_and_execute(
                question, schema_context, None, None
            )
            generated_sql = gen_result.get("final_sql")
        else:
            gen_result = await self.generation_service.execute(
                question, schema_context, strategies=strategies
            )
            generated_sql = gen_result.get("generated_sql")

        logger.debug(
            "[step] sql_generation",
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )

        # SCENARIO 1 — No schema was retrieved
        if gen_result.get("status") == "schema_missing":
            msg = gen_result.get(
                "message",
                "No relevant database schema was retrieved. SQL generation skipped.",
            )
            logger.warning(
                "[pipeline] schema_missing – SQL generation skipped", question=question
            )
            logger.info(
                "[pipeline] done (schema_missing)",
                total_ms=round((time.perf_counter() - pipeline_t0) * 1000, 2),
            )
            return AskResponseData(
                answer=msg,
                sql=None,
                columns=None,
                rows=None,
                row_count=0,
                latency=round(time.perf_counter() - pipeline_t0, 4),
            )

        if not generated_sql:
            logger.info(
                "[pipeline] done (no SQL generated)",
                total_ms=round((time.perf_counter() - pipeline_t0) * 1000, 2),
            )
            return AskResponseData(
                answer="I'm sorry, I couldn't generate a SQL query for your request.",
                sql=None,
                columns=None,
                rows=None,
                row_count=0,
                latency=round(time.perf_counter() - pipeline_t0, 4),
            )
        logger.info("[pipeline] generated_sql", generated_sql)

        # 4 + 5. Self-Correction Loop (Validate → Execute → Correct → Retry)
        t0 = time.perf_counter()
        correction_result = await self.correction_service.run_correction_loop(
            question=question,
            schema_context=schema_context,
            initial_sql=generated_sql,
            validate_fn=self.validation_service.validate,
            execute_fn=self.execution_service.execute,
            strategies=intent_result.get("strategies"),
        )
        total_attempts = correction_result.get("total_attempts", 1)
        logger.debug(
            "[step] self_correction_loop",
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            total_attempts=total_attempts,
        )

        final_sql = correction_result.get("sql", generated_sql)

        if correction_result["status"] != "success":
            fail_msg = correction_result.get(
                "message",
                "The system could not generate a valid query. Please rephrase your question.",
            )
            logger.warning(
                "[pipeline] self-correction exhausted",
                total_attempts=total_attempts,
            )
            logger.info(
                "[pipeline] done (correction failed)",
                total_ms=round((time.perf_counter() - pipeline_t0) * 1000, 2),
            )
            return AskResponseData(
                answer=fail_msg,
                sql=final_sql,
                columns=None,
                rows=None,
                row_count=0,
                latency=round(time.perf_counter() - pipeline_t0, 4),
            )

        rows_data = correction_result.get("data", [])

        # 6. Answer Generation
        t0 = time.perf_counter()
        answer_result = await self.answer_service.generate(question, rows_data)
        logger.debug(
            "[step] answer_generation",
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )

        columns = list(rows_data[0].keys()) if rows_data else []
        rows = [list(row.values()) for row in rows_data]

        logger.info(
            "[pipeline] done",
            total_ms=round((time.perf_counter() - pipeline_t0) * 1000, 2),
            row_count=len(rows),
            sql_attempts=total_attempts,
        )
        return AskResponseData(
            sql=final_sql,
            columns=columns,
            rows=rows,
            answer=answer_result.get("answer", "No answer generated."),
            row_count=len(rows),
            latency=round(time.perf_counter() - pipeline_t0, 4),
        )

    async def ask_question_stream(
        self, request: AskRequest
    ) -> AsyncGenerator[dict[str, Any]]:
        """
        Streaming pipeline that yields event dicts progressively.
        Each dict is a SSE-compatible event payload.
        """
        question = request.question
        pipeline_t0 = time.perf_counter()
        logger.info("[stream] start", question=question)

        try:
            # 1. Intent Detection
            t0 = time.perf_counter()
            intent_result = await self.intent_service.detect(question)
            logger.debug(
                "[step] intent_detection",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )
            yield {
                "event": "intent_detected",
                "strategies": intent_result.get("strategies"),
            }

            if not intent_result.get("requires_query", True):
                logger.info(
                    f"Intent detected as non-query (strategies: {intent_result.get('strategies')})"
                )
                t0 = time.perf_counter()
                answer_result = await self.answer_service.generate(question, [])
                logger.debug(
                    "[step] answer_generation",
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                )
                logger.info(
                    "[stream] done",
                    total_ms=round((time.perf_counter() - pipeline_t0) * 1000, 2),
                )
                yield {
                    "event": "final_answer",
                    "answer": answer_result.get(
                        "answer", "I'm not sure how to answer that."
                    ),
                    "sql": None,
                    "columns": None,
                    "rows": None,
                    "latency": round(time.perf_counter() - pipeline_t0, 4),
                }
                return

            # 2. Schema Retrieval
            logger.info(
                f"Intent requires query (strategies: {intent_result.get('strategies')})"
            )
            t0 = time.perf_counter()
            retrieval_result = await self.retrieval_service.execute(question)
            retrieved_schema = retrieval_result.get("retrieved_schema", {})
            logger.debug(
                "[step] schema_retrieval",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )

            tables = retrieved_schema.get("tables", [])
            yield {"event": "schema_retrieved", "table_count": len(tables)}

            schema_context = ""
            database_name = retrieved_schema.get("database")
            if database_name:
                schema_context += f"Database: {database_name}\n\n"

            for table in tables:
                schema_context += f"Table: {table.get('table')}\nColumns:\n"
                for col in table.get("columns", []):
                    col_type = col.get("type", "unknown")
                    flags = []
                    if col.get("pk"):
                        flags.append("PK")
                    if col.get("fk"):
                        flags.append("FK")

                    type_str = (
                        col_type if not flags else f"{col_type}, {', '.join(flags)}"
                    )
                    schema_context += f"- {col.get('name')} ({type_str})\n"
                schema_context += "\n"

            # 3. SQL Generation
            t0 = time.perf_counter()
            strategies = intent_result.get("strategies", [])

            if 4 in strategies:
                logger.info(
                    "Complex query detected. Applying Strategy 4: Multi-Step Planning."
                )
                yield {
                    "event": "planning_steps",
                    "message": "Complex query detected. Decomposing into logical steps...",
                }
                gen_result = await self.planner_service.plan_and_execute(
                    question, schema_context, None, None
                )
                generated_sql = gen_result.get("final_sql")
            else:
                gen_result = await self.generation_service.execute(
                    question, schema_context, strategies=strategies
                )
                generated_sql = gen_result.get("generated_sql")

            logger.debug(
                "[step] sql_generation",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )

            # SCENARIO 1 — No schema retrieved
            if gen_result.get("status") == "schema_missing":
                msg = gen_result.get(
                    "message",
                    "No relevant database schema was retrieved. SQL generation skipped.",
                )
                logger.warning(
                    "[stream] schema_missing – SQL generation skipped",
                    question=question,
                )
                yield {"event": "schema_missing", "message": msg}
                return

            if not generated_sql:
                yield {"event": "error", "message": "SQL generation returned no query."}
                return

            yield {"event": "sql_generated", "sql": generated_sql}

            # 4 + 5. Self-Correction Loop
            t0 = time.perf_counter()
            correction_result = await self.correction_service.run_correction_loop(
                question=question,
                schema_context=schema_context,
                initial_sql=generated_sql,
                validate_fn=self.validation_service.validate,
                execute_fn=self.execution_service.execute,
            )
            total_attempts = correction_result.get("total_attempts", 1)
            logger.debug(
                "[step] self_correction_loop",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                total_attempts=total_attempts,
            )

            final_sql = correction_result.get("sql", generated_sql)

            if correction_result["status"] != "success":
                fail_msg = correction_result.get(
                    "message",
                    "The system could not generate a valid query. Please rephrase your question.",
                )
                logger.warning(
                    "[stream] self-correction exhausted", total_attempts=total_attempts
                )
                yield {
                    "event": "correction_failed",
                    "message": fail_msg,
                    "sql": final_sql,
                    "total_attempts": total_attempts,
                }
                return

            yield {
                "event": "sql_validated",
                "is_valid": True,
                "total_attempts": total_attempts,
                "sql": final_sql,
            }

            rows_data = correction_result.get("data", [])
            yield {"event": "query_executed", "row_count": len(rows_data)}

            # 6. Strategy 3: Result Refinement
            strategies = intent_result.get("strategies", [])
            final_data = correction_result.get("data", [])
            final_sql = correction_result.get("sql", generated_sql)

            if (
                3 in strategies
                and correction_result.get("status") == "success"
                and final_data
            ):
                columns = list(final_data[0].keys()) if final_data else []
                if await self.refinement_service.should_refine(final_data, columns):
                    logger.info("Result is 'thin'. Applying Strategy 3: Refinement.")
                    yield {
                        "event": "refining_result",
                        "message": "Result needs more context. Fetching descriptive fields...",
                    }

                    refine_result = await self.refinement_service.refine(
                        question, schema_context, final_sql, final_data
                    )
                    if refine_result.get("status") == "success":
                        refined_sql = refine_result["refined_sql"]
                        yield {"event": "refinement_sql_generated", "sql": refined_sql}

                        val_res = await self.validation_service.validate(refined_sql)
                        if val_res.get("is_valid"):
                            exec_res = await self.execution_service.execute(refined_sql)
                            if exec_res.get("status") == "success":
                                logger.info("Refinement query successful.")
                                final_data = exec_res.get("data", [])
                                final_sql = refined_sql
                                yield {"event": "refinement_completed"}
                            else:
                                logger.warning(
                                    f"Refinement query execution failed: {exec_res.get('message')}"
                                )
                        else:
                            logger.warning(
                                f"Refinement query validation failed: {val_res.get('reason')}"
                            )

            # 7. Answer Generation
            t0 = time.perf_counter()
            answer_result = await self.answer_service.generate(question, final_data)
            logger.debug(
                "[step] answer_generation",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )

            rows = final_data
            columns = list(rows[0].keys()) if rows else []

            logger.info(
                "[stream] done",
                total_ms=round((time.perf_counter() - pipeline_t0) * 1000, 2),
                row_count=len(rows),
            )
            yield {
                "event": "final_answer",
                "answer": answer_result.get("answer", "No answer generated."),
                "sql": final_sql,
                "columns": columns,
                "rows": rows,
                "latency": round(time.perf_counter() - pipeline_t0, 4),
            }

        except Exception as exc:
            logger.exception("Streaming pipeline encountered an unexpected error.")
            yield {"event": "error", "message": str(exc)}


# ---------------------------------------------------------------------------
# Singleton helpers — module-level entry points for the router
# ---------------------------------------------------------------------------

_pipeline: "OnlinePipeline | None" = None


def _get_pipeline() -> "OnlinePipeline":
    global _pipeline
    if _pipeline is None:
        _pipeline = OnlinePipeline()
    return _pipeline


async def ask_question(request: AskRequest) -> AskResponseData:
    """Blocking entry point for the online pipeline."""
    return await _get_pipeline().ask_question(request)


async def ask_question_stream(
    request: AskRequest,
) -> AsyncGenerator[dict[str, Any]]:
    """Streaming entry point for the online pipeline."""
    async for event in _get_pipeline().ask_question_stream(request):
        yield event


# Keep stubs for history/detail (not yet implemented)
async def get_history(limit: int = 20, offset: int = 0) -> list[Any]:
    return []


async def get_query_detail(query_id: str) -> Any:
    return None
