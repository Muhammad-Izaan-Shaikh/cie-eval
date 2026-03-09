import logging
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import auth, papers, questions, answers
from app.database import engine, Base
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CIE Exam Evaluator API", version="1.0.0")

# Build CORS origins list — always include localhost for local dev,
# plus any FRONTEND_URL set via env var (e.g. the Render frontend URL)
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads/papers", exist_ok=True)
os.makedirs("uploads/markschemes", exist_ok=True)
os.makedirs("uploads/images", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
app.include_router(papers.router,    prefix="/papers",    tags=["Papers"])
app.include_router(questions.router, prefix="/questions", tags=["Questions"])
app.include_router(answers.router,   prefix="/answers",   tags=["Answers"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
