from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.auth.deps import current_user
from backend.app.auth.schemas import Credentials, TokenOut, UserOut
from backend.app.auth.security import create_access_token, hash_password, verify_password
from backend.app.db.deps import get_db
from backend.app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: Credentials, db: Session = Depends(get_db)) -> User:
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(data: Credentials, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/logout", status_code=204)
def logout() -> None:
    return None


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user
