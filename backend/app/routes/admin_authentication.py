from fastapi import APIRouter, Depends, HTTPException, Request, status # Added status
from sqlalchemy.orm import Session
from dependencies import get_db
from models import Admin # Import the Admin model
from pydantic import BaseModel
from auth import get_password_hash, verify_password # Import hashing functions
# Import the dependency to get current admin
from routes.admin_management import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])

class AdminLoginDetails(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(admin_auth: AdminLoginDetails, request: Request, db: Session = Depends(get_db)):
    admin_obj = db.query(Admin).filter(Admin.username == admin_auth.username).first()

    if not admin_obj:
        # Use 401 for authentication failure, avoid revealing if user exists
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    # Verify password using hashing function
    if not verify_password(admin_auth.password, admin_obj.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    # Store admin info in session
    request.session["admin"] = {"username": admin_obj.username, "id": admin_obj.admin_id}

    # Return username and id along with message
    return {
        "message": f"Admin {admin_obj.username} Login successful",
        "admin_id": admin_obj.admin_id,
        "username": admin_obj.username
    }


class AdminCreateDetails(BaseModel):
    username: str
    password: str

# WARNING: Secure this endpoint appropriately in production (e.g., run once, command-line flag)
@router.post("/create_initial", status_code=status.HTTP_201_CREATED)
def create_initial_admin(admin_data: AdminCreateDetails, db: Session = Depends(get_db)):
    # Basic check if ANY admin exists. In production, you might want more robust checks.
    if db.query(Admin).count() > 0:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Initial admin already exists.")

    existing_admin = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if existing_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin username already exists")

    hashed_password = get_password_hash(admin_data.password) # Hash the password
    new_admin = Admin(username=admin_data.username, password=hashed_password) # Store hashed password
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"message": "Initial admin created successfully", "admin_id": new_admin.admin_id}

# --- Add endpoint for updating own password ---
class AdminPasswordUpdate(BaseModel):
    password: str

@router.put("/profile", status_code=status.HTTP_200_OK)
def update_admin_self(password_update: AdminPasswordUpdate, current_admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    admin_id = current_admin["id"]
    admin_obj = db.query(Admin).filter(Admin.admin_id == admin_id).first()

    if not admin_obj:
        # Should not happen if get_current_admin works correctly
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current admin not found")

    # Update the password
    admin_obj.password = get_password_hash(password_update.password)
    db.commit()

    return {"message": "Password updated successfully"}

# Add logout endpoint if needed
@router.post("/logout")
def logout(request: Request):
    admin_info = request.session.pop("admin", None)
    if admin_info:
        return {"message": "Admin logout successful"}
    else:
        # Raise error if no admin was in session
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
