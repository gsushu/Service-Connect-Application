from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import get_db
from models import *

router = APIRouter()

@router.get("/allservices")
def getAllRequests(db: Session = Depends(get_db)):
    allServices = db.query(Service).all()

    return [{
        "service_id": r.service_id,
        "name": r.name,
        "description": r.description
    } for r in allServices]