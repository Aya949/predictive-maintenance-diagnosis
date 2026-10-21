"""
Route protection — extracts and validates the current user from a JWT token.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from apps.api.auth.security import decode_access_token
from apps.models.db_models import SessionLocal, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email = payload.get("sub")
    if email is None:
        raise credentials_exception

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        return user
    finally:
        session.close()