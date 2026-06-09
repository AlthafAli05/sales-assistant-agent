from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sales_agent.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    session_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class EvalLog(Base):
    __tablename__ = "eval_logs"
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    session_id = Column(String, nullable=False)
    groundedness = Column(Float)
    relevance = Column(Float)
    confidence = Column(Float)
    flagged = Column(Boolean, default=False)
    reasoning = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
