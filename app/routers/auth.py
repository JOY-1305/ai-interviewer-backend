# app/routers/auth.py
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..security import hash_password, verify_password, create_access_token
from ..deps import get_current_user

router = APIRouter(tags=["auth"])

ADMIN_EMAILS = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}

@router.post("/auth/register", response_model=schemas.TokenOut)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    password = payload.password.strip()
    print("REGISTER payload keys:", payload.model_dump().keys())
    print("REGISTER password repr:", repr(payload.password))
    print("REGISTER password len:", len(payload.password))
    print("REGISTER password bytes:", len(payload.password.encode("utf-8")))
    # Defensive validation (prevents 500 even if schema changes later)
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password too long (max 72 bytes). Avoid emojis or use a shorter password."
        )

    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    role = "admin" if email in ADMIN_EMAILS else "user"

    user = models.User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.email, extra={"role": user.role, "uid": user.id})
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.post("/auth/login", response_model=schemas.TokenOut)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    password = payload.password.strip()

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(subject=user.email, extra={"role": user.role, "uid": user.id})
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.get("/auth/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user
