
from pydantic import BaseModel


class SchemaExtractionRequest(BaseModel):
    database_name: str | None = None
    force_refresh: bool = False


class EmbeddingRegenerationRequest(BaseModel):
    force: bool = False

class DatasetAugmentationRequest(BaseModel):
    method: str = "paraphrase"

class IndexRebuildRequest(BaseModel):
    force: bool = False

class PipelineStepRunRequest(BaseModel):
    step: str

class DescriptionGenerationRequest(BaseModel):
    table_names: list[str] | None = None
    limit: int | None = None

class SchemaSearchRequest(BaseModel):
    question: str
    limit: int = 5
