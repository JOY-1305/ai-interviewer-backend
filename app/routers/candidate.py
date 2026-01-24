from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..deps import get_current_user
from .. import models, schemas

router = APIRouter(prefix="/candidate", tags=["candidate"])

@router.get("/interviews", response_model=schemas.CandidateInterviewListOut)
def get_my_interviews(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    interviews = (
        db.query(models.Interview)
        .filter(
            or_(
                models.Interview.candidate_user_id == current_user.id,
                models.Interview.candidate_email == current_user.email,
            )
        )
        .order_by(models.Interview.id.desc())
        .all()
    )

    out = []
    for i in interviews:
        out.append(
            schemas.CandidateInterviewOut(
                id=i.id,
                job_id=i.job_id,
                job_title=i.job.title if i.job else None,
                candidate_name=i.candidate_name,
                candidate_email=i.candidate_email,
                status=i.status,
                invite_token=i.invite_token,
                created_at=getattr(i, "created_at", None),
                started_at=i.started_at,
                completed_at=i.completed_at,
            )
        )

    return {"interviews": out}


@router.get("/dashboard", response_model=schemas.CandidateDashboardOut)
def candidate_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    qs = db.query(models.Interview).filter(
        or_(
            models.Interview.candidate_user_id == current_user.id,
            models.Interview.candidate_email == current_user.email,
        )
    )

    total = qs.count()
    pending = qs.filter(models.Interview.status == models.InterviewStatus.NOT_STARTED).count()
    in_progress = qs.filter(models.Interview.status == models.InterviewStatus.IN_PROGRESS).count()
    completed = qs.filter(models.Interview.status == models.InterviewStatus.COMPLETED).count()

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
    }
