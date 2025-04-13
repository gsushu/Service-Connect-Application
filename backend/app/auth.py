# filepath: d:\Other\adbms\Service-Connect-Application-main\backend\app\auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models import User
from dependencies import get_db
from pydantic import BaseModel
from passlib.context import CryptContext
import os

# --- Configuration ---
# Use environment variables in production
SECRET_KEY = os.getenv("SECRET_KEY", "abcdefghijklmnopqrstuvwxyz1234567890")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- Token Data Schema ---
class TokenData(BaseModel):
    username: str | None = None
    user_id: int | None = None

# --- Token Creation ---
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- OAuth2 Scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login") # Points to your user login endpoint

# --- Dependency to Get Current User ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") # Assuming 'sub' holds the username
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.user_id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    # You might want to return the user object directly
    # return user
    # Or return a dictionary/Pydantic model with user info
    return {"username": user.username, "id": user.user_id}

# --- Optional: Dependency for Optional Authentication ---
async def get_current_user_optional(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token is None:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
