from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from models import *
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from routes.worker_notifications import notify_workers 

router = APIRouter()

class ServiceRequest(BaseModel):
    service_id: int = Field(..., example=1)
    description: str = Field(..., example="Fix a broken chair leg")
    location_id: int = Field(..., example=1)
    scheduled_time: Optional[datetime] = Field(None, example="2025-03-15T10:00:00")
    urgency_level: Optional[str] = Field(None, example="High")
    additional_notes: Optional[str] = Field(None, example="I have pets at home, please be mindful")

@router.post("/requests")
async def create_service(request: Request, service: ServiceRequest, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="User not logged in")
    if "id" not in user:
        raise HTTPException(status_code=500, detail="User ID not found in session")
    
    service_exists = db.query(Service).filter(Service.service_id == service.service_id).first()
    if not service_exists:
        raise HTTPException(status_code=400, detail="Service not found")
    
    location = db.query(UserLocation).filter(
        UserLocation.location_id == service.location_id,
        UserLocation.user_id == user["id"]
    ).first()
    if not location:
        raise HTTPException(status_code=400, detail="Invalid or unauthorized location ID")

    new_request = sRequest(
        user_id=user["id"],
        worker_id=None,
        service_id=service.service_id,
        user_location_id=service.location_id,
        status="pending",
        description=service.description
    )
    
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    request_data = {
        "request_id": new_request.request_id,
        "user_id": new_request.user_id,
        "service_id": new_request.service_id,
        "user_location_id": new_request.user_location_id,
        "description": new_request.description,
        "status": new_request.status,
        "created_at": str(new_request.created_at)  # Convert datetime to string
    }
    await notify_workers(request_data)

    return {"data": {"request_id": new_request.request_id}}
