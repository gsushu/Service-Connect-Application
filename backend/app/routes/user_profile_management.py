# filepath: d:\Other\adbms\Service-Connect-Application-main\backend\app\routes\user_profile_management.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies import get_db
from models import UserLocation, User
from auth import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix="/addresses", # Prefix for all address routes
    tags=["User Profile"], # Tag for API docs
    dependencies=[Depends(get_current_user)] # Require authentication for all routes here
)

class AddressBase(BaseModel):
    address: str
    pincode: str

class AddressCreate(AddressBase):
    pass

class AddressUpdate(AddressBase):
    pass

class AddressResponse(AddressBase):
    location_id: int
    user_id: int

    class Config:
        orm_mode = True # Changed from from_attributes=True for Pydantic v1 compatibility if needed

@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(address_data: AddressCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    new_address = UserLocation(
        **address_data.dict(),
        user_id=user_id
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address

@router.get("", response_model=List[AddressResponse])
def get_addresses(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    addresses = db.query(UserLocation).filter(UserLocation.user_id == user_id).all()
    return addresses

@router.get("/{location_id}", response_model=AddressResponse)
def get_address(location_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    address = db.query(UserLocation).filter(UserLocation.location_id == location_id, UserLocation.user_id == user_id).first()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found or unauthorized")
    return address

@router.put("/{location_id}", response_model=AddressResponse)
def update_address(location_id: int, address_data: AddressUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    address = db.query(UserLocation).filter(UserLocation.location_id == location_id, UserLocation.user_id == user_id).first()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found or unauthorized")

    address.address = address_data.address
    address.pincode = address_data.pincode
    db.commit()
    db.refresh(address)
    return address

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(location_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    address = db.query(UserLocation).filter(UserLocation.location_id == location_id, UserLocation.user_id == user_id).first()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found or unauthorized")

    # Optional: Check if address is used in any pending requests before deleting?
    # pending_requests = db.query(sRequest).filter(sRequest.user_location_id == location_id, sRequest.status == 'pending').count()
    # if pending_requests > 0:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete address used in pending requests")

    db.delete(address)
    db.commit()
    return None # No content response
