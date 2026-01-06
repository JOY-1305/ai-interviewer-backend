from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/public", tags=["public"])

@router.post("/contact", response_model=schemas.ContactOut)
def create_contact(payload: schemas.ContactCreate, db: Session = Depends(get_db)):
    lead = models.ContactLead(
        name=payload.name.strip(),
        email=payload.email.strip(),
        message=payload.message.strip(),
    )
    db.add(lead)
    db.commit()
    return {"ok": True}
