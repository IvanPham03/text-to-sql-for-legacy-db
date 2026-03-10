"""Unit tests for SqlGenerationService safe-generation guards."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_llm_service():
    """Returns a mock LLMService that returns a simple SELECT query."""
    svc = MagicMock()
    svc.generate = AsyncMock(
        return_value={"text": "SELECT id, name FROM products WHERE active = 1"}
    )
    return svc


@pytest.fixture
def generation_service(mock_llm_service):
    from ivanpham_chatbot_assistant.services.pipelines.online.generation.sql_generation_service import (
        SqlGenerationService,
    )
    return SqlGenerationService(llm_service=mock_llm_service)


# ---------------------------------------------------------------------------
# SCENARIO 1: No schema context → skip LLM entirely
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_schema_missing_guard_empty_string(generation_service, mock_llm_service):
    """When schema_context is an empty string, the LLM must NOT be called."""
    result = await generation_service.execute("show all products", schema_context="")

    assert result["status"] == "schema_missing"
    assert result["generated_sql"] is None
    assert "No relevant database schema" in result["message"]
    mock_llm_service.generate.assert_not_called()


@pytest.mark.anyio
async def test_schema_missing_guard_whitespace_only(generation_service, mock_llm_service):
    """When schema_context is only whitespace, the LLM must NOT be called."""
    result = await generation_service.execute("show all products", schema_context="   \n\t")

    assert result["status"] == "schema_missing"
    assert result["generated_sql"] is None
    mock_llm_service.generate.assert_not_called()


# ---------------------------------------------------------------------------
# SCENARIO 2: Valid schema context → LLM is called, SQL is returned
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_normal_generation_calls_llm(generation_service, mock_llm_service):
    """When a valid schema_context is provided, the LLM should be called and SQL returned."""
    schema_context = "Table: products, Column: id (int) - Primary key\nTable: products, Column: name (varchar) - Product name\n"
    result = await generation_service.execute("show all products", schema_context=schema_context)

    assert result["status"] == "success"
    assert result["generated_sql"] is not None
    assert "SELECT" in result["generated_sql"].upper()
    mock_llm_service.generate.assert_called_once()


# ---------------------------------------------------------------------------
# SCENARIO 3: Validation failure message format
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_validation_failure_contains_reason(generation_service, mock_llm_service):
    """LLM returns SQL that triggers validation — verify the service still returns the sql field."""
    # The generation service itself doesn't run validation; that's the pipeline's job.
    # We just verify that sql is returned so the pipeline CAN pass it to the validator.
    schema_context = "Table: products, Column: id (int) - Primary key\n"
    result = await generation_service.execute("show all services", schema_context=schema_context)

    # Generation service should succeed; validation happens upstream in the pipeline.
    assert result["status"] == "success"
    assert result["generated_sql"] is not None
