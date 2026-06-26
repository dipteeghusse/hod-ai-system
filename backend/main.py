"""HOD AI System — FastAPI Application Entry Point."""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database.db import init_db
from api.routes import router
from rag.retriever import rag_retriever
from services.email_poller import run_email_poller


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME}")
    await init_db()
    print("✅ Database initialized")
    await rag_retriever.initialize()
    print("✅ RAG knowledge base loaded")

    # Start email poller in background (no-op if IMAP_USER not set)
    poller_task = asyncio.create_task(run_email_poller())
    print("✅ Email poller started" if settings.IMAP_USER else "ℹ️  Email poller disabled (IMAP_USER not set)")

    yield

    poller_task.cancel()
    print("🛑 Shutting down HOD AI System")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered HoD Assistant for MITAOE CSE-AIML Department",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "system": settings.APP_NAME,
        "department": settings.DEPARTMENT,
        "institution": settings.INSTITUTION,
        "status": "operational",
        "api_docs": "/api/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
