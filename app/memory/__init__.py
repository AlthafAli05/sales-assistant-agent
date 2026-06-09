"""
Memory layer — abstracted so swapping SQLite → Postgres → Mem0
requires changing only this file.
"""
from sqlalchemy.orm import Session
from app.db import Message, EvalLog
from datetime import datetime
import uuid


class MemoryStore:
    def __init__(self, db: Session):
        self.db = db

    def save_message(self, user_id: str, session_id: str, role: str, content: str):
        msg = Message(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        self.db.add(msg)
        self.db.commit()
        return msg

    def get_history(self, user_id: str):
        return (
            self.db.query(Message)
            .filter(Message.user_id == user_id)
            .order_by(Message.timestamp.asc())
            .all()
        )

    def get_recent_context(self, user_id: str, limit: int = 10):
        msgs = (
            self.db.query(Message)
            .filter(Message.user_id == user_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(msgs))

    def delete_user_memory(self, user_id: str):
        self.db.query(Message).filter(Message.user_id == user_id).delete()
        self.db.query(EvalLog).filter(EvalLog.user_id == user_id).delete()
        self.db.commit()

    def save_eval(self, user_id: str, session_id: str, eval_data: dict):
        log = EvalLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            groundedness=eval_data["groundedness"],
            relevance=eval_data["relevance"],
            confidence=eval_data["confidence"],
            flagged=eval_data["flagged"],
            reasoning=eval_data["reasoning"],
            timestamp=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()

    def get_user_summary(self, user_id: str) -> str:
        """Returns a text summary of past user interactions for context injection."""
        msgs = self.get_recent_context(user_id, limit=20)
        if not msgs:
            return "No previous interactions found for this user."
        lines = []
        for m in msgs:
            lines.append(f"{m.role.upper()}: {m.content}")
        return "\n".join(lines)
