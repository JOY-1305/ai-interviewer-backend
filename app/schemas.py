from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from enum import Enum


class InterviewStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


# ---------- Job & Questions ----------
class JobQuestionCreate(BaseModel):
    text: str
    competency: Optional[str] = None
    order_index: int = 0


class JobCreate(BaseModel):
    title: str
    description: str
    competencies: Optional[List[str]] = None
    questions: List[JobQuestionCreate]


class JobQuestionOut(BaseModel):
    id: int
    text: str
    competency: Optional[str]
    order_index: int

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    id: int
    title: str
    description: str
    competencies: Optional[List[str]]
    questions: List[JobQuestionOut]

    class Config:
        from_attributes = True


# ---------- Interview ----------
class InterviewCreate(BaseModel):
    job_id: int
    candidate_name: str
    candidate_email: EmailStr


class InterviewOut(BaseModel):
    id: int
    job_id: int
    candidate_name: str
    candidate_email: EmailStr
    status: InterviewStatus
    current_question_index: int
    invite_token: str

    class Config:
        from_attributes = True


class InterviewQuestionOut(BaseModel):
    question_id: int
    question_text: str
    competency: Optional[str] = None


class InterviewStartResponse(BaseModel):
    interview_id: int
    status: InterviewStatus
    next_question: Optional[InterviewQuestionOut] = None


class AnswerSubmit(BaseModel):
    answer_text: str


class AnswerScoringOut(BaseModel):
    question_id: int
    score: Optional[int]
    competency_scores: Optional[Dict[str, int]]
    ai_feedback: Optional[str]
    next_question: Optional[InterviewQuestionOut] = None
    interview_status: InterviewStatus


class InterviewSummaryOut(BaseModel):
    interview_id: int
    overall_recommendation: str
    overall_commentary: str
    average_score: float
    competency_summary: Dict[str, float]


class InterviewAnswerDetail(BaseModel):
    id: int
    question_text: str
    answer_text: str
    score: Optional[int]
    competency_scores: Optional[dict]
    ai_feedback: Optional[str]

    class Config:
        from_attributes = True


class InterviewDetail(BaseModel):
    id: int
    candidate_name: str
    candidate_email: EmailStr
    status: str
    job_title: str
    answers: List[InterviewAnswerDetail]
    summary: Optional[dict] = None

    class Config:
        from_attributes = True

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    message: str

class ContactOut(BaseModel):
    ok: bool

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True  # for SQLAlchemy model -> schema

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
