from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session, contains_eager, joinedload # Import contains_eager, joinedload
from sqlalchemy.sql import func
from sqlalchemy import Integer
from dependencies import get_db
from models import * # Import models including UserLocation, RequestStatus, Service, ServiceCategory
from routes.worker_authentication import get_current_worker_session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/worker", tags=["Worker Requests"])

# Define response model
class RequestOpenResponse(BaseModel):
    request_id: int
    user_id: int
    user_location_id: int
    service_id: int
    description: Optional[str]
    status: RequestStatus
    urgency_level: Optional[str]
    additional_notes: Optional[str]
    created_at: datetime
    user_quoted_price: Optional[float]
    # Add user address fields
    user_address: Optional[str]
    user_pincode: Optional[str]

    class Config:
        orm_mode = True
        use_enum_values = True

@router.get("/openrequests", response_model=List[RequestOpenResponse])
def get_open_requests_nearby(current_worker: Worker = Depends(get_current_worker_session), db: Session = Depends(get_db)):
    # Ensure worker profile is complete (pincode, radius, and categories)
    if not current_worker.pincode or current_worker.radius is None:
        raise HTTPException(status_code=400, detail="Worker profile incomplete (pincode/radius missing)")
    # Worker must select at least one category to see requests
    worker_category_ids = [cat.category_id for cat in current_worker.service_categories]
    if not worker_category_ids:
         raise HTTPException(status_code=400, detail="Worker profile incomplete (service categories not selected)")

    try:
        worker_pincode_int = int(current_worker.pincode)
        radius = current_worker.radius
        min_pincode = worker_pincode_int - radius
        max_pincode = worker_pincode_int + radius
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid worker pincode format")

    # Query requests
    query = db.query(sRequest)\
        .join(sRequest.user_location)\
        .join(sRequest.service)\
        .options(contains_eager(sRequest.user_location), contains_eager(sRequest.service))\
        .filter(
            sRequest.status == RequestStatus.pending,
            sRequest.worker_id == None,
            UserLocation.pincode.isnot(None),
            # Pincode range filter
            func.cast(UserLocation.pincode, Integer) >= min_pincode,
            func.cast(UserLocation.pincode, Integer) <= max_pincode,
            # Service category filter
            Service.category_id.in_(worker_category_ids)
        )\
        .order_by(sRequest.created_at.desc())

    allRequests = query.all()

    # Map results to response model including address
    response_list = []
    for req in allRequests:
        response_list.append(RequestOpenResponse(
            request_id=req.request_id,
            user_id=req.user_id,
            user_location_id=req.user_location_id,
            service_id=req.service_id,
            description=req.description,
            status=req.status,
            urgency_level=req.urgency_level,
            additional_notes=req.additional_notes,
            created_at=req.created_at,
            user_quoted_price=req.user_quoted_price,
            user_address=req.user_location.address, # Get address from relationship
            user_pincode=req.user_location.pincode # Get pincode from relationship
        ))

    return response_list