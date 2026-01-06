from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..utils.auth import admin_api_key

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/leads", dependencies=[Depends(admin_api_key)])
def list_leads(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(models.ContactLead)
        .order_by(models.ContactLead.id.desc())
        .limit(limit)
        .all()
    )
