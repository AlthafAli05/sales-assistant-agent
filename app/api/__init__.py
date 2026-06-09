import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import ChatRequest, ChatResponse, HistoryResponse, MemoryDeleteResponse, HealthResponse, HistoryMessage
from app.services import process_chat, get_history, delete_memory

router = APIRouter()

CATALOG_PATH = Path(__file__).parent.parent.parent / "catalog.json"


@router.post("/chat/{user_id}", response_model=ChatResponse)
async def chat(user_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    try:
        result = process_chat(user_id, request.message, db)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{user_id}/history", response_model=HistoryResponse)
async def history(user_id: str, db: Session = Depends(get_db)):
    messages = get_history(user_id, db)
    return HistoryResponse(
        user_id=user_id,
        messages=[
            HistoryMessage(
                role=m.role,
                content=m.content,
                timestamp=m.timestamp,
                session_id=m.session_id
            ) for m in messages
        ]
    )


@router.delete("/chat/{user_id}/memory", response_model=MemoryDeleteResponse)
async def wipe_memory(user_id: str, db: Session = Depends(get_db)):
    delete_memory(user_id, db)
    return MemoryDeleteResponse(user_id=user_id, status="memory_deleted")


@router.get("/catalog")
async def catalog():
    with open(CATALOG_PATH) as f:
        return json.load(f)


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0")
