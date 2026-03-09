from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid
import logging

from app.database import get_db
from app.models.models import User, Question, StudentAnswer
from app.schemas.schemas import AnswerSubmit, ChatRequest, AnswerResponse, GradeResponse
from app.utils.auth import get_verified_user
from app.services.ai_grader import grade_answer, chat_with_ai
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_IMAGE_UPLOADS = 3


@router.post("/submit", response_model=GradeResponse)
async def submit_answer(
    data: AnswerSubmit,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == data.question_id).first()
    if not question:
        raise HTTPException(404, "Question not found")

    # Ensure the paper belongs to user
    if question.paper.user_id != current_user.id:
        raise HTTPException(403, "Access denied")

    # Get or create answer record
    answer = db.query(StudentAnswer).filter(
        StudentAnswer.question_id == data.question_id,
        StudentAnswer.user_id == current_user.id,
    ).first()

    if not answer:
        answer = StudentAnswer(
            question_id=data.question_id,
            user_id=current_user.id,
            chat_history=[],
            image_paths=[],
        )
        db.add(answer)

    answer.answer_text = data.answer_text
    answer.attempt_count = (answer.attempt_count or 0) + 1
    db.commit()

    # Grade with AI
    try:
        marks_awarded, feedback = await grade_answer(
            question_text=question.question_text or "",
            markscheme_text=question.markscheme_text or "",
            marks=question.marks or 1,
            student_answer=data.answer_text,
        )
    except Exception as e:
        logger.error(f"AI grading failed: {e}")
        raise HTTPException(503, f"AI grading service unavailable: {str(e)}")

    answer.marks_awarded = marks_awarded
    answer.ai_feedback = feedback
    db.commit()
    db.refresh(answer)

    return GradeResponse(
        marks_awarded=marks_awarded,
        max_marks=question.marks or 1,
        feedback=feedback,
        answer_id=answer.id,
    )


@router.post("/chat", response_model=dict)
async def chat_about_answer(
    data: ChatRequest,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == data.question_id).first()
    if not question:
        raise HTTPException(404, "Question not found")

    if question.paper.user_id != current_user.id:
        raise HTTPException(403, "Access denied")

    answer = db.query(StudentAnswer).filter(
        StudentAnswer.question_id == data.question_id,
        StudentAnswer.user_id == current_user.id,
    ).first()

    if not answer:
        raise HTTPException(400, "Please submit an answer before chatting")

    try:
        ai_response = await chat_with_ai(
            question_text=question.question_text or "",
            markscheme_text=question.markscheme_text or "",
            marks=question.marks or 1,
            student_answer=answer.answer_text or "",
            current_marks=answer.marks_awarded or 0,
            ai_feedback=answer.ai_feedback or "",
            user_message=data.message,
            mode=data.mode,
            chat_history=answer.chat_history or [],
        )
    except Exception as e:
        raise HTTPException(503, f"AI service error: {str(e)}")

    # Append to chat history
    history = answer.chat_history or []
    history.append({"role": "user", "content": data.message})
    history.append({"role": "assistant", "content": ai_response})
    answer.chat_history = history
    db.commit()

    return {"response": ai_response, "mode": data.mode}


@router.post("/upload-image/{question_id}", response_model=dict)
async def upload_diagram(
    question_id: int,
    image: UploadFile = File(...),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(404, "Question not found")

    answer = db.query(StudentAnswer).filter(
        StudentAnswer.question_id == question_id,
        StudentAnswer.user_id == current_user.id,
    ).first()

    if not answer:
        answer = StudentAnswer(
            question_id=question_id,
            user_id=current_user.id,
            chat_history=[],
            image_paths=[],
        )
        db.add(answer)
        db.commit()

    if len(answer.image_paths or []) >= MAX_IMAGE_UPLOADS:
        raise HTTPException(400, f"Maximum {MAX_IMAGE_UPLOADS} image uploads per question")

    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    ext = os.path.splitext(image.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(400, "Only image files are allowed")

    img_dir = os.path.join(settings.UPLOAD_DIR, "images")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, f"{uuid.uuid4()}{ext}")

    content = await image.read()
    with open(img_path, "wb") as f:
        f.write(content)

    paths = list(answer.image_paths or [])
    paths.append(img_path)
    answer.image_paths = paths
    db.commit()

    return {"message": "Image uploaded", "path": img_path}


@router.get("/question/{question_id}", response_model=Optional[AnswerResponse])
async def get_answer(
    question_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    answer = db.query(StudentAnswer).filter(
        StudentAnswer.question_id == question_id,
        StudentAnswer.user_id == current_user.id,
    ).first()
    return answer
