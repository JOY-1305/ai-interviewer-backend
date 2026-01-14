from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    Enum,
    JSON,
    func,
)
from sqlalchemy.orm import relationship
import enum
from .database import Base


class InterviewStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    competencies = Column(JSON, nullable=True)  # e.g. ["communication","ownership"]

    questions = relationship(
        "JobQuestion", back_populates="job", cascade="all, delete-orphan"
    )
    interviews = relationship("Interview", back_populates="job")


class JobQuestion(Base):
    __tablename__ = "job_questions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    text = Column(Text, nullable=False)
    competency = Column(String(100), nullable=True)
    order_index = Column(Integer, nullable=False, default=0)

    job = relationship("Job", back_populates="questions")


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("job_questions.id"), nullable=False)

    answer_text = Column(Text, nullable=False)
    score = Column(Integer, nullable=True)  # 1-5
    competency_scores = Column(JSON, nullable=True)  # {"communication": 4, ...}
    ai_feedback = Column(Text, nullable=True)

    interview = relationship("Interview", back_populates="answers")
    question = relationship("JobQuestion")


class ContactLead(Base):
    __tablename__ = "contact_leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")  # "user" | "admin"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    interviews = relationship("Interview", back_populates="candidate", foreign_keys="Interview.candidate_user_id")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    candidate_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False)

    status = Column(Enum(InterviewStatus), default=InterviewStatus.NOT_STARTED)
    current_question_index = Column(Integer, nullable=False, default=0)
    invite_token = Column(String(255), unique=True, index=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    overall_score = Column(Integer, nullable=True)

    job = relationship("Job", back_populates="interviews")
    candidate = relationship("User", foreign_keys=[candidate_user_id])
    answers = relationship("InterviewAnswer", back_populates="interview", cascade="all, delete-orphan")
