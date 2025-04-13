from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from models import sRequest, RequestStatus # Import specific model and Enum
from auth import get_current_user
from typing import List, Optional # Import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Define response model
class RequestUserResponse(BaseModel):
    request_id: int
    worker_id: Optional[int]
    service_id: int
    description: Optional[str]
    status: RequestStatus # Use Enum
    urgency_level: Optional[str]
    additional_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    user_location_id: int
    # New fields
    user_quoted_price: Optional[float]
    worker_quoted_price: Optional[float]
    final_price: Optional[float]
    user_price_agreed: bool
    worker_price_agreed: bool
    worker_comments: Optional[str]

    class Config:
        orm_mode = True
        use_enum_values = True # Return enum values as strings

@router.get("/myrequests", response_model=List[RequestUserResponse])
def get_my_requests(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    # Order by updated_at descending to see recent changes first
    allRequests = db.query(sRequest).filter(sRequest.user_id == user_id).order_by(sRequest.updated_at.desc()).all()
    return allRequests # Pydantic will handle conversion based on response_model