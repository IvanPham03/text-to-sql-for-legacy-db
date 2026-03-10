# Pipeline Services Documentation

The Text-to-SQL system architecture is built around two primary pipelines:

1. **[Offline Pipeline](./offline/README.md)**: Responsible for knowledge preparation, schema extraction, and vector indexing.
2. **[Online Pipeline](./online/README.md)**: Handles the runtime flow from natural language query to SQL execution and verification.

## Architecture Overview

```mermaid
graph TD
    subgraph "Offline Pipeline"
        SE[Schema Extraction] --> SM[Schema Embedding]
        SM --> VI[Vector Indexing]
        EG[Example Generation] --> VI
    end

    subgraph "Online Pipeline"
        ID[Intent Detection] --> SR[Schema Retrieval]
        SR --> SG[SQL Generation]
        SG --> SV[SQL Validation]
        SV --> SX[SQL Execution]
        SX --> AG[Answer Generation]
    end

    VI -.-> SR
```

Each step in these pipelines is implemented as a modular service under `ivanpham_chatbot_assistant/services/pipelines/`.
