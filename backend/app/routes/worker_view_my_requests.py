from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session, joinedload # Import joinedload
from dependencies import get_db
from models import sRequest, Worker, RequestStatus, UserLocation, User # Import User
from routes.worker_authentication import get_current_worker_session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/worker", tags=["Worker Requests"])

# Define response model
class RequestWorkerResponse(BaseModel):
    request_id: int
    user_id: int
    worker_id: Optional[int] # Should always be self for this endpoint
    service_id: int
    description: Optional[str]
    status: RequestStatus # Use Enum
    urgency_level: Optional[str]
    additional_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    user_location_id: int
    # Pricing fields
    user_quoted_price: Optional[float] # User's initial budget
    # worker_quoted_price: Optional[float] # Removed (now in RequestQuote)
    final_price: Optional[float] # Price from accepted quote
    # user_price_agreed: bool # Removed
    # worker_price_agreed: bool # Removed
    # worker_comments: Optional[str] # Removed (now in RequestQuote)

    # User contact details (conditionally shown)
    user_address: Optional[str] = None
    user_pincode: Optional[str] = None
    user_mobile: Optional[str] = None # Add user mobile

    class Config:
        orm_mode = True
        use_enum_values = True # Return enum values as strings


@router.get("/myrequests", response_model=List[RequestWorkerResponse])
def get_my_assigned_requests(current_worker: Worker = Depends(get_current_worker_session), db: Session = Depends(get_db)):
    # Get requests where worker_id matches, eagerly load location and user
    myRequests = db.query(sRequest)\
        .options(
            joinedload(sRequest.user_location),
            joinedload(sRequest.user) # Eager load user details
        )\
        .filter(sRequest.worker_id == current_worker.worker_id)\
        .order_by(sRequest.updated_at.desc())\
        .all()

    # Map results, conditionally including contact details
    response_list = []
    for req in myRequests:
        resp_data = {
            "request_id": req.request_id,
            "user_id": req.user_id,
            "worker_id": req.worker_id,
            "service_id": req.service_id,
            "description": req.description,
            "status": req.status,
            "urgency_level": req.urgency_level,
            "additional_notes": req.additional_notes,
            "created_at": req.created_at,
            "updated_at": req.updated_at,
            "user_location_id": req.user_location_id,
            "user_quoted_price": req.user_quoted_price,
            "final_price": req.final_price,
            # Initialize contact details as None
            "user_address": None,
            "user_pincode": None,
            "user_mobile": None,
        }

        # Only include contact details if status is accepted or later
        if req.status in [RequestStatus.accepted, RequestStatus.inprogress, RequestStatus.completed]:
            if req.user_location:
                resp_data["user_address"] = req.user_location.address
                resp_data["user_pincode"] = req.user_location.pincode
            if req.user: # Check if user object was loaded
                resp_data["user_mobile"] = req.user.mobile

        response_list.append(RequestWorkerResponse(**resp_data))

    return response_list