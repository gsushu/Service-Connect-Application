from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from dependencies import get_db
from models import *
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

router = APIRouter()

class ServiceRequest(BaseModel):
    service_type: str = Field(..., example="Carpenter")
    description: str = Field(..., example="Fix a broken chair leg")
    location: str = Field(..., example="123 Main St, Springfield")
    scheduled_time: Optional[datetime] = Field(None, example="2025-03-15T10:00:00")
    urgency_level: Optional[str] = Field(None, example="High")
    additional_notes: Optional[str] = Field(None, example="I have pets at home, please be mindful")

@router.post("/post_service")
def create_service(request: Request, service: ServiceRequest, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return {"error": "User not logged in"}
    new_request = sRequest(
        user_id=user["id"],
        worker_id=None,
        service_id=1,
        user_location_id=1,
        status="pending",
        description=service.description
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return {"data": {"request_id": new_request.request_id}}
