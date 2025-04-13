from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from dependencies import get_db
from models import User, Worker, sRequest, Service, WorkerStatus, RequestStatus, Admin, ServiceCategory, worker_service_categories_table
from auth import get_password_hash # Import hashing function
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime # Import datetime

# --- Admin Authentication Dependency ---
def get_current_admin(request: Request):
    admin = request.session.get("admin")
    if not admin or "id" not in admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not logged in")
    return admin

router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"],
    dependencies=[Depends(get_current_admin)] # Apply auth to all routes in this router
)

# --- User Management ---

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    mobile: str
    created_at: Optional[datetime] = None # Changed from str

    class Config:
        orm_mode = True

@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Consider implications: delete related requests, locations? Or just disassociate?
    # For now, just delete the user. Add cascading deletes or checks later if needed.
    db.delete(user)
    db.commit()
    return None

# --- Worker Management ---

class WorkerResponse(BaseModel):
    worker_id: int
    username: str
    email: str
    mobile: str
    employee_number: str
    status: WorkerStatus # Use the enum
    created_at: Optional[datetime] = None # Changed from str

    class Config:
        orm_mode = True
        use_enum_values = True # Ensure enum values are returned as strings

class WorkerStatusUpdate(BaseModel):
    status: WorkerStatus # Expect 'approved' or 'rejected'

@router.get("/workers", response_model=List[WorkerResponse])
def get_all_workers(db: Session = Depends(get_db)):
    workers = db.query(Worker).all()
    return workers

@router.patch("/workers/{worker_id}/status", response_model=WorkerResponse)
def update_worker_status(worker_id: int, status_update: WorkerStatusUpdate, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    if status_update.status not in [WorkerStatus.approved, WorkerStatus.rejected]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'approved' or 'rejected'")

    worker.status = status_update.status
    db.commit()
    db.refresh(worker)
    return worker

@router.delete("/workers/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    # Consider implications: reassign pending requests?
    db.delete(worker)
    db.commit()
    return None

# --- Service Request Management ---

class RequestAdminResponse(BaseModel): # Updated response for admin
    request_id: int
    user_id: int
    worker_id: Optional[int]
    service_id: int
    user_location_id: int
    status: RequestStatus # Use Enum
    description: Optional[str]
    urgency_level: Optional[str]
    additional_notes: Optional[str]
    created_at: datetime # Use datetime
    updated_at: datetime # Use datetime
    # New fields
    user_quoted_price: Optional[float]
    worker_quoted_price: Optional[float]
    final_price: Optional[float]
    user_price_agreed: bool
    worker_price_agreed: bool
    worker_comments: Optional[str]

    class Config:
        orm_mode = True
        use_enum_values = True # Return enum values as strings

@router.get("/requests", response_model=List[RequestAdminResponse])
def get_all_requests(db: Session = Depends(get_db)):
    requests = db.query(sRequest).order_by(sRequest.updated_at.desc()).all() # Order by update time
    return requests

@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(request_id: int, db: Session = Depends(get_db)):
    request_obj = db.query(sRequest).filter(sRequest.request_id == request_id).first()
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    db.delete(request_obj)
    db.commit()
    return None

# --- Service Management ---

class ServiceResponse(BaseModel):
    service_id: int
    name: str
    description: Optional[str]
    category_id: int # Make category ID required in response

    class Config:
        orm_mode = True

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int # Make category ID required on creation

@router.get("/services", response_model=List[ServiceResponse])
def get_all_services(db: Session = Depends(get_db)):
    services = db.query(Service).all()
    return services

@router.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(service_data: ServiceCreate, db: Session = Depends(get_db)):
    # Check if service name already exists
    existing_service = db.query(Service).filter(Service.name == service_data.name).first()
    if existing_service:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service name already exists")

    # Check if category exists
    category = db.query(ServiceCategory).filter(ServiceCategory.category_id == service_data.category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service category not found")

    new_service = Service(**service_data.dict())
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service

@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.service_id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    # Consider implications: check if service is used in requests or worker_services?
    db.delete(service)
    db.commit()
    return None

# --- Service Category Management ---

class ServiceCategoryBase(BaseModel):
    name: str

class ServiceCategoryCreate(ServiceCategoryBase):
    pass

class ServiceCategoryUpdate(ServiceCategoryBase):
    pass

class ServiceCategoryResponse(ServiceCategoryBase):
    category_id: int

    class Config:
        orm_mode = True

@router.get("/service-categories", response_model=List[ServiceCategoryResponse])
def get_all_service_categories_admin(db: Session = Depends(get_db)):
    """
    Admin: Retrieve all service categories.
    """
    categories = db.query(ServiceCategory).order_by(ServiceCategory.name).all()
    return categories

@router.post("/service-categories", response_model=ServiceCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_service_category(category_data: ServiceCategoryCreate, db: Session = Depends(get_db)):
    """
    Admin: Create a new service category.
    """
    existing_category = db.query(ServiceCategory).filter(ServiceCategory.name == category_data.name).first()
    if existing_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service category name already exists")

    new_category = ServiceCategory(**category_data.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.put("/service-categories/{category_id}", response_model=ServiceCategoryResponse)
def update_service_category(category_id: int, category_data: ServiceCategoryUpdate, db: Session = Depends(get_db)):
    """
    Admin: Update a service category's name.
    """
    category = db.query(ServiceCategory).filter(ServiceCategory.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service category not found")

    # Check if the new name already exists (and it's not the current category)
    existing_category = db.query(ServiceCategory).filter(ServiceCategory.name == category_data.name, ServiceCategory.category_id != category_id).first()
    if existing_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Another service category with this name already exists")

    category.name = category_data.name
    db.commit()
    db.refresh(category)
    return category

@router.delete("/service-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_category(category_id: int, db: Session = Depends(get_db)):
    """
    Admin: Delete a service category.
    """
    category = db.query(ServiceCategory).filter(ServiceCategory.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service category not found")

    # **Important Consideration:** Check for dependencies before deleting.
    # Check if any Services use this category
    linked_services = db.query(Service).filter(Service.category_id == category_id).count()
    if linked_services > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: {linked_services} service(s) are linked to it. Reassign or delete them first."
        )

    # Check if any Workers use this category (via the association table)
    # This requires checking the association table directly or through the relationship
    linked_workers = db.query(Worker).join(worker_service_categories_table).filter(worker_service_categories_table.c.category_id == category_id).count()
    if linked_workers > 0:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: {linked_workers} worker(s) are linked to it. Ask workers to update their profiles first."
         )

    db.delete(category)
    db.commit()
    return None

# --- Admin Account Management ---

class AdminBase(BaseModel):
    username: str

class AdminCreate(AdminBase):
    password: str

class AdminResponse(AdminBase):
    admin_id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

@router.get("/admins", response_model=List[AdminResponse])
def get_all_admins(db: Session = Depends(get_db)):
    """
    Retrieve all admin accounts.
    """
    admins = db.query(Admin).all()
    return admins

@router.post("/create", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def create_admin(admin_data: AdminCreate, db: Session = Depends(get_db)):
    """
    Create a new admin account. Only accessible by other admins.
    """
    existing_admin = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if existing_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin username already exists")

    hashed_password = get_password_hash(admin_data.password)
    new_admin = Admin(username=admin_data.username, password=hashed_password)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin

@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(admin_id: int, current_admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """
    Delete an admin account. Admins cannot delete themselves.
    """
    if admin_id == current_admin["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot delete their own account")

    admin_to_delete = db.query(Admin).filter(Admin.admin_id == admin_id).first()
    if not admin_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")

    db.delete(admin_to_delete)
    db.commit()
    return None # No content response
