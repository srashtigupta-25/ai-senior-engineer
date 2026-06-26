from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.repository import router as repository_router
from app.api.chat import router as chat_router
from app.api.analysis import router as analysis_router


app = FastAPI(
    title="AI Senior Engineer API",
    description="Backend API for repository indexing, retrieval, and AI codebase analysis.",
    version="1.0.0"
)

# This allows the Next.js frontend to call the FastAPI backend during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    repository_router,
    prefix="/repository",
    tags=["Repository"]
)

app.include_router(
    chat_router,
    prefix="/chat",
    tags=["Chat"]
)

app.include_router(
    analysis_router,
    prefix="/analysis",
    tags=["Analysis"]
)


@app.get("/")
def home():
    return {
        "message": "AI Senior Engineer API is running"
    }