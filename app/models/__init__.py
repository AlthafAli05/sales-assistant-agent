from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatRequest(BaseModel):
    message: str


class EvalBlock(BaseModel):
    groundedness: float
    relevance: float
    confidence: float
    flagged: bool
    reasoning: str


class ChatResponse(BaseModel):
    response: str
    eval: EvalBlock
    tools_called: List[str]
    session_id: str
    user_id: str


class HistoryMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
    session_id: str


class HistoryResponse(BaseModel):
    user_id: str
    messages: List[HistoryMessage]


class MemoryDeleteResponse(BaseModel):
    user_id: str
    status: str


class HealthResponse(BaseModel):
    status: str
    version: str
