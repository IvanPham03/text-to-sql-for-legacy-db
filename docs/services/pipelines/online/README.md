# Online Pipeline Services

The Online Pipeline handles user natural language questions in real-time. It uses a centralized **Orchestrator** to coordinate multiple modular services—from intent detection to final natural language answer generation, supported by a robust self-correction mechanism and multi-strategy reasoning.

## Orchestration Flow

The `OnlinePipeline` orchestrator manages the following sequential flow:

1.  **Intent Detection**: Determines if the question requires database access and identifies applicable query strategies.
    - If `requires_query=False` (conversational), it skips directly to **Answer Generation**.
    - If `requires_query=True`, it proceeds with the Text-to-SQL logic using a specific execution order for strategies.
2.  **Schema Retrieval**: Fetches relevant tables and columns from the vector store to build the context.
3.  **SQL Generation / Planning**:
    - **Standard Generation**: Used for basic queries (Lookup, Aggregation, Analytical).
    - **Multi-Step Planning**: Triggered for complex questions (Strategy 4) to decompose reasoning steps.
4.  **Self-Correction Loop**: Validates and executes the SQL, attempting automatic correction (up to 3 times) if errors occur.
5.  **Result Refinement**: (Strategy 3) Checks for "thin" results and fetches descriptive business context if needed.
6.  **Answer Generation**: Synthesizes the final response for the user based on the (potentially refined) results.

### Latency Instrumentation

Every step in the pipeline is instrumented with `time.perf_counter()` to measure execution latency in milliseconds. This enables real-time performance monitoring and identification of bottlenecks. Latency is logged for each step and included in the API response.

## Core Services

### 1. Intent Detection Service
- **Purpose**: Classifies user intent and assigns high-level **Strategy Codes** to guide the pipeline.
- **Strategies**:
  - `1 — Lookup`: Specific entity search (phone, ID, email).
  - `2 — Aggregation`: Totals, counts, rankings.
  - `5 — Analytical`: Grouped insights and breakdowns.
  - `3 — Refinement`: Enforces fetching descriptive labels for "thin" data.
  - `4 — Multi-Step`: Complex reasoning requiring sequential logic.
- **Execution Order**: Ensuring production stability, strategies are processed in the order: `1 -> 2 -> 5 -> 3 -> 4`.

### 2. SQL Generation & Planning
- **SqlGenerationService**: Strategy-aware generator that injects specific rules for Lookup, Aggregation, and Analytical queries.
- **MultiStepPlannerService**: Handles Strategy 4. It uses a "Reasoning-First" approach to break down complex questions before generating the final SQL (often using CTEs).

### 3. Self-Correction Service
- **Purpose**: Automatically fixes SQL syntax, schema references, or execution errors.
- **Logic**:
  - Validates SQL via `SqlValidationService`.
  - Executes SQL and captures DB errors.
  - Feeds errors back to the LLM (up to **3 attempts**) with the original question and schema context.
- **Strategy Awareness**: The correction prompt is also strategy-aware, ensuring the LLM maintains the intended query structure during fixes.

### 4. Result Refinement Service (Strategy 3)
- **Purpose**: Prevents "thin" answers (e.g., returning only a phone number or ID).
- **Detection**: Automatically identifies if result columns are primarily identifiers.
- **Outcome**: Triggers a secondary "Refinement Query" to join master data and fetch names, statuses, or categories for a richer user response.

### 5. SQL Validation Service
- **Read-Only Enforcement**: Blocks DDL/DML.
- **Metadata Verification**: Batch-validates table and column existence against the registry.
- **T-SQL Enforcement**: Ensures compatibility with Microsoft SQL Server (e.g., `TOP` vs `LIMIT`).

### 6. Answer Generation Service
- **Multilingual Support**: Detects and responds in Vietnamese, English, Chinese, Japanese, or Korean.
- **Value Normalization**: Converts internal system codes into business-friendly labels via `VALUE_NORMALIZATION_MAP`.
- **KPI Focused**: Summarizes trends and highlights anomalies found in the data.

## SQL Best Practices & Constraints

The `SqlGenerationService` and `SqlCorrectionService` enforce several production-grade rules to ensure security and execution stability:

1. **Set Operation Rules**: When using `UNION`, `UNION ALL`, `INTERSECT`, or `EXCEPT`:
   - `SELECT *` is strictly forbidden.
   - All columns must be explicitly selected and named.
   - Column types and counts must be perfectly matched across segments.
2. **T-SQL Compatibility**: Automatically adapts SQL for Microsoft SQL Server, specifically for pagination and sampling.
3. **Identifier Safety**: All identifiers are validated against the database metadata before execution.
4. **Row Limits**: Global `TOP 100` enforcement to prevent result set explosion.

## Changelog

### 2026-03-09

**Strategy-Aware Pipeline Implementation**
- Refactored `OnlinePipeline` to support **multi-strategy orchestration**.
- Upgraded `IntentDetectionService` to return specific strategy codes (`0-5`).
- Implemented `ResultRefinementService` for automated context enrichment.
- Implemented `MultiStepPlannerService` for complex SQL reasoning.
- Added strategy-specific rules to `sql_generation.jinja2` and `sql_correction.jinja2`.

**Self-Correction System**
- Implemented `SqlCorrectionService` with a 3-attempt retry loop.
- Integrated execution feedback into the correction prompt.

**Latency & Performance**
- Added per-step latency measurement across all pipeline services.
- Latency data is now propagated to the final `AskResponseData`.
