# Offline Pipeline Services

The Offline Pipeline prepares the system's "knowledge base" to enable efficient and accurate SQL generation during runtime.

## Services

### 1. Schema Extraction Service
- **Purpose**: Connects to source databases and extracts structural metadata (tables, columns, types, constraints).
- **Output**: Detailed JSON schema representation.

### 2. Schema Embedding & Sync Service
- **Granularity**: Implements **Column-Level Granularity**, indexing each column with a description as a separate vector for precise retrieval.
- **Deterministic IDs**: Vector IDs are stable and generated from the schema hierarchy (`db.schema.table.column`), ensuring idempotency.
- **Incremental Sync**: Uses multi-field checksums (name, type, sample values, and descriptions) to intelligently update only modified metadata.
- **Deletion Sync**: Automatically removes points from Qdrant if their corresponding columns or descriptions are deleted from the database.
- **Output**: Optimized, versioned column-level vectors in Qdrant.

### 3. SQL Example Generation Service
- **Purpose**: Generates synthetic or curated NL-SQL pairs to serve as few-shot examples for the LLM.
- **Output**: A collection of high-quality examples.

### 4. Vector Indexing Service
- **Purpose**: Interfaces with a vector database to store and index embeddings and examples.
- **Goal**: Enable rapid retrieval of relevant context during the Online phase.
