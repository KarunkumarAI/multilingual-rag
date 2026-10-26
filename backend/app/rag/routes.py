from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.auth.deps import current_user
from backend.app.db.deps import get_db
from backend.app.db.models import Conversation, ConversationMode, Message, User
from backend.app.rag.schemas import RagRequest, RagResponse
from backend.app.rag.service import answer
from backend.app.rag.vector_store import search

router = APIRouter(prefix="/rag", tags=["rag"])

@router.get("/search")
def hybrid_search(q: str = Query(min_length=2), limit: int = Query(5, ge=1, le=10), user: User = Depends(current_user)):
    return search(user.id, q, limit)

@router.post("/ask", response_model=RagResponse)
def rag_ask(body: RagRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = db.get(Conversation, body.conversation_id) if body.conversation_id else None
    if conv and (conv.user_id != user.id or conv.mode != ConversationMode.RAG):
        raise HTTPException(404, "Conversation not found")
    if not conv:
        conv=Conversation(user_id=user.id, mode=ConversationMode.RAG, title=body.question[:80]); db.add(conv); db.flush()
    db.add(Message(conversation_id=conv.id, role="user", content=body.question)); db.commit()
    try:
        text, provider, citations, grounded, abstained = answer(user.id, body.question, body.language, body.provider)
        db.add(Message(conversation_id=conv.id, role="assistant", content=text)); db.commit()
        return RagResponse(answer=text,provider=provider,conversation_id=conv.id,citations=citations,grounded=grounded,abstained=abstained)
    except RuntimeError as exc: raise HTTPException(503, str(exc)) from exc
    except Exception as exc: raise HTTPException(502, "RAG answer generation failed") from exc
