from fastapi import APIRouter, Depends, Request, HTTPException, status # Added status
from sqlalchemy.orm import Session
from dependencies import get_db
from models import sRequest, Service, UserLocation, RequestStatus # Added RequestStatus
from pydantic import BaseModel, Field
from typing import Optional
from routes.worker_notifications import notify_workers # Assuming this exists and works via websockets
from auth import get_current_user

router = APIRouter()

class ServiceRequestCreate(BaseModel): # Renamed for clarity
    service_id: int = Field(..., example=1)
    description: str = Field(..., example="Fix a broken chair leg")
    location_id: int = Field(..., example=1)
    urgency_level: Optional[str] = Field(None, example="High")
    additional_notes: Optional[str] = Field(None, example="I have pets at home, please be mindful")
    user_quoted_price: Optional[float] = Field(None, example=50.00) # Added user price

class PriceQuote(BaseModel):
    price: float

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
        worker_id=None,
        service_id=service_data.service_id,
        user_location_id=service_data.location_id,
        status=RequestStatus.pending, # Use Enum
        description=service_data.description,
        urgency_level=service_data.urgency_level,
        additional_notes=service_data.additional_notes,
        user_quoted_price=service_data.user_quoted_price # Save user price
        # Agreement flags default to False, other prices default to None
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    # Notify relevant workers (logic might need update based on pincode/service)
    request_data_for_notify = {
        "request_id": new_request.request_id,
        "user_id": new_request.user_id,
        "service_id": new_request.service_id,
        "user_location_id": new_request.user_location_id,
        "description": new_request.description,
        "status": new_request.status.value, # Send enum value
        "urgency_level": new_request.urgency_level,
        "user_quoted_price": new_request.user_quoted_price, # Include price
        "created_at": str(new_request.created_at)
    }
    # await notify_workers(request_data_for_notify) # Uncomment if worker notification is ready

    return {
        "message": "Request created successfully",
        "request_id": new_request.request_id,
        "status": new_request.status.value
    }

# --- User Update Price ---
@router.put("/requests/{request_id}/quote", status_code=status.HTTP_200_OK)
def user_update_quote(request_id: int, quote: PriceQuote, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    req = db.query(sRequest).filter(sRequest.request_id == request_id, sRequest.user_id == user_id).first()

    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found or unauthorized")

    # Allow price update only in pending or negotiating states
    if req.status not in [RequestStatus.pending, RequestStatus.negotiating]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot update price in current status: {req.status.value}")

    if quote.price <= 0:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be positive")

    req.user_quoted_price = quote.price
    # If user updates price, reset both agreement flags to force re-agreement
    req.user_price_agreed = False
    req.worker_price_agreed = False
    req.final_price = None # Clear final price
    # If it was pending, and worker had already quoted, keep it negotiating. If worker hadn't quoted, keep pending.
    # If it was negotiating, keep it negotiating.
    if req.status == RequestStatus.pending and req.worker_id is not None:
         req.status = RequestStatus.negotiating # Ensure it's negotiating if worker involved

    db.commit()
    db.refresh(req)
    # Notify worker if involved?
    return {"message": "Price quote updated successfully", "request_id": req.request_id, "new_price": req.user_quoted_price, "status": req.status.value}

# --- User Agree Price ---
@router.put("/requests/{request_id}/agree", status_code=status.HTTP_200_OK)
def user_agree_price(request_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    req = db.query(sRequest).filter(sRequest.request_id == request_id, sRequest.user_id == user_id).first()

    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found or unauthorized")

    if req.status != RequestStatus.negotiating:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot agree price in current status: {req.status.value}")

    if req.user_quoted_price is None or req.worker_quoted_price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both user and worker must quote a price before agreement")

    if req.user_quoted_price != req.worker_quoted_price:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot agree when prices do not match")

    req.user_price_agreed = True
    final_message = "User agreed to price."

    # Check if worker also agreed
    if req.worker_price_agreed:
        req.final_price = req.user_quoted_price # or worker_quoted_price, they are equal
        req.status = RequestStatus.accepted # Move to accepted state
        final_message = "Price agreed by both parties. Request accepted."
        # Notify worker?

    db.commit()
    db.refresh(req)
    return {"message": final_message, "request_id": req.request_id, "final_price": req.final_price, "status": req.status.value}
