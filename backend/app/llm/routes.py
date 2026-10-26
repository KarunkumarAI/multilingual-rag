from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.auth.deps import current_user
from backend.app.db.deps import get_db
from backend.app.db.models import Conversation, ConversationMode, Message, User
from backend.app.llm.schemas import ChatRequest, ChatResponse
from backend.app.llm.service import chat

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/message", response_model=ChatResponse)
def chatbot_message(body: ChatRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = db.get(Conversation, body.conversation_id) if body.conversation_id else None
    if conv and (conv.user_id != user.id or conv.mode != ConversationMode.CHATBOT):
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conv:
        conv = Conversation(user_id=user.id, mode=ConversationMode.CHATBOT, title=body.message[:80])
        db.add(conv); db.flush()
    db.add(Message(conversation_id=conv.id, role="user", content=body.message)); db.commit()
    try:
        answer, provider = chat(body.message, body.language, body.provider)
        db.add(Message(conversation_id=conv.id, role="assistant", content=answer)); db.commit()
        return ChatResponse(answer=answer, provider=provider, conversation_id=conv.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="LLM provider request failed") from exc
