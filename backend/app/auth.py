# filepath: d:\Other\adbms\Service-Connect-Application-main\backend\app\auth.py
from fastapi import Depends, HTTPException, status, Request
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
        username: str | None = payload.get("sub") # Assuming 'sub' holds the username
        user_id: int | None = payload.get("id")
        role: str | None = payload.get("role") # Extract role

        if username is None or user_id is None or role is None: # Validate all expected fields
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise credentials_exception
    # Return a dictionary that includes the role
    return {"username": user.username, "id": user.user_id, "role": role}

# --- Optional: Dependency for Optional Authentication ---
async def get_current_user_optional(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token is None:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None

# Role-based access control dependency functions
def get_current_user_with_role_check(allowed_roles: list = ["User"]):  # Updated default to capitalized "User"
    """
    Dependency that checks if the current user has one of the allowed roles.
    Default is to only allow regular users.
    """
    async def _get_user_with_role(current_user_payload: dict = Depends(get_current_user)):
        # current_user_payload is the dictionary returned by get_current_user (e.g., JWT payload)
        user_role = current_user_payload.get("role")

        if user_role and user_role in allowed_roles:
            return current_user_payload # Return the payload

        # Role not allowed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this endpoint. Insufficient permissions.",
        )

    return _get_user_with_role

# Session authentication for Admin and Worker
def verify_session(request: Request, required_role: str = None):
    """
    Helper function to verify session-based authentication
    for Admin and Worker routes.
    """
    # Check for admin session
    if required_role == "Admin":  # Capitalized role
        admin_session = request.session.get("admin")
        if not admin_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated as admin"
            )
        return admin_session

    # Check for worker session
    if required_role == "Worker":  # Capitalized role
        worker_session = request.session.get("worker")
        if not worker_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated as worker"
            )
        return worker_session

    # If no specific role required, return None
    return None

# Example usage: Depends(get_current_user_with_role_check(["admin"]))
