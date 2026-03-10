# Text-to-SQL Strategies Documentation

This document describes the multi-layered strategy system implemented in the Text-to-SQL pipeline. The system distinguishes between **High-Level Intent Strategies** (orchestration patterns) and **Low-Level Prompting Strategies** (specific techniques).

## 1. High-Level Intent Strategies

These strategies are detected in the initial **Intent Detection** phase and determine the high-level logic and orchestration of the pipeline.

| Code | Strategy | Focus | Behavior |
| :--- | :--- | :--- | :--- |
| **1** | **Lookup** | Specific Entities | Prioritizes human-readable names over IDs. |
| **2** | **Aggregation** | Metrics & Rankings | Enforces aggregate functions and proper T-SQL TOP clauses. |
| **5** | **Analytical** | Groupings | Focuses on multi-dimensional breakdowns and GROUP BY logic. |
| **3** | **Refinement** | Data Enrichment | Triggers a follow-up query if the initial results are "thin" (IDs only). |
| **4** | **Multi-Step** | Complex Reasoning | Uses a Reasoning-First Planner to solve questions in logical stages. |

**Execution Order**: To ensure stability, high-level strategies are applied in the sequence: `1 -> 2 -> 5 -> 3 -> 4`.

---

## 2. Low-Level Prompting Strategies

These are implementation-level techniques applied within specific services (primarily `SqlGenerationService`) to enhance LLM performance.

### 2.1 Prompting Techniques

| Strategy | Name | Description |
| :--- | :--- | :--- |
| **Few-Shot** | `few_shot` | Prepends relevant question-SQL pairs as examples to guide the model. |
| **Role Prompting** | `role_prompting` | Assigns an expert persona (e.g., Senior SQL Expert). |
| **Negative Prompting** | `negative_prompting` | Explicitly lists constraints and common pitfalls to avoid. |
| **Chain of Thought** | `chain_of_thought` | Encourages step-by-step reasoning before SQL output. |

### 2.2 Reasoning Patterns

| Strategy | Name | Description |
| :--- | :--- | :--- |
| **Self-Consistency** | `self_consistency` | Generates multiple paths and selects the most consistent result. |
| **Least-to-Most** | `least_to_most` | Decomposes questions into simpler sub-problems. |
| **Skeleton SQL** | `skeleton_sql` | Focuses on generating the SQL structure first. |

### 2.3 Schema Optimization

| Strategy | Name | Description |
| :--- | :--- | :--- |
| **Schema Linking** | `schema_linking` | Maps natural language entities to specific tables/columns. |
| **Schema Pruning** | `schema_pruning` | Removes irrelevant tables and columns to save tokens. |
| **Schema Description** | `schema_description` | Adds semantic comments/descriptions to schema context. |
| **Sample Value Schema**| `sample_value_schema` | Appends real data examples to help LLM understand distribution. |
| **Foreign Key Linking**| `foreign_key_linking` | Highlights relationships to improve JOIN accuracy. |

### 2.4 Validation & Feedback (Self-Correction)

These techniques power the **SqlCorrectionService**.

| Strategy | Name | Description |
| :--- | :--- | :--- |
| **SQL Validation** | `sql_validation` | Checks generated SQL for syntax and safety before execution. |
| **Execution Feedback** | `execution_feedback` | Feeds database errors back to the LLM for iterative refinement. |
| **Result Verification**| `result_verification` | Evaluates if the data returned logically answers the user intent. |

---

## Orchestration

The system uses a `StrategyManager` to combine these techniques. High-level intent strategies (e.g., **Multi-Step**) often utilize multiple low-level patterns (e.g., **Chain of Thought** + **Schema Linking**) to achieve their goal.
