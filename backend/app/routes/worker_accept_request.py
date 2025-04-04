from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from models import *

router = APIRouter(prefix="/worker", tags=["Worker"])

from pydantic import BaseModel

class AcceptRequest(BaseModel):
    request_id: int

@router.patch("/acceptrequest")
def acceptRequest(request: Request, accept_data: AcceptRequest, db: Session = Depends(get_db)):
    worker = request.session.get("worker")
    if not worker or "id" not in worker:
        raise HTTPException(status_code=401, detail="Worker not logged in")
    
    service_request = db.query(sRequest).filter(sRequest.request_id == accept_data.request_id).first()
    if not service_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if service_request.status != "pending" or service_request.worker_id is not None:
        raise HTTPException(status_code=400, detail="Request already taken or not pending")
    
    service_request.worker_id = worker["id"]
    service_request.status = "accepted"
    db.commit()

    return {"message": "Request accepted", "request_id": accept_data.request_id}