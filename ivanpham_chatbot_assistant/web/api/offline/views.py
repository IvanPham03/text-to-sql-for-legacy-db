from fastapi import APIRouter, Request

from ivanpham_chatbot_assistant.services.pipelines.offline.extraction.schema_extraction_pipeline import (
    SchemaExtractionPipeline,
)
from ivanpham_chatbot_assistant.services.pipelines.offline.generate.pipeline import (
    DescriptionGenerationPipeline,
)
from ivanpham_chatbot_assistant.services.pipelines.offline.embedding.schema_sync_service import (
    SchemaSyncService,
)
from ivanpham_chatbot_assistant.web.schemas.base_response import BaseResponse
from ivanpham_chatbot_assistant.web.schemas.schema_index_request import SchemaIndexRequest
from ivanpham_chatbot_assistant.web.utils.response_builder import success_response

from .schemas import (
    DatasetAugmentationRequest,
    DescriptionGenerationRequest,
    EmbeddingRegenerationRequest,
    IndexRebuildRequest,
    PipelineStepRunRequest,
    SchemaExtractionRequest,
    SchemaSearchRequest,
)

router = APIRouter()

# --- SCHEMA MANAGEMENT ---

@router.post("/schema/index", response_model=BaseResponse)
async def index_schema(request: Request, schema_req: SchemaIndexRequest):
    """Indexes a source database schema including samples."""
    # Obtain session factory from request state, injected in lifespan
    session_factory = request.app.state.db_session_factory

    pipeline = SchemaExtractionPipeline(session_factory)
    await pipeline.run(schema_req)

    return success_response(message="Schema indexed successfully")

@router.post("/schema/extract", response_model=BaseResponse)
async def extract_schema(request: SchemaExtractionRequest):
    """Extract database schema and metadata."""
    # offline_pipeline_service.run_schema_extraction(request.database_name, request.force_refresh)
    return success_response(message="Schema extraction started")

@router.post("/schema/refresh", response_model=BaseResponse)
async def refresh_schema(request: SchemaExtractionRequest):
    """Refresh schema metadata."""
    return success_response(message="Schema refresh started")

@router.get("/schema/status", response_model=BaseResponse)
async def check_schema_status():
    """Check extraction status."""
    return success_response(data={"status": "completed"})

@router.post("/schema/descriptions/generate", response_model=BaseResponse)
async def generate_descriptions(request: Request, body: DescriptionGenerationRequest):
    """Generates semantic descriptions for tables and columns."""
    session_factory = request.app.state.db_session_factory
    pipeline = DescriptionGenerationPipeline(session_factory)

    await pipeline.run(
        table_names=body.table_names,
        limit=body.limit
    )

    return success_response(message="Semantic descriptions generated successfully")


@router.post("/schema/sync", response_model=BaseResponse)
async def sync_schema_full(request: Request) -> BaseResponse:
    """Performs full schema sync to vector store."""
    session_factory = request.app.state.db_session_factory
    service = SchemaSyncService(session_factory)
    stats = await service.full_sync()
    return success_response(
        message="Full schema sync completed",
        data=stats
    )

@router.post("/schema/sync/incremental", response_model=BaseResponse)
async def sync_schema_incremental(request: Request) -> BaseResponse:
    """Performs incremental schema sync to vector store."""
    session_factory = request.app.state.db_session_factory
    service = SchemaSyncService(session_factory)
    stats = await service.incremental_sync()
    return success_response(
        message="Incremental schema sync completed",
        data=stats
    )

@router.post("/schema/sync/cleanup", response_model=BaseResponse)
async def sync_schema_cleanup(request: Request) -> BaseResponse:
    """Cleans up stale schema vectors."""
    session_factory = request.app.state.db_session_factory
    service = SchemaSyncService(session_factory)
    stats = await service.cleanup_sync()
    return success_response(
        message="Schema cleanup sync completed",
        data=stats
    )

@router.post("/schema/search", response_model=BaseResponse)
async def search_schema(request: Request, body: SchemaSearchRequest) -> BaseResponse:
    """Search for schema elements by natural language."""
    session_factory = request.app.state.db_session_factory
    service = SchemaSyncService(session_factory)
    results = await service.search(body.question, body.limit)
    return success_response(
        data={"schemas": results}
    )


# --- EMBEDDING GENERATION ---

@router.post("/embedding/generate", response_model=BaseResponse)
async def generate_embeddings():
    """Generate embeddings for schema."""
    # offline_pipeline_service.generate_embeddings()
    return success_response(message="Embedding generation started")

@router.post("/embedding/regenerate", response_model=BaseResponse)
async def regenerate_embeddings(request: EmbeddingRegenerationRequest):
    """Regenerate embeddings if schema changed."""
    return success_response(message="Embedding regeneration started")

@router.get("/embedding/status", response_model=BaseResponse)
async def check_embedding_status():
    """Check embedding job status."""
    return success_response(data={"status": "completed"})


# --- EMBEDDING MANAGEMENT ---

@router.get("/embedding/tables", response_model=BaseResponse)
async def list_embedded_tables():
    """List tables that already have embeddings."""
    return success_response(data={"tables": ["users", "orders", "payments"]})


@router.get("/embedding/tables/{table_name}/columns", response_model=BaseResponse)
async def list_embedded_columns(table_name: str):
    """Return all columns that already have embeddings."""
    return success_response(data={
        "table": table_name,
        "columns": ["id", "user_id", "amount", "created_at"]
    })


@router.get("/embedding/tables/{table_name}/status", response_model=BaseResponse)
async def check_table_embedding_status(table_name: str):
    """Check table embedding status."""
    return success_response(data={
        "table": table_name,
        "embedded": True,
        "embedded_columns": 6,
        "total_columns": 8
    })


@router.get("/embedding/tables/{table_name}/columns/{column_name}", response_model=BaseResponse)
async def check_column_embedding_status(table_name: str, column_name: str):
    """Check column embedding status."""
    return success_response(data={
        "table": table_name,
        "column": column_name,
        "embedded": True
    })


@router.post("/embedding/tables/{table_name}/reembed", response_model=BaseResponse)
async def force_reembed_table(table_name: str):
    """Force regeneration of embeddings for a table."""
    return success_response(message=f"Forced re-embedding for table {table_name} started")


@router.post("/embedding/tables/{table_name}/columns/{column_name}/reembed", response_model=BaseResponse)
async def force_reembed_column(table_name: str, column_name: str):
    """Force regeneration of a single column embedding."""
    return success_response(message=f"Forced re-embedding for column {table_name}.{column_name} started")


@router.get("/embedding/jobs", response_model=BaseResponse)
async def list_embedding_jobs():
    """Return embedding job history."""
    return success_response(data={"jobs": [{"id": "emb-job-1", "table": "orders", "status": "completed"}]})


# --- DATASET GENERATION ---

@router.post("/dataset/generate", response_model=BaseResponse)
async def generate_dataset():
    """Generate SQL examples dataset."""
    # offline_pipeline_service.generate_dataset()
    return success_response(message="Dataset generation started")

@router.post("/dataset/augment", response_model=BaseResponse)
async def augment_dataset(request: DatasetAugmentationRequest):
    """Augment dataset using paraphrasing or synthetic generation."""
    return success_response(message="Dataset augmentation started")

@router.get("/dataset/status", response_model=BaseResponse)
async def check_dataset_status():
    """Check dataset generation status."""
    return success_response(data={"status": "completed"})


# --- VECTOR INDEX MANAGEMENT ---

@router.post("/index/build", response_model=BaseResponse)
async def build_index():
    """Build vector index."""
    # offline_pipeline_service.build_vector_index()
    return success_response(message="Vector index building started")

@router.post("/index/rebuild", response_model=BaseResponse)
async def rebuild_index(request: IndexRebuildRequest):
    """Rebuild the entire index."""
    return success_response(message="Vector index rebuild started")

@router.post("/index/refresh", response_model=BaseResponse)
async def refresh_index():
    """Incrementally update the index."""
    return success_response(message="Vector index refresh started")

@router.get("/index/status", response_model=BaseResponse)
async def check_index_status():
    """Check index status."""
    return success_response(data={"status": "completed"})


# --- PIPELINE ORCHESTRATION ---

@router.post("/pipeline/run", response_model=BaseResponse)
async def run_pipeline():
    """Run the entire offline pipeline."""
    # offline_pipeline_service.run_full_pipeline()
    return success_response(message="Full offline pipeline started")

@router.post("/pipeline/run-step", response_model=BaseResponse)
async def run_pipeline_step(request: PipelineStepRunRequest):
    """Run a specific pipeline step."""
    return success_response(message=f"Offline pipeline step '{request.step}' started")

@router.get("/pipeline/status", response_model=BaseResponse)
async def check_pipeline_status():
    """Check pipeline execution status."""
    return success_response(data={"status": "running", "current_step": "indexing"})


# --- MONITORING ---

@router.get("/jobs", response_model=BaseResponse)
async def list_jobs():
    """List all offline jobs."""
    return success_response(data={"jobs": [{"id": "job-1", "type": "schema_extraction", "status": "completed"}]})

@router.get("/jobs/{job_id}", response_model=BaseResponse)
async def get_job_status(job_id: str):
    """Get job status."""
    return success_response(data={"job_id": job_id, "status": "running"})

@router.delete("/jobs/{job_id}", response_model=BaseResponse)
async def cancel_job(job_id: str):
    """Cancel job."""
    return success_response(message=f"Job {job_id} cancelled")
