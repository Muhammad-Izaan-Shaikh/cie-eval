from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Any, Dict
from datetime import datetime


# --- Auth Schemas ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class EmailVerifyRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Paper Schemas ---

class PaperCreate(BaseModel):
    subject_code: str
    subject_name: str
    paper_name: str
    year: Optional[str] = None
    session: Optional[str] = None


class PaperResponse(BaseModel):
    id: int
    user_id: int
    subject_code: str
    subject_name: str
    paper_name: str
    year: Optional[str]
    session: Optional[str]
    parse_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaperDetailResponse(PaperResponse):
    parsed_questions: Optional[Dict[str, Any]]
    parsed_markscheme: Optional[Dict[str, Any]]


# --- Question Schemas ---

class QuestionResponse(BaseModel):
    id: int
    paper_id: int
    question_key: str
    question_text: Optional[str]
    markscheme_text: Optional[str]
    marks: int
    question_type: str
    order_index: int

    class Config:
        from_attributes = True


# --- Answer Schemas ---

class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    question_id: int
    message: str
    mode: str = "feedback"  # feedback, improve, model_answer


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    user_id: int
    answer_text: Optional[str]
    marks_awarded: Optional[float]
    ai_feedback: Optional[str]
    chat_history: List[Dict[str, str]]
    attempt_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class GradeResponse(BaseModel):
    marks_awarded: float
    max_marks: int
    feedback: str
    answer_id: int
