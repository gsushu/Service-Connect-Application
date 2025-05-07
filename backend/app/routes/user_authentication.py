from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dependencies import get_db
from models import User
from pydantic import BaseModel
from auth import create_access_token, get_password_hash, verify_password, get_current_user
from datetime import timedelta

router = APIRouter()

class UserDetails(BaseModel):
    username: str
    email: str
    mobile: str
    password: str

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user_data: UserDetails, db: Session = Depends(get_db)):
    existing_user_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_user_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    existing_user_name = db.query(User).filter(User.username == user_data.username).first()
    if existing_user_name:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        mobile=user_data.mobile,
        password=hashed_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": new_user.username, "id": new_user.user_id, "role": "User"},  # Capitalize role
        expires_delta=access_token_expires
    )

    return {
        "message": f"User {new_user.username} created successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "role": "User",  # Capitalize role
        "username": new_user.username,
        "user_id": new_user.user_id,  # Added explicit user_id field
        "id": new_user.user_id  # Keep id for backwards compatibility
    }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_obj = db.query(User).filter(User.username == form_data.username).first()
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    if not verify_password(form_data.password, user_obj.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    # Create the token with role information
    payload = {
        "sub": user_obj.username,
        "id": user_obj.user_id,
        "role": "User"  # Capitalize role for consistency
    }

    # Generate token
    access_token = create_access_token(data=payload)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "User",  # Capitalize role for consistency
        "username": user_obj.username,
        "user_id": user_obj.user_id,  # Added explicit user_id field
        "id": user_obj.user_id  # Keep id for backwards compatibility
    }

@router.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    userDetails = db.query(User).filter(User.user_id == current_user["id"]).first()
    if not userDetails:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": userDetails.user_id,
        "username": userDetails.username,
        "email": userDetails.email,
        "mobile": userDetails.mobile,
    }

class UserUpdate(BaseModel):
    email: str
    mobile: str

@router.put("/profile")
def update_profile(user_update: UserUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update.email != user.email:
        existing_email = db.query(User).filter(User.email == user_update.email).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered by another user")
        user.email = user_update.email

    user.mobile = user_update.mobile
    db.commit()
    db.refresh(user)
    return {"message": "Profile updated successfully", "user": {"username": user.username, "email": user.email, "mobile": user.mobile}}