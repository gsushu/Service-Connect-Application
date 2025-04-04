from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from models import sRequest, Worker
from pydantic import BaseModel

router = APIRouter(prefix="/worker", tags=["Worker"])

class ModifyRequest(BaseModel):
    request_id: int
    status: str

@router.patch("/modifyrequest")
def modify_request(request: Request, modify_data: ModifyRequest, db: Session = Depends(get_db)):
    worker = request.session.get("worker")
    if not worker or "id" not in worker:
        raise HTTPException(status_code=401, detail="Worker not logged in")
    
    service_request = db.query(sRequest).filter(
        sRequest.request_id == modify_data.request_id,
        sRequest.worker_id == worker["id"]
    ).first()
    if not service_request:
        raise HTTPException(status_code=404, detail="Request not found or not assigned to you")
    
    valid_statuses = ["accepted", "completed", "cancelled"]
    if modify_data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")
    
    service_request.status = modify_data.status
    db.commit()
    return {"message": "Request status updated", "request_id": modify_data.request_id}