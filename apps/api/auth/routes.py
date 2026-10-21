"""
Authentication routes — register and login.
"""

from fastapi import APIRouter, HTTPException, status

from apps.api.schemas import UserCreate, UserLogin, Token
from apps.api.auth.security import hash_password, verify_password, create_access_token
from apps.models.db_models import SessionLocal, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate):
    session = SessionLocal()
    try:
        existing = session.query(User).filter(User.email == user_in.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = User(
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
        )
        session.add(new_user)
        session.commit()
        return {"message": "User registered successfully"}
    finally:
        session.close()


@router.post("/login", response_model=Token)
def login(user_in: UserLogin):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == user_in.email).first()
        if not user or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        session.close()