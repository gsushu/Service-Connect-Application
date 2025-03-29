from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from dependencies import get_db
from models import *
from pydantic import BaseModel

router = APIRouter()

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
    request.session["user"] = {"username": user_obj.username, "id": user_obj.id}
    return {"message": "Login successful"}

@router.get("/profile")
def get_profile(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"username": user["username"], "id": user["id"]}

# Logout route
@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}