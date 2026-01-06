# app/utils/auth.py
import os
from fastapi import Header, HTTPException

def admin_api_key(x_api_key: str = Header(None)):
    expected = os.getenv("ADMIN_API_KEY")
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
