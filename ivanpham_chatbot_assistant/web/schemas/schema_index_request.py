from pydantic import BaseModel

class SchemaIndexRequest(BaseModel):
    force_refresh: bool = False
