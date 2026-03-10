# Text-to-SQL for Legacy Relational Databases 🤖📊

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.122+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open-source system designed to enable **natural language querying for legacy relational databases**. Stop writing complex SQL manually and start asking questions in plain English.

## 🌟 Overview

This project is tailored for enterprise environments with large, complex, or poorly documented legacy database schemas. It provides a **rough base (base thô)** for building natural language interfaces, leveraging **RAG (Retrieval-Augmented Generation)** with **Qdrant** for vector storage and **LangChain** for strategic pipeline orchestration.

The system is designed to:
1.  **Understand Intent**: Classify user requests and identify relevant data domains.
2.  **Semantic Retrieval**: Use vector search (Qdrant) to find relevant tables and columns among thousands.
3.  **Intelligent Generation**: Construct optimized SQL queries using state-of-the-art LLMs (OpenAI, Anthropic).
4.  **Safe Execution**: Validate and execute queries against your legacy systems.

> [!NOTE]
> This repository is a **foundational base**. It is designed to be forked and extended for specific enterprise needs or more advanced RAG strategies.

---

## ✨ Key Features

- 🗣️ **Natural Language to SQL**: Accurate conversion of complex business questions.
- 🏗️ **Legacy Support**: Optimized for MS SQL Server, PostgreSQL, and MySQL.
- 🔍 **Semantic Schema Retrieval**: Efficiently handles huge schemas using vector embeddings and Qdrant.
- 🛠️ **LangChain Strategies**: Extensible pipeline using modular generation tactics.
- 🛡️ **Query Validation**: Built-in safety checks before database execution.
- 🚀 **Production-Ready**: High-performance FastAPI backend with telemetry and monitoring.

---

## 🏗️ Architecture

### Basic Pipeline Flow
The core workflow follows a retrieval-augmented execution path:

```mermaid
graph TD
    A[User Question] --> B[Embedding]
    B --> C[Vector Search - Qdrant]
    C --> D[Relevant Schema / Docs]
    D --> E[Prompt Construction]
    E --> F[Generate SQL - LLM]
    F --> G[Execute DB]
    G --> H[Return Answer]
```

### Advanced Strategies
For more complex scenarios, the architecture can be extended with multi-stage RAG:

```mermaid
graph LR
    subgraph RAG Layers
    S[RAG for Schema]
    D[RAG for Documentation]
    end
    
    Q[Question] --> S
    Q --> D
    S --> G[SQL Generation]
    D --> G
    G --> A[Answer Synthesis]
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (highly recommended for dependency management)
- Docker & Docker Compose

### Local Setup (using `uv`)

```bash
# Clone the repository
git clone https://github.com/IvanPham03/text-to-sql-legacy.git
cd text-to-sql-legacy

# Sync dependencies
uv sync --locked

# Run the server
uv run -m ivanpham_chatbot_assistant
```
The API will be available at `http://localhost:8000`. Explore the Swagger docs at `/api/docs`.

### Docker Setup

```bash
docker-compose up --build
```

---

## ⚙️ Configuration

Configure the application using environment variables or a `.env` file in the root.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `IVANPHAM_CHATBOT_ASSISTANT_PORT` | Application port | `8000` |
| `IVANPHAM_CHATBOT_ASSISTANT_DB_HOST` | Database host | `localhost` |
| `OPENAI_API_KEY` | Your OpenAI API Key | - |
| `QDRANT_HOST` | Vector database host | `localhost` |

*Refer to `ivanpham_chatbot_assistant/settings.py` for a full list of configurable parameters.*

---

## 🛠️ Development

### Project Structure
```text
ivanpham_chatbot_assistant
├── db/          # Database models, DAO, and migrations
├── services/    # Core logic: Extraction, Embedding, Generation
├── web/         # FastAPI application, API routes, and lifespan
└── tests/       # Pytest suite
```

### Database Migrations
We use Alembic for schema management:
```bash
uv run alembic upgrade head
```

### Running Tests
```bash
pytest -vv .
```

### Pre-commit Hooks
Ensure code quality before committing:
```bash
pre-commit install
```

---

## 📝 Example

**User Question:**  
> "Who are the top 10 customers with the highest total orders in the last 6 months?"

**Generated SQL (MS SQL):**
```sql
SELECT TOP 10 c.CustomerName, SUM(o.TotalAmount) AS TotalSpent
FROM Orders o
JOIN Customers c ON o.CustomerId = c.Id
WHERE o.OrderDate >= DATEADD(month, -6, GETDATE())
GROUP BY c.CustomerName
ORDER BY TotalSpent DESC
```

---

## 🤝 Contributions

Contributions are what make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.