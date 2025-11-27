from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=schemas.JobOut)
def create_job(job_in: schemas.JobCreate, db: Session = get_db()):
    job = models.Job(
        title=job_in.title,
        description=job_in.description,
        competencies=job_in.competencies or [],
    )
    db.add(job)
    db.commit()
    db.refresh(job)

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


@router.get("/", response_model=List[schemas.JobOut])
def list_jobs(db: Session = get_db()):
    jobs = db.query(models.Job).all()
    return jobs
