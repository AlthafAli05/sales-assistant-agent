from fastapi import FastAPI
from app.api import router
from app.db import create_tables

app = FastAPI(
    title="Sales Assistant Agent",
    description="Persistent AI sales assistant with memory, tool use, and self-evaluation",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    create_tables()

app.include_router(router)
