import uuid
from datetime import datetime
from pydantic import BaseModel


class ConversationOut(BaseModel):
    id: uuid.UUID
    mode: str
    title: str | None


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime
