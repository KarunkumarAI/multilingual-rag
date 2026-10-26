import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.auth.deps import current_user
from backend.app.db.deps import get_db
from backend.app.db.models import Conversation, Message, User
from backend.app.conversations.schemas import ConversationOut, MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


def owned(db: Session, user: User, cid: uuid.UUID) -> Conversation:
    conv = db.get(Conversation, cid)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.get("", response_model=list[ConversationOut])
def list_conversations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.id.desc())
    return db.scalars(q).all()


@router.get("/{cid}/messages", response_model=list[MessageOut])
def messages(cid: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned(db, user, cid)
    q = select(Message).where(Message.conversation_id == cid).order_by(Message.created_at, Message.id)
    return db.scalars(q).all()


@router.delete("/{cid}", status_code=204)
def delete(cid: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = owned(db, user, cid); db.delete(conv); db.commit()
