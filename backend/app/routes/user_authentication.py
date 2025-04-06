from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from dependencies import get_db
from models import *
from pydantic import BaseModel

router = APIRouter()

class UserDetails(BaseModel):
    username: str
    email: str
    mobile: str
    password: str

@router.post("/signup")
def signup(user_data: UserDetails, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_data = User(
        username = user_data.username,
        email = user_data.email,
        mobile = user_data.mobile,
        password = user_data.password,
    )

    db.add(user_data)
    db.commit()
    db.refresh(user_data)

    return {"message": f"{user_data.username}({user_data.user_id}) created successfully"}

class AuthDetails(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(user_auth: AuthDetails, request: Request, db: Session = Depends(get_db)):
    user_obj = db.query(User).filter(User.username == user_auth.username).first()
    if not user_obj:
        raise HTTPException(status_code=400, detail="User does not exist")
    if user_obj.password != user_auth.password:
        raise HTTPException(status_code=400, detail="Incorrect password")
    request.session["user"] = {"username": user_obj.username, "id": user_obj.user_id}
    return {"message": "user Login successful"}

@router.get("/profile")
def get_profile(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    userDetails = db.query(User).filter(User.user_id == user["id"]).first()
    if not userDetails:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": userDetails.user_id,
        "username": userDetails.username,
        "email": userDetails.email,
        "mobile": userDetails.mobile,
    }

@router.post("/logout")
def logout(request: Request):
    if "user" not in request.session:
        raise HTTPException(status_code=401, detail="Not logged in")

    del request.session["user"]

    return {"message": "User Logged out successfully"}