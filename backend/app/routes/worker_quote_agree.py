from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload
from dependencies import get_db
from models import sRequest, Worker, RequestStatus, RequestQuote # Import RequestQuote
from pydantic import BaseModel, Field
from typing import Optional
from routes.worker_authentication import get_current_worker_session
# Import the user notification function
from routes.user_notifications import notify_user
import asyncio # Import asyncio
from datetime import datetime # Import datetime

router = APIRouter(prefix="/worker/requests", tags=["Worker Requests"]) # Keep prefix

class WorkerQuoteSubmit(BaseModel):
    price: float = Field(..., gt=0) # Ensure price is positive
    comments: Optional[str] = None

class WorkerQuoteResponse(BaseModel):
    quote_id: int
    request_id: int
    worker_id: int
    worker_quoted_price: float
    worker_comments: Optional[str]
    updated_at: datetime # Use datetime from models

    class Config:
        orm_mode = True

# --- Worker Submit/Update Quote ---
@router.put("/{request_id}/quote", response_model=WorkerQuoteResponse, status_code=status.HTTP_200_OK)
async def worker_submit_or_update_quote(request_id: int, quote_data: WorkerQuoteSubmit, current_worker: Worker = Depends(get_current_worker_session), db: Session = Depends(get_db)): # Make async
    # 1. Find the request
    # Eager load user to get user_id without extra query
    req = db.query(sRequest).options(joinedload(sRequest.user)).filter(sRequest.request_id == request_id).first()

    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # 2. Check if worker can quote (request is pending and not yet assigned)
    if req.status != RequestStatus.pending or req.worker_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot submit quote for this request (not pending or already assigned)")

    # 3. Check if this worker already submitted a quote for this request
    existing_quote = db.query(RequestQuote).filter(
        RequestQuote.request_id == request_id,
        RequestQuote.worker_id == current_worker.worker_id
    ).first()

    notification_type = ""
    quote_result = None

    if existing_quote:
        # Update existing quote
        existing_quote.worker_quoted_price = quote_data.price
        existing_quote.worker_comments = quote_data.comments
        db.commit()
        db.refresh(existing_quote)
        quote_result = existing_quote
        notification_type = "quote_updated"
    else:
        # Create new quote
        new_quote = RequestQuote(
            request_id=request_id,
            worker_id=current_worker.worker_id,
            worker_quoted_price=quote_data.price,
            worker_comments=quote_data.comments
        )
        db.add(new_quote)
        db.commit()
        db.refresh(new_quote)
        quote_result = new_quote
        notification_type = "new_quote"

    # --- Send notification to the user ---
    if req.user_id:
        notification_data = {
            "type": notification_type,
            "request_id": req.request_id,
            "quote_id": quote_result.quote_id,
            "worker_id": current_worker.worker_id,
            "worker_username": current_worker.username, # Assuming current_worker has username
            "price": quote_result.worker_quoted_price,
            "comments": quote_result.worker_comments
        }
        # Run notification in background task to avoid blocking response
        asyncio.create_task(notify_user(req.user_id, notification_data))
    # --- End Notification ---

    return quote_result

# --- Worker Agree Price (REMOVED) ---
# The PUT /{request_id}/agree endpoint is removed as the user now accepts the quote.
