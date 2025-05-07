from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload # Import joinedload
from dependencies import get_db
from models import Worker, WorkerStatus, ServiceCategory # Import ServiceCategory
from pydantic import BaseModel
from auth import get_password_hash, verify_password
from typing import Optional, List # Import List
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/worker", tags=["Worker"])

class WorkerSignUpDetails(BaseModel):
    username: str
    password: str
    email: str
    mobile: str
    employee_number: str
    pincode: str
    category_ids: Optional[List[int]] = None # Added optional list of category IDs

@router.post("/signup")
def signup(worker_data: WorkerSignUpDetails, db: Session = Depends(get_db)):
    existing_worker = db.query(Worker).filter(
        (Worker.username == worker_data.username) |
        (Worker.email == worker_data.email) |
        (Worker.employee_number == worker_data.employee_number) # Check employee_number uniqueness
    ).first()
    if existing_worker:
        detail = "Username already exists"
        if existing_worker.email == worker_data.email:
            detail = "Email already exists"
        elif existing_worker.employee_number == worker_data.employee_number:
            detail = "Employee number already exists"
        raise HTTPException(status_code=400, detail=detail)

    # Check pincode format (basic check)
    if not worker_data.pincode.isdigit() or len(worker_data.pincode) < 5: # Example check
         raise HTTPException(status_code=400, detail="Invalid pincode format")

    hashed_password = get_password_hash(worker_data.password) # Hash the password
    new_worker = Worker(
        username=worker_data.username,
        email=worker_data.email,
        mobile=worker_data.mobile,
        employee_number=worker_data.employee_number,
        password=hashed_password, # Store the hashed password
        status=WorkerStatus.pending, # Set status to pending
        pincode=worker_data.pincode, # Save pincode
        radius=10 # Set default radius
    )

    # --- Debugging Service Categories ---
    print(f"Received category_ids: {worker_data.category_ids}") # Print received IDs

    # Handle service categories if provided
    if worker_data.category_ids:
        categories = db.query(ServiceCategory).filter(ServiceCategory.category_id.in_(worker_data.category_ids)).all()
        print(f"Fetched category objects: {categories}") # Print fetched category objects
        if len(categories) != len(set(worker_data.category_ids)): # Use set to handle potential duplicates
            # Raise error if not all IDs were valid/found
            raise HTTPException(status_code=400, detail="One or more invalid category IDs provided")
        new_worker.service_categories = categories # Assign fetched objects to the relationship
        print(f"Assigned categories to new_worker.service_categories")
    else:
        print("No category_ids received or list is empty.")
    # --- End Debugging ---

    db.add(new_worker)
    print("Attempting to commit new worker with categories...")
    try:
        db.commit()
        print("Commit successful.")
        db.refresh(new_worker)
        # Refresh the relationship explicitly if needed, though commit should handle it
        # db.refresh(new_worker, ['service_categories'])
        print(f"Worker created with ID: {new_worker.worker_id}")
        # Verify categories after commit (optional)
        # db.expire(new_worker) # Expire to force reload from DB
        # reloaded_worker = db.query(Worker).options(joinedload(Worker.service_categories)).filter(Worker.worker_id == new_worker.worker_id).first()
        # print(f"Categories after commit & reload: {[cat.category_id for cat in reloaded_worker.service_categories]}")

    except Exception as e:
        print(f"Error during commit: {e}") # Print commit errors
        db.rollback() # Rollback on error
        raise HTTPException(status_code=500, detail=f"Database error during worker creation: {e}")


    # Changed message to reflect pending status
    return {"message": "Worker registration submitted for approval", "worker_id": new_worker.worker_id}

class WorkerLoginDetails(BaseModel):
    username: str
    password: str

# Keep only one login endpoint - the one that uses OAuth2PasswordRequestForm
@router.post("/login")
async def worker_login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.username == form_data.username).first()

    if not worker or not verify_password(form_data.password, worker.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if worker.status != WorkerStatus.approved:
        raise HTTPException(status_code=403, detail="Worker account not approved yet.")

    # Create worker session
    request.session["worker"] = {
        "id": worker.worker_id,
        "username": worker.username,
        "role": "Worker"  # Capitalized to match frontend expectations
    }

    return {
        "status": "success",
        "role": "Worker",  # Capitalized to match frontend expectations
        "username": worker.username,
        "worker_id": worker.worker_id,
        "id": worker.worker_id  # Include both for consistency
    }

# --- Worker Profile Management ---

class WorkerProfileResponse(BaseModel):
    username: str
    email: str
    mobile: str
    pincode: Optional[str]
    radius: int
    category_ids: List[int] # Include category IDs

    class Config:
        orm_mode = True # Enable ORM mode

class WorkerProfileUpdate(BaseModel):
    email: str
    mobile: str
    pincode: str
    radius: int
    category_ids: List[int] # Accept list of category IDs

# Dependency to get current logged-in worker from session
def get_current_worker_session(request: Request, db: Session = Depends(get_db)):
    worker_session = request.session.get("worker")
    if not worker_session or "id" not in worker_session:
        raise HTTPException(status_code=401, detail="Worker not logged in")
    # Use joinedload to eagerly load categories
    worker = db.query(Worker).options(joinedload(Worker.service_categories)).filter(Worker.worker_id == worker_session["id"]).first()
    if not worker:
        # Clear session if worker not found in DB
        request.session.pop("worker", None)
        raise HTTPException(status_code=401, detail="Worker not found")
    return worker

@router.get("/profile", response_model=WorkerProfileResponse)
def get_worker_profile(current_worker: Worker = Depends(get_current_worker_session)):
    # Extract category IDs from the loaded relationship
    category_ids = [cat.category_id for cat in current_worker.service_categories]
    # Manually construct the response dictionary to include category_ids
    # Pydantic v2 might handle this better automatically with from_attributes=True
    profile_data = {
        "username": current_worker.username,
        "email": current_worker.email,
        "mobile": current_worker.mobile,
        "pincode": current_worker.pincode,
        "radius": current_worker.radius,
        "category_ids": category_ids
    }
    return profile_data

@router.put("/profile", response_model=WorkerProfileResponse)
def update_worker_profile(profile_data: WorkerProfileUpdate, current_worker: Worker = Depends(get_current_worker_session), db: Session = Depends(get_db)):
    # Validate pincode and radius
    if not profile_data.pincode.isdigit() or len(profile_data.pincode) < 5:
        raise HTTPException(status_code=400, detail="Invalid pincode format")
    if profile_data.radius <= 0:
        raise HTTPException(status_code=400, detail="Radius must be positive")

    # Check if email is being changed and if it's already taken by another worker
    if profile_data.email != current_worker.email:
        existing_email_worker = db.query(Worker).filter(Worker.email == profile_data.email, Worker.worker_id != current_worker.worker_id).first()
        if existing_email_worker:
            raise HTTPException(status_code=400, detail="Email already registered by another worker")
        current_worker.email = profile_data.email

    current_worker.mobile = profile_data.mobile
    current_worker.pincode = profile_data.pincode
    current_worker.radius = profile_data.radius

    # Update service categories
    if profile_data.category_ids is not None: # Check if list is provided
        # Fetch the category objects from the database
        categories = db.query(ServiceCategory).filter(ServiceCategory.category_id.in_(profile_data.category_ids)).all()
        # Validate if all provided IDs were found
        if len(categories) != len(set(profile_data.category_ids)): # Use set to handle potential duplicates in input
             raise HTTPException(status_code=400, detail="One or more invalid category IDs provided")
        # Replace the existing categories with the new list
        current_worker.service_categories = categories
    else:
        # If an empty list or None is provided, clear the categories
        current_worker.service_categories = []

    db.commit()
    db.refresh(current_worker)
    # Re-fetch category IDs after refresh for the response
    db.expire(current_worker, ['service_categories']) # Ensure relationship is reloaded
    updated_category_ids = [cat.category_id for cat in current_worker.service_categories]
    response_data = {
        "username": current_worker.username,
        "email": current_worker.email,
        "mobile": current_worker.mobile,
        "pincode": current_worker.pincode,
        "radius": current_worker.radius,
        "category_ids": updated_category_ids
    }
    return response_data

@router.post("/logout")
def worker_logout(request: Request):
    if "worker" not in request.session:
        raise HTTPException(status_code=401, detail="Not logged in")

    del request.session["worker"]

    return {"message": "Worker logged out successfully"}