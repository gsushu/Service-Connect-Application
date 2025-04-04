from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from models import *

router = APIRouter(prefix="/worker", tags=["Worker"])

@router.get("/myrequests")
def getMyRequests(request: Request, db: Session = Depends(get_db)):
    worker = request.session.get("worker")
    if not worker or "id" not in worker:
        raise HTTPException(status_code=401, detail="Worker not logged in")
    
    myRequests = db.query(sRequest).filter(sRequest.worker_id == worker["id"]).all()
    
    return [{
        "request_id": r.request_id,
        "worker_id": r.worker_id,
        "user_id": r.user_id,
        "user_location_id": r.user_location_id,
        "service_id": r.service_id,
        "description": r.description,
        "status": r.status,
        "created_at": r.created_at
    } for r in myRequests]