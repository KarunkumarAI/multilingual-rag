from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, HttpUrl

class UrlIn(BaseModel):
    url: HttpUrl

class DocumentOut(BaseModel):
    id: UUID
    name: str
    source_type: str
    source_url: str | None
    status: str
    error: str | None
    created_at: datetime
