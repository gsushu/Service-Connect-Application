from fastapi import APIRouter, Depends, Request, HTTPException, status # Added status
from sqlalchemy.orm import Session, joinedload # Import joinedload
from dependencies import get_db
from models import sRequest, Service, UserLocation, RequestStatus, RequestQuote, Worker # Added RequestQuote, Worker
from pydantic import BaseModel, Field
from typing import Optional, List # Import List
from routes.worker_notifications import notify_all_workers, notify_specific_worker # Assuming this exists and works via websockets
from auth import get_current_user
from datetime import datetime # Import datetime
import asyncio # Import asyncio

router = APIRouter()

class ServiceRequestCreate(BaseModel): # Renamed for clarity
    service_id: int = Field(..., example=1)
    description: str = Field(..., example="Fix a broken chair leg")
    location_id: int = Field(..., example=1)
    urgency_level: Optional[str] = Field(None, example="High")
    additional_notes: Optional[str] = Field(None, example="I have pets at home, please be mindful")
    user_quoted_price: Optional[float] = Field(None, example=50.00) # User's initial budget/offer

# Removed PriceQuote model as user doesn't update quote directly anymore

# --- Create Request ---
@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_service_request(service_data: ServiceRequestCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]

    # ... (validation for service and location remains the same) ...
    service_exists = db.query(Service).filter(Service.service_id == service_data.service_id).first()
    if not service_exists:
        raise HTTPException(status_code=400, detail="Service not found")

    location = db.query(UserLocation).filter(
        UserLocation.location_id == service_data.location_id,
        UserLocation.user_id == user_id
    ).first()
    if not location:
        raise HTTPException(status_code=400, detail="Invalid or unauthorized location ID")

    new_request = sRequest(
        user_id=user_id,
        worker_id=None, # Worker not assigned initially
        service_id=service_data.service_id,
        user_location_id=service_data.location_id,
        status=RequestStatus.pending, # Use Enum
        description=service_data.description,
        urgency_level=service_data.urgency_level,
        additional_notes=service_data.additional_notes,
        user_quoted_price=service_data.user_quoted_price # Save user initial price indication
        # final_price is None initially
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    # Notify relevant workers (logic might need update based on pincode/service)
    # Consider if notification should happen here or if workers just poll open requests
    # await notify_workers(...) # Keep commented for now

    return {
        "message": "Request created successfully, awaiting quotes",
        "request_id": new_request.request_id,
        "status": new_request.status.value
    }

# --- User Update Price (REMOVED) ---
# PUT /requests/{request_id}/quote is removed. User indicates price on creation.

# --- User Agree Price (REMOVED) ---
# PUT /requests/{request_id}/agree is removed. Replaced by accept_quote.


# --- User View Quotes for a Request ---
class QuoteResponseForUser(BaseModel):
    quote_id: int
    worker_id: int
    worker_username: str # Include worker username
    worker_quoted_price: float
    worker_comments: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

@router.get("/requests/{request_id}/quotes", response_model=List[QuoteResponseForUser])
def get_quotes_for_request(request_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    # Verify the request belongs to the user
    req = db.query(sRequest).filter(sRequest.request_id == request_id, sRequest.user_id == user_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found or unauthorized")

    # Fetch quotes, joining with Worker to get username
    quotes = db.query(RequestQuote)\
        .join(Worker, RequestQuote.worker_id == Worker.worker_id)\
        .filter(RequestQuote.request_id == request_id)\
        .options(joinedload(RequestQuote.worker))\
        .order_by(RequestQuote.updated_at.desc())\
        .all()

    # Map results to include worker username
    response_list = []
    for quote in quotes:
        response_list.append(QuoteResponseForUser(
            quote_id=quote.quote_id,
            worker_id=quote.worker_id,
            worker_username=quote.worker.username, # Get username from relationship
            worker_quoted_price=quote.worker_quoted_price,
            worker_comments=quote.worker_comments,
            created_at=quote.created_at,
            updated_at=quote.updated_at
        ))
    return response_list

# --- User Accept Quote ---
@router.post("/requests/{request_id}/accept_quote/{quote_id}", status_code=status.HTTP_200_OK)
async def user_accept_quote(request_id: int, quote_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)): # Make async
    user_id = current_user["id"]

    # 1. Find the request and verify ownership and status
    req = db.query(sRequest).filter(
        sRequest.request_id == request_id,
        sRequest.user_id == user_id
    ).first()

    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found or unauthorized")

    if req.status != RequestStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot accept quote for request in status: {req.status.value}")
    if req.worker_id is not None:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already has an assigned worker")

    # 2. Find the specific quote to accept
    quote_to_accept = db.query(RequestQuote).filter(
        RequestQuote.quote_id == quote_id,
        RequestQuote.request_id == request_id # Ensure quote belongs to this request
    ).first()

    if not quote_to_accept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found for this request")

    # 3. Update the main request
    req.worker_id = quote_to_accept.worker_id
    req.final_price = quote_to_accept.worker_quoted_price
    req.status = RequestStatus.accepted # Move to accepted state

    db.commit()
    db.refresh(req)

    # --- Send notification to the accepted worker ---
    if req.worker_id:
        notification_data = {
            "type": "quote_accepted",
            "request_id": req.request_id,
            "message": "Your quote has been accepted by the user!",
            "final_price": req.final_price
            # Add user contact details here if desired, but worker can get them via /myrequests now
        }
        # Run notification in background task
        asyncio.create_task(notify_specific_worker(req.worker_id, notification_data))
    # --- End Notification ---

    return {
        "message": "Quote accepted successfully. Worker assigned.",
        "request_id": req.request_id,
        "assigned_worker_id": req.worker_id,
        "final_price": req.final_price,
        "status": req.status.value
    }
