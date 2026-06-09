import uuid
from sqlalchemy.orm import Session
from app.memory import MemoryStore
from app.agents import run_agent


def process_chat(user_id: str, message: str, db: Session) -> dict:
    session_id = str(uuid.uuid4())
    memory_store = MemoryStore(db)

    # Save user message
    memory_store.save_message(user_id, session_id, "user", message)

    # Run agent
    result = run_agent(user_id, session_id, message, memory_store)

    # Save assistant response
    memory_store.save_message(user_id, session_id, "assistant", result["response"])

    # Save eval log
    memory_store.save_eval(user_id, session_id, result["eval"])

    result["user_id"] = user_id
    return result


def get_history(user_id: str, db: Session):
    memory_store = MemoryStore(db)
    return memory_store.get_history(user_id)


def delete_memory(user_id: str, db: Session):
    memory_store = MemoryStore(db)
    memory_store.delete_user_memory(user_id)
