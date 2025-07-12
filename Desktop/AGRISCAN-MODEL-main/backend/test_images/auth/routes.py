from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from backend.auth.utils import create_access_token, verify_password, get_user_by_email, fake_user_db, save_user
from backend.models.user import UserCreate, UserInDB, UserOut

router = APIRouter()


@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate):
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(user.password)
    user_db = UserInDB(**user.dict(), hashed_password=hashed_password)
    save_user(user_db)
    return user_db


@router.post("/login")
def login(user: UserCreate):
    db_user = get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}
