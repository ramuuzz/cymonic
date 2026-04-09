"""
Meeting Intelligence Hub — FastAPI Application
"""
from contextlib import asynccontextmanager
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Allow running from the 'backend' directory without ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import create_tables
from backend.routers import transcripts, extraction, chatbot, sentiment


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    print("✅ Database tables created / verified")
    yield


app = FastAPI(
    title="Meeting Intelligence Hub",
    description="AI-powered meeting transcript analysis API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcripts.router, prefix="/api", tags=["Transcripts & Projects"])
app.include_router(extraction.router, prefix="/api", tags=["Extraction"])
app.include_router(chatbot.router, prefix="/api", tags=["Chatbot"])
app.include_router(sentiment.router, prefix="/api", tags=["Sentiment"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Meeting Intelligence Hub"}


