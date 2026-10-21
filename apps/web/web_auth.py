"""
Cookie-based authentication for browser pages (separate from the
header-based JWT auth used by the JSON API in apps/api/auth/).
"""

from fastapi import Request, HTTPException, status

from apps.api.auth.security import decode_access_token
from apps.models.db_models import SessionLocal, User


def get_current_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})

    email = payload.get("sub")
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
        return user
    finally:
        session.close()
