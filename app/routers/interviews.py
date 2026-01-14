from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from ..deps_admin import require_admin


from ..database import get_db
from .. import models, schemas
from ..services import interview_service
from datetime import datetime, timezone

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
        candidate_email=interview_in.candidate_email,
        invite_token=token,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


@router.post("/start/{invite_token}", response_model=schemas.InterviewStartResponse)
def start_interview(invite_token: str, db: Session = Depends(get_db)):
    interview = (
        db.query(models.Interview)
        .filter(models.Interview.invite_token == invite_token)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    next_q = interview_service.start_interview(db, interview)

    next_question_out = None
    if next_q:
        next_question_out = schemas.InterviewQuestionOut(
            question_id=next_q.id,
            question_text=next_q.text,
            competency=next_q.competency,
        )

    return schemas.InterviewStartResponse(
        interview_id=interview.id,
        status=interview.status,
        next_question=next_question_out,
    )


@router.post("/{interview_id}/answer", response_model=schemas.AnswerScoringOut)
def submit_answer(
    interview_id: int,
    payload: schemas.AnswerSubmit,
    db: Session = Depends(get_db),
):
    interview = db.query(models.Interview).get(interview_id)
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
    scoring = result["scoring"]
    status = result["interview_status"]

    next_question_out = None
    if next_q:
        next_question_out = schemas.InterviewQuestionOut(
            question_id=next_q.id,
            question_text=next_q.text,
            competency=next_q.competency,
        )

    return schemas.AnswerScoringOut(
        question_id=db_answer.question_id,
        score=db_answer.score,
        competency_scores=db_answer.competency_scores or {},
        ai_feedback=db_answer.ai_feedback,
        next_question=next_question_out,
        interview_status=status,
    )


@router.get("/{interview_id}/summary", response_model=schemas.InterviewSummaryOut)
def get_interview_summary(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(models.Interview).get(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status != models.InterviewStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Interview not completed yet")

    summary = interview_service.generate_interview_summary(db, interview)
    return schemas.InterviewSummaryOut(
        interview_id=interview.id,
        overall_recommendation=summary["recommendation"],
        overall_commentary=summary["overall_commentary"],
        average_score=summary["average_score"],
        competency_summary=summary["competency_summary"],
    )


@router.get("/job/{job_id}")
def list_interviews(
    job_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return db.query(models.Interview).filter(models.Interview.job_id == job_id).all()


@router.get("/{interview_id}/detail", response_model=schemas.AdminInterviewDetailOut)
def get_interview_detail(
    interview_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview

@router.post("/{interview_id}/complete", response_model=schemas.InterviewCompleteOut)
def complete_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status != models.InterviewStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Interview not completed yet")

    # Build transcript from answers
    lines = []
    for ans in interview.answers:
        q = ans.question.text if ans.question else f"Question {ans.question_id}"
        lines.append(f"Q: {q}\nA: {ans.answer_text}\n")

    transcript = "\n".join(lines).strip()

    interview.transcript = transcript
    interview.completed_at = interview.completed_at or datetime.now(timezone.utc)
    db.commit()
    db.refresh(interview)

    return schemas.InterviewCompleteOut(
        interview_id=interview.id,
        status=interview.status,
        transcript=interview.transcript or "",
        summary=None,
        overall_score=interview.overall_score,
    )
