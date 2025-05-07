from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from config import engine, Base
# Import necessary routers
from routes import hello, user_request, user_authentication, user_view_requests, user_view_services
from routes import worker_authentication, worker_view_all_open_requests, worker_view_my_requests, worker_complete_cancel_request, worker_quote_agree
from routes import worker_notifications, admin_authentication, admin_management
from routes import user_profile_management
# Import the new user notifications router
from routes import user_notifications
import models
import os
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Create database tables (Keep commented out unless resetting)
# models.Base.metadata.drop_all(bind=engine)
# models.Base.metadata.create_all(bind=engine)

# --- Main FastAPI Application ---
app = FastAPI(title="Service Connect Main API")

# Get session secret key from environment variable
SESSION_SECRET = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET:
    raise ValueError("SESSION_SECRET_KEY environment variable not set")

# Add Session Middleware using the loaded secret key
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Allows Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include ALL routers for the main application ---
app.include_router(hello.router)
app.include_router(user_request.router) # Includes user quote/agree endpoints now
app.include_router(user_authentication.router)
app.include_router(user_view_requests.router)
app.include_router(user_view_services.router)
app.include_router(user_profile_management.router) # Group user routes
app.include_router(user_notifications.router) # Add user notifications router

app.include_router(worker_authentication.router)
app.include_router(worker_view_all_open_requests.router)
app.include_router(worker_quote_agree.router) # Add the new router
app.include_router(worker_view_my_requests.router)
app.include_router(worker_complete_cancel_request.router)
app.include_router(worker_notifications.router) # Group worker routes

app.include_router(admin_authentication.router)
app.include_router(admin_management.router) # Add the admin management router

# --- Root Endpoint for Main App ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Service Connect API"}

# Example of accessing session (for debugging or other purposes)
@app.get("/session-info")
async def get_session_info(request: Request):
    return request.session