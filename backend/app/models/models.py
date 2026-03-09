from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey,
    Text, Float, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    refresh_token = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    papers = relationship("Paper", back_populates="user")
    answers = relationship("StudentAnswer", back_populates="user")


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_code = Column(String(20), nullable=False)
    subject_name = Column(String(255), nullable=False)
    paper_name = Column(String(255), nullable=False)
    year = Column(String(10), nullable=True)
    session = Column(String(50), nullable=True)
    question_pdf_path = Column(String(500), nullable=False)
    markscheme_pdf_path = Column(String(500), nullable=False)
    parsed_questions = Column(JSON, nullable=True)
    parsed_markscheme = Column(JSON, nullable=True)
    parse_status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="papers")
    questions = relationship("Question", back_populates="paper", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    question_key = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=True)
    markscheme_text = Column(Text, nullable=True)
    marks = Column(Integer, default=0)
    question_type = Column(String(50), default="text")  # text, diagram, mcq
    order_index = Column(Integer, default=0)

    paper = relationship("Paper", back_populates="questions")
    answers = relationship("StudentAnswer", back_populates="question", cascade="all, delete-orphan")


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answer_text = Column(Text, nullable=True)
    image_paths = Column(JSON, default=list)
    marks_awarded = Column(Float, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    chat_history = Column(JSON, default=list)
    attempt_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    question = relationship("Question", back_populates="answers")
    user = relationship("User", back_populates="answers")
