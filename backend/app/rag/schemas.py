import uuid
from typing import Literal
from pydantic import BaseModel, Field

class RagRequest(BaseModel):
    question: str = Field(min_length=2, max_length=12000)
    language: Literal["Auto", "English", "Kannada", "Hindi", "Telugu"] = "Auto"
    provider: Literal["openai", "gemini", "openrouter"] | None = None
    conversation_id: uuid.UUID | None = None

class Citation(BaseModel):
    id: int
    source: str
    document_id: str
    chunk_index: int
    quote: str

class RagResponse(BaseModel):
    answer: str
    provider: str | None
    conversation_id: uuid.UUID
    citations: list[Citation]
    retrieval: str = "hybrid_rrf"
    grounded: bool
    abstained: bool
