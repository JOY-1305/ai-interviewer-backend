from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime
from typing import Any

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
    questions: Optional[List[JobQuestionCreate]] = None


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

class InterviewByTokenOut(BaseModel):
    id: int
    job_id: int
    candidate_name: str
    candidate_email: EmailStr
    status: InterviewStatus
    current_question_index: int
    invite_token: str
    job_title: Optional[str] = None
    total_questions: int = 0

    class Config:
        from_attributes = True

class InterviewTokenStartRequest(BaseModel):
    invite_token: str

class InterviewTokenAnswerRequest(BaseModel):
    invite_token: str
    answer_text: str

class InterviewCompleteOut(BaseModel):
    interview_id: int
    status: InterviewStatus
    transcript: str
    summary: Optional[dict] = None
    overall_score: Optional[int] = None


class JobQuestionMini(BaseModel):
    id: int
    text: str
    competency: Optional[str] = None
    order_index: int

    class Config:
        from_attributes = True

class InterviewAnswerOut(BaseModel):
    id: int
    question_id: int
    answer_text: str
    score: Optional[int] = None
    competency_scores: Optional[dict] = None
    ai_feedback: Optional[str] = None
    question: Optional[JobQuestionMini] = None

    class Config:
        from_attributes = True

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


class InterviewDetail(BaseModel):
    id: int
    candidate_name: str
    candidate_email: EmailStr
    status: InterviewStatus
    job_title: str
    answers: List[InterviewAnswerOut]
    summary: Optional[Any] = None  # keep flexible for now

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


class AdminInterviewOut(InterviewOut):
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    transcript: Optional[str] = None
    summary: Optional[Any] = None
    overall_score: Optional[int] = None

class AdminInterviewDetailOut(AdminInterviewOut):
    answers: List[InterviewAnswerOut] = []

class JobDetailOut(JobOut):
    pass

class AdminInterviewDetailOut(AdminInterviewOut):
    answers: List[InterviewAnswerOut] = []


from datetime import datetime
from typing import Optional, List

class CandidateInterviewOut(BaseModel):
    id: int
    job_id: int
    job_title: Optional[str] = None

    candidate_name: str
    candidate_email: EmailStr

    status: InterviewStatus
    invite_token: str

    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CandidateInterviewListOut(BaseModel):
    interviews: List[CandidateInterviewOut]
