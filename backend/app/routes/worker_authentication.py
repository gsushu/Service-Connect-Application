from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from dependencies import get_db
from models import *
from pydantic import BaseModel

router = APIRouter(prefix="/worker", tags=["Worker"])

class WorkerSignUpDetails(BaseModel):
    username: str
    password: str
    email: str
    mobile: str
    employee_number: str

@router.post("/signup")
def signup(worker_data: WorkerSignUpDetails, db: Session = Depends(get_db)):
    existing_worker = db.query(Worker).filter(
        (Worker.username == worker_data.username) | (Worker.email == worker_data.email)
    ).first()
    if existing_worker:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    new_worker = Worker(
        username=worker_data.username,
        email=worker_data.email,
        mobile=worker_data.mobile,
        employee_number=worker_data.employee_number,
        password=worker_data.password
    )

    db.add(new_worker)
    db.commit()
    db.refresh(new_worker)

    return {"message": "Worker registered successfully", "worker_id": new_worker.worker_id}

class WorkerLoginDetails(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(worker_auth: WorkerLoginDetails, request: Request, db: Session = Depends(get_db)):
    worker_obj = db.query(Worker).filter(Worker.username == worker_auth.username).first()

    if not worker_obj:
        raise HTTPException(status_code=400, detail="Worker does not exist")
    if not worker_obj.password == worker_auth.password:
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    request.session["worker"] = {"username": worker_obj.username, "id": worker_obj.worker_id}
    
    return {"message": "Worker Login successful"}

@router.get("/profile")
def get_profile(request: Request):
    worker = request.session.get("worker")

    if not worker:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {"username": worker["username"], "id": worker["id"]}

@router.post("/logout")
def worker_logout(request: Request):
    if "worker" not in request.session:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    del request.session["worker"]

    return {"message": "Worker logged out successfully"}