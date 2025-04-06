from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from models import *

router = APIRouter()

@router.get("/allrequests")
def getAllRequests(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    allRequests = db.query(sRequest).filter(sRequest.user_id == user["id"]).all()

    return [{
        "request_id": r.request_id,
        "worker_id": r.worker_id,
        "service_id": r.service_id,
        "description": r.description,
        "status": r.status,
        "created_at": r.created_at
    } for r in allRequests]