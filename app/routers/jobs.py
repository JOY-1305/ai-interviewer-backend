# app/routers/jobs.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.utils.auth import admin_api_key
from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(admin_api_key)]  # Secures all routes under /jobs
)


# -----------------------------
# CREATE JOB
# -----------------------------
@router.post("/", response_model=schemas.JobOut)
def create_job(job_in: schemas.JobCreate, db: Session = Depends(get_db)):
    job = models.Job(
        title=job_in.title,
        description=job_in.description,
        competencies=job_in.competencies or [],
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Add questions
    for q in job_in.questions:
        jq = models.JobQuestion(
            job_id=job.id,
            text=q.text,
            competency=q.competency,
            order_index=q.order_index,
        )
        db.add(jq)

    db.commit()
    db.refresh(job)

    return job


# -----------------------------
# LIST JOBS
# -----------------------------
@router.get("/", response_model=List[schemas.JobOut])
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(models.Job).all()
    return jobs


# -----------------------------
# GET JOB
# -----------------------------
@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
