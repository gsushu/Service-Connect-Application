from fastapi import APIRouter, Depends, HTTPException
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