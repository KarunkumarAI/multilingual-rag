import uuid
from typing import Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    language: Literal["Auto", "English", "Kannada", "Hindi", "Telugu"] = "Auto"
    provider: Literal["openai", "gemini", "openrouter"] | None = None
    conversation_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    answer: str
    provider: str
    conversation_id: uuid.UUID
