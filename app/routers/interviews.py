from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone

from ..database import get_db
from .. import models, schemas
from ..services import interview_service
from sqlalchemy import desc
from ..services import proctoring_service

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
        interview_id=interview.id,
        answer_text=payload.answer_text,
        answer_meta=payload.answer_meta,
    )


    scoring = result.get("scoring") or {}
    next_q = result.get("next_question")
    status = result["interview_status"]

    next_question_out = None
    if next_q:
        # service returns either dict for followups OR JobQuestion model
        if isinstance(next_q, dict) and next_q.get("type") == "FOLLOWUP":
            next_question_out = schemas.InterviewQuestionOut(
                question_id=None,
                question_text=next_q["text"],
                competency=None,
                is_followup=True,
                followup_round=int(next_q.get("round") or 1),
            )
        else:
            # JobQuestion model
            next_question_out = schemas.InterviewQuestionOut(
                question_id=next_q.id,
                question_text=next_q.text,
                competency=getattr(next_q, "competency", None),
                is_followup=False,
                followup_round=0,
            )

    return schemas.AnswerScoringOut(
        asked_question_text=result.get("asked_question_text") or "",
        is_followup=bool(result.get("is_followup")),
        followup_round=int(result.get("followup_round") or 0),
        score=scoring.get("overall_score"),
        competency_scores=scoring.get("competency_scores"),
        ai_feedback=scoring.get("feedback"),
        next_question=next_question_out,
        interview_status=status,
    )


@router.post("/{interview_id}/proctoring/event", response_model=dict)
def add_proctor_event(
    interview_id: int,
    payload: schemas.ProctorEventIn,
    db: Session = Depends(get_db),
):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Save event
    ev = models.InterviewProctorEvent(
        interview_id=interview_id,
        event_type=payload.event_type.upper().strip(),
        severity=int(payload.severity or 1),
        payload=payload.payload or {},
    )
    db.add(ev)
    db.commit()

    # Recompute integrity from latest N events (cheap + reliable)
    recent = (
        db.query(models.InterviewProctorEvent)
        .filter(models.InterviewProctorEvent.interview_id == interview_id)
        .order_by(desc(models.InterviewProctorEvent.created_at))
        .limit(200)
        .all()
    )

    computed = proctoring_service.compute_integrity(
        [{"event_type": r.event_type} for r in recent]
    )

    interview.integrity_score = computed["score"]
    interview.integrity_flags = computed["flags"]
    interview.proctoring_version = computed["flags"].get("version", "v1")
    db.commit()

    return {"ok": True, "integrity_score": interview.integrity_score}


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
