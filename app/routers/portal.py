# app/routers/portal.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User

router = APIRouter(prefix="/portal", tags=["portal"])

@router.get("/dashboard")
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # MVP: return basic info; later return interviews list, stats, etc.
    return {
        "message": "User portal is live",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
        }
    }
