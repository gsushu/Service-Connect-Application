from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from dependencies import get_db
from models import sRequest, Worker, RequestStatus
from pydantic import BaseModel, Field
from typing import Optional
from routes.worker_authentication import get_current_worker_session

router = APIRouter(prefix="/worker/requests", tags=["Worker Requests"]) # New prefix

class WorkerQuote(BaseModel):
    price: float
    comments: Optional[str] = None

# --- Worker Propose/Update Price and Comment ---
@router.put("/{request_id}/quote", status_code=status.HTTP_200_OK)
def worker_update_quote(request_id: int, quote: WorkerQuote, current_worker: Worker = Depends(get_current_worker_session), db: Session = Depends(get_db)):
    req = db.query(sRequest).filter(sRequest.request_id == request_id).first()

    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Worker can only quote on pending or negotiating requests
    # If pending, this worker claims it. If negotiating, only assigned worker can update.
    if req.status == RequestStatus.pending:
        if req.worker_id is not None: # Should not happen if logic is correct, but check
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already assigned")
        req.worker_id = current_worker.worker_id # Assign worker
        req.status = RequestStatus.negotiating # Move to negotiating
    elif req.status == RequestStatus.negotiating:
        if req.worker_id != current_worker.worker_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Request not assigned to this worker")
    else:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot quote price in current status: {req.status.value}")

    if quote.price <= 0:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be positive")

    req.worker_quoted_price = quote.price
    req.worker_comments = quote.comments
    # If worker updates price, reset both agreement flags
    req.user_price_agreed = False
    req.worker_price_agreed = False
    req.final_price = None # Clear final price

    db.commit()
    db.refresh(req)
    # Notify user?
    return {
        "message": "Worker price quote submitted successfully",
        "request_id": req.request_id,
        "worker_price": req.worker_quoted_price,
        "comments": req.worker_comments,
        "status": req.status.value
    }

# --- Worker Agree Price ---
@router.put("/{request_id}/agree", status_code=status.HTTP_200_OK)
def worker_agree_price(request_id: int, current_worker: Worker = Depends(get_current_worker_session), db: Session = Depends(get_db)):
    req = db.query(sRequest).filter(
        sRequest.request_id == request_id,
        sRequest.worker_id == current_worker.worker_id # Ensure worker is assigned
    ).first()

    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found or not assigned to this worker")

    if req.status != RequestStatus.negotiating:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot agree price in current status: {req.status.value}")

    if req.user_quoted_price is None or req.worker_quoted_price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both user and worker must quote a price before agreement")

    if req.user_quoted_price != req.worker_quoted_price:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot agree when prices do not match")

    req.worker_price_agreed = True
    final_message = "Worker agreed to price."

    # Check if user also agreed
    if req.user_price_agreed:
        req.final_price = req.worker_quoted_price # or user_quoted_price, they are equal
        req.status = RequestStatus.accepted # Move to accepted state
        final_message = "Price agreed by both parties. Request accepted."
        # Notify user?

    db.commit()
    db.refresh(req)
    return {"message": final_message, "request_id": req.request_id, "final_price": req.final_price, "status": req.status.value}
