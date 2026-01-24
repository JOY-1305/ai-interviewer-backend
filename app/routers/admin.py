from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import secrets

from ..database import get_db
from .. import models, schemas
from ..deps_admin import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

# --------------------
# Leads
# --------------------
@router.get("/leads")
def list_leads(
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    return (
        db.query(models.ContactLead)
        .order_by(models.ContactLead.id.desc())
        .limit(limit)
        .all()
    )

# --------------------
# Jobs
# --------------------
@router.get("/jobs", response_model=List[schemas.JobOut])
def admin_list_jobs(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    return db.query(models.Job).order_by(models.Job.id.desc()).all()

@router.post("/jobs", response_model=schemas.JobOut)
def admin_create_job(
    payload: schemas.JobCreate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    job = models.Job(
        title=payload.title,
        description=payload.description,
        competencies=payload.competencies,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if payload.questions:
        for q in payload.questions:
            db.add(
                models.JobQuestion(
                    job_id=job.id,
                    text=q.text,
                    competency=q.competency,
                    order_index=q.order_index,
                )
            )
        db.commit()
        db.refresh(job)

    return job

@router.get("/jobs/{job_id}", response_model=schemas.JobDetailOut)
def admin_get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/jobs/{job_id}/questions", response_model=schemas.JobQuestionOut)
def admin_add_job_question(
    job_id: int,
    payload: schemas.JobQuestionCreate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    q = models.JobQuestion(
        job_id=job_id,
        text=payload.text,
        competency=payload.competency,
        order_index=payload.order_index,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

@router.delete("/jobs/{job_id}")
def admin_delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"ok": True}

# --------------------
# Interviews
# --------------------
@router.get("/interviews", response_model=List[schemas.AdminInterviewOut])
def admin_list_interviews(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    return db.query(models.Interview).order_by(models.Interview.id.desc()).all()

@router.post("/interviews", response_model=schemas.AdminInterviewOut)
def admin_create_interview(
    payload: schemas.InterviewCreate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    job = db.query(models.Job).filter(models.Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    email = str(payload.candidate_email).strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()

    token = secrets.token_urlsafe(32)

    interview = models.Interview(
        job_id=payload.job_id,
        candidate_name=payload.candidate_name,
        candidate_email=email,
        candidate_user_id=user.id if user else None,
        invite_token=token,
        status=models.InterviewStatus.NOT_STARTED,
        current_question_index=0,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


@router.get("/interviews/{interview_id}", response_model=schemas.AdminInterviewDetailOut)
def admin_get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview
