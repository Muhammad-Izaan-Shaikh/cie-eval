from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import User, Paper, Question
from app.schemas.schemas import QuestionResponse
from app.utils.auth import get_verified_user

router = APIRouter()


@router.get("/paper/{paper_id}", response_model=List[QuestionResponse])
async def get_paper_questions(
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

    if paper.parse_status != "complete":
        raise HTTPException(
            400,
            f"Paper is still being processed (status: {paper.parse_status})"
        )

    questions = (
        db.query(Question)
        .filter(Question.paper_id == paper_id)
        .order_by(Question.order_index)
        .all()
    )
    return questions
