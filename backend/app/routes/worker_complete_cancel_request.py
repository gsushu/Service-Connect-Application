from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from dependencies import get_db
from models import sRequest, Worker, RequestStatus
from pydantic import BaseModel
from routes.worker_authentication import get_current_worker_session

router = APIRouter(prefix="/worker", tags=["Worker Actions"])

class ModifyRequestStatus(BaseModel):
    request_id: int
    status: RequestStatus

@router.patch("/modifyrequest", status_code=status.HTTP_200_OK)
def modify_request_status(modify_data: ModifyRequestStatus, current_worker: Worker = Depends(get_current_worker_session), db: Session = Depends(get_db)):

    service_request = db.query(sRequest).filter(
        sRequest.request_id == modify_data.request_id,
        sRequest.worker_id == current_worker.worker_id
    ).first()

    if not service_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found or not assigned to you")

    target_status = modify_data.status
    current_status = service_request.status

    # Updated allowed transitions - removed negotiating status
    allowed_transitions = {
        RequestStatus.accepted: [RequestStatus.inprogress, RequestStatus.cancelled],
        RequestStatus.inprogress: [RequestStatus.completed, RequestStatus.cancelled],
    }

    if current_status not in allowed_transitions or target_status not in allowed_transitions.get(current_status, []):
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail=f"Cannot change status from '{current_status.value}' to '{target_status.value}'"
         )

    valid_statuses = ["accepted", "inprogress", "completed", "cancelled"]
    if target_status.value not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")

    service_request.status = target_status
    db.commit()
    db.refresh(service_request)
    return {"message": f"Request status updated to {target_status.value}", "request_id": service_request.request_id, "status": service_request.status.value}