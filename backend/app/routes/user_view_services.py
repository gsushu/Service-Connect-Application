from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import get_db
from models import * # Import ServiceCategory
from pydantic import BaseModel # Import BaseModel
from typing import List # Import List

router = APIRouter()

@router.get("/allservices")
def getAllRequests(db: Session = Depends(get_db)):
    allServices = db.query(Service).all()

    return [{
        "service_id": r.service_id,
        "name": r.name,
        "description": r.description
    } for r in allServices]

# --- Add endpoint for Service Categories ---
class ServiceCategoryResponse(BaseModel):
    category_id: int
    name: str

    class Config:
        orm_mode = True

@router.get("/service-categories", response_model=List[ServiceCategoryResponse])
def get_all_service_categories(db: Session = Depends(get_db)):
    """
    Retrieve all available service categories.
    """
    categories = db.query(ServiceCategory).order_by(ServiceCategory.name).all()
    return categories