from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone

from ..database import get_db
from .. import models, schemas
from ..services import interview_service

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/", response_model=schemas.InterviewOut)
def create_interview(interview_in: schemas.InterviewCreate, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == interview_in.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    token = str(uuid.uuid4())
    interview = models.Interview(
        job_id=job.id,
        candidate_name=interview_in.candidate_name,
        candidate_email=str(interview_in.candidate_email).strip().lower(),
        invite_token=token,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


@router.post("/start/{invite_token}", response_model=schemas.InterviewStartResponse)
def start_interview(invite_token: str, db: Session = Depends(get_db)):
    interview = db.query(models.Interview).filter(models.Interview.invite_token == invite_token).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.started_at is None:
        interview.started_at = datetime.now(timezone.utc)

    next_q = interview_service.start_interview(db, interview)

    next_question_out = None
    if next_q:
        next_question_out = schemas.InterviewQuestionOut(
            question_id=next_q.id,
            question_text=next_q.text,
            competency=next_q.competency,
            is_followup=False,
            followup_round=0,
        )

    return schemas.InterviewStartResponse(
        interview_id=interview.id,
        status=interview.status,
        next_question=next_question_out,
    )


@router.post("/{interview_id}/answer", response_model=schemas.AnswerScoringOut)
def submit_answer(interview_id: int, payload: schemas.AnswerSubmit, db: Session = Depends(get_db)):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status == models.InterviewStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Interview already completed")

    result = interview_service.submit_answer_and_get_next(
        db=db,
        interview=interview,
        answer_text=payload.answer_text,
    )

    db_answer = result["answer"]
    next_q = result["next_question"]
    status = result["interview_status"]

    next_question_out = None

    # Follow-up next question
    if isinstance(next_q, dict) and next_q.get("type") == "FOLLOWUP":
        next_question_out = schemas.InterviewQuestionOut(
            question_id=None,
            question_text=next_q["text"],
            competency=None,
            is_followup=True,
            followup_round=int(next_q.get("round", 1)),
        )
    # Spine next question
    elif next_q:
        next_question_out = schemas.InterviewQuestionOut(
            question_id=next_q.id,
            question_text=next_q.text,
            competency=next_q.competency,
            is_followup=False,
            followup_round=0,
        )

    return schemas.AnswerScoringOut(
        asked_question_text=result.get("asked_question_text", ""),
        is_followup=bool(result.get("is_followup", False)),
        followup_round=int(result.get("followup_round", 0)),
        score=getattr(db_answer, "score", None),
        competency_scores=getattr(db_answer, "competency_scores", None) or {},
        ai_feedback=getattr(db_answer, "ai_feedback", None),
        next_question=next_question_out,
        interview_status=status,
    )
