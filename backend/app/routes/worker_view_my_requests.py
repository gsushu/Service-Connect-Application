from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session, joinedload # Import joinedload
from dependencies import get_db
from models import sRequest, Worker, RequestStatus, UserLocation # Import UserLocation
from routes.worker_authentication import get_current_worker_session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/worker", tags=["Worker Requests"])

# Define response model (similar to user view, can be shared later if identical)
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
    # New fields
    user_quoted_price: Optional[float]
    worker_quoted_price: Optional[float]
    final_price: Optional[float]
    user_price_agreed: bool
    worker_price_agreed: bool
    worker_comments: Optional[str]
    # Add user address fields
    user_address: Optional[str]
    user_pincode: Optional[str]

    class Config:
        orm_mode = True
        use_enum_values = True # Return enum values as strings


@router.get("/myrequests", response_model=List[RequestWorkerResponse])
def get_my_assigned_requests(current_worker: Worker = Depends(get_current_worker_session), db: Session = Depends(get_db)):
    # Get requests where worker_id matches, eagerly load location
    myRequests = db.query(sRequest)\
        .options(joinedload(sRequest.user_location))\
        .filter(sRequest.worker_id == current_worker.worker_id)\
        .order_by(sRequest.updated_at.desc())\
        .all()

    # Map results to include address
    response_list = []
    for req in myRequests:
        response_list.append(RequestWorkerResponse(
            request_id=req.request_id,
            user_id=req.user_id,
            worker_id=req.worker_id,
            service_id=req.service_id,
            description=req.description,
            status=req.status,
            urgency_level=req.urgency_level,
            additional_notes=req.additional_notes,
            created_at=req.created_at,
            updated_at=req.updated_at,
            user_location_id=req.user_location_id,
            user_quoted_price=req.user_quoted_price,
            worker_quoted_price=req.worker_quoted_price,
            final_price=req.final_price,
            user_price_agreed=req.user_price_agreed,
            worker_price_agreed=req.worker_price_agreed,
            worker_comments=req.worker_comments,
            user_address=req.user_location.address if req.user_location else None, # Get address
            user_pincode=req.user_location.pincode if req.user_location else None # Get pincode
        ))
    return response_list