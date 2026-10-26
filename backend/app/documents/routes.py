from pathlib import Path
import socket, uuid
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.auth.deps import current_user
from backend.app.db.deps import get_db
from backend.app.db.models import Document, DocumentStatus, DocumentVersion, User
from backend.app.documents.extractors import SUPPORTED, extract
from backend.app.documents.schemas import UrlIn
from backend.app.rag.vector_store import delete_document as delete_vectors, index_document

router = APIRouter(prefix="/documents", tags=["documents"])
MAX_BYTES = 20 * 1024 * 1024

def owned(db, user, did):
    d = db.scalar(select(Document).where(Document.id == did, Document.user_id == user.id))
    if not d: raise HTTPException(404, "Document not found")
    return d

def out(d):
    return {"id":str(d.id),"name":d.name,"source_type":d.source_type,"source_url":d.source_url,"status":d.status.value,"error":d.error,"created_at":d.created_at}

def store_and_index(db, d, text, source, user):
    version = DocumentVersion(document_id=d.id,version="1",extracted_text=text,char_count=str(len(text)))
    db.add(version); db.flush()
    count = index_document(user.id, d.id, version.id, text, source)
    if count < 1: raise ValueError("No chunks could be indexed.")
    d.status = DocumentStatus.READY

@router.get("")
def list_documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [out(d) for d in db.scalars(select(Document).where(Document.user_id==user.id).order_by(Document.created_at.desc())).all()]

@router.post("/upload", status_code=201)
def upload(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    name = Path(file.filename or "upload").name
    if Path(name).suffix.lower() not in SUPPORTED: raise HTTPException(415, "Unsupported file format.")
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES: raise HTTPException(413, "File exceeds 20 MB limit.")
    d = Document(user_id=user.id,name=name,source_type="file",status=DocumentStatus.PROCESSING); db.add(d); db.flush()
    try:
        text, used_ocr = extract(name,data)
        text = text.strip()
        if not text: raise ValueError("No readable text found, including OCR fallback.")
        store_and_index(db, d, text, name, user)
    except Exception as e:
        d.status=DocumentStatus.FAILED; d.error=str(e)[:500]
    db.commit(); db.refresh(d); return out(d)

@router.post("/url", status_code=201)
def add_url(body: UrlIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    url=str(body.url); host=urlparse(url).hostname or ""
    try:
        ips={x[4][0] for x in socket.getaddrinfo(host,None)}
        if any(ip.startswith(("127.","10.","192.168.")) or ip.startswith("172.") for ip in ips): raise HTTPException(400,"Private/local URLs are not allowed.")
        r=requests.get(url,timeout=12,allow_redirects=True,headers={"User-Agent":"SelfHealingRAG/1.0"}); r.raise_for_status()
        if len(r.content)>MAX_BYTES: raise HTTPException(413,"URL content exceeds 20 MB limit.")
    except HTTPException: raise
    except Exception as e: raise HTTPException(400,"Could not fetch URL") from e
    d=Document(user_id=user.id,name=host or url,source_type="url",source_url=url,status=DocumentStatus.PROCESSING); db.add(d); db.flush()
    try:
        text=BeautifulSoup(r.text,"html.parser").get_text("\n",strip=True)
        if not text: raise ValueError("No readable text found.")
        store_and_index(db, d, text, url, user)
    except Exception as e:
        d.status=DocumentStatus.FAILED; d.error=str(e)[:500]
    db.commit(); db.refresh(d); return out(d)

@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID,user: User=Depends(current_user),db: Session=Depends(get_db)):
    d=owned(db,user,document_id)
    try: delete_vectors(document_id)
    except Exception: pass
    db.delete(d); db.commit()
