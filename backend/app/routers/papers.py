from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import logging

from app.database import get_db
from app.models.models import User, Paper, Question
from app.schemas.schemas import PaperResponse, PaperDetailResponse
from app.utils.auth import get_verified_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf"}
MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def save_upload(upload: UploadFile, subfolder: str) -> str:
    ext = os.path.splitext(upload.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Only PDF files are allowed")

    unique_name = f"{uuid.uuid4()}{ext}"
    dest_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, unique_name)

    bytes_written = 0
    upload.file.seek(0)
    with open(dest_path, "wb") as out_file:
        while chunk := upload.file.read(1024 * 1024):
            bytes_written += len(chunk)
            if bytes_written > MAX_SIZE_BYTES:
                out_file.close()
                os.remove(dest_path)
                raise HTTPException(413, f"File too large. Max {settings.MAX_FILE_SIZE_MB} MB")
            out_file.write(chunk)

    logger.info(f"Saved: {dest_path} ({bytes_written / 1024:.1f} KB)")
    return dest_path


def process_paper_background(paper_id: int, db_url: str):
    """
    Background task:
    1. Extract raw text from both PDFs
    2. Send to LLM to parse question structure and mark scheme
    3. Merge results and save Question rows to DB
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.services.pdf_parser import extract_text_from_pdf
    from app.services.llm_parser import (
        parse_question_paper_with_llm,
        parse_mark_scheme_with_llm,
        merge_questions_and_markscheme,
    )

    engine = create_engine(db_url)
    LocalSession = sessionmaker(bind=engine)
    db = LocalSession()

    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            logger.error(f"[paper {paper_id}] Not found")
            return

        paper.parse_status = "processing"
        db.commit()
        logger.info(f"[paper {paper_id}] Starting LLM-based parse")

        # Step 1: Extract raw text from PDFs
        logger.info(f"[paper {paper_id}] Extracting text from question paper PDF")
        q_text = extract_text_from_pdf(paper.question_pdf_path)

        logger.info(f"[paper {paper_id}] Extracting text from mark scheme PDF")
        ms_text = extract_text_from_pdf(paper.markscheme_pdf_path)

        # Step 2: LLM parsing
        logger.info(f"[paper {paper_id}] Sending question paper to LLM")
        questions = parse_question_paper_with_llm(q_text)

        logger.info(f"[paper {paper_id}] Sending mark scheme to LLM")
        markscheme = parse_mark_scheme_with_llm(ms_text)

        # Step 3: Merge
        records = merge_questions_and_markscheme(questions, markscheme)
        logger.info(f"[paper {paper_id}] {len(records)} records merged")

        # Step 4: Save to DB
        db.query(Question).filter(Question.paper_id == paper_id).delete()
        for rec in records:
            db.add(Question(paper_id=paper_id, **rec))

        paper.parsed_questions  = {"llm_parsed": True, "count": len(questions)}
        paper.parsed_markscheme = {"llm_parsed": True, "count": len(markscheme)}
        paper.parse_status = "complete"
        db.commit()
        logger.info(f"[paper {paper_id}] ✓ Complete — {len(records)} questions saved")

    except Exception as e:
        logger.exception(f"[paper {paper_id}] Parse failed: {e}")
        try:
            p = db.query(Paper).filter(Paper.id == paper_id).first()
            if p:
                p.parse_status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/upload", response_model=PaperResponse, status_code=201)
async def upload_paper(
    background_tasks: BackgroundTasks,
    subject_code: str = Form(...),
    subject_name: str = Form(...),
    paper_name: str = Form(...),
    year: Optional[str] = Form(None),
    session: Optional[str] = Form(None),
    question_pdf: UploadFile = File(...),
    markscheme_pdf: UploadFile = File(...),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Upload from user {current_user.id}: {subject_code} / {paper_name}"
    )

    q_path  = save_upload(question_pdf, "papers")
    ms_path = save_upload(markscheme_pdf, "markschemes")

    paper = Paper(
        user_id=current_user.id,
        subject_code=subject_code,
        subject_name=subject_name,
        paper_name=paper_name,
        year=year,
        session=session,
        question_pdf_path=q_path,
        markscheme_pdf_path=ms_path,
        parse_status="pending",
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    logger.info(f"Paper {paper.id} created, queuing LLM parse")
    background_tasks.add_task(process_paper_background, paper.id, settings.DATABASE_URL)
    return paper


@router.get("", response_model=List[PaperResponse])
async def list_papers(
    subject_code: Optional[str] = None,
    subject_name: Optional[str] = None,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    query = db.query(Paper).filter(Paper.user_id == current_user.id)
    if subject_code:
        query = query.filter(Paper.subject_code.ilike(f"%{subject_code}%"))
    if subject_name:
        query = query.filter(Paper.subject_name.ilike(f"%{subject_name}%"))
    return query.order_by(Paper.created_at.desc()).all()


@router.get("/{paper_id}", response_model=PaperDetailResponse)
async def get_paper(
    paper_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.user_id == current_user.id
    ).first()
    if not paper:
        raise HTTPException(404, "Paper not found")
    return paper


@router.delete("/{paper_id}", status_code=204)
async def delete_paper(
    paper_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.user_id == current_user.id
    ).first()
    if not paper:
        raise HTTPException(404, "Paper not found")

    for path in [paper.question_pdf_path, paper.markscheme_pdf_path]:
        if path and os.path.exists(path):
            os.remove(path)

    db.delete(paper)
    db.commit()
