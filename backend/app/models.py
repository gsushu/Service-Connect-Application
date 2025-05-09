from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Enum, Float, Boolean, Table # Added Float, Boolean, Table
from sqlalchemy.orm import relationship, Session # Added Session
from sqlalchemy.sql import func, text
from config import Base
import enum
from typing import Optional, List # Import Optional, List

# Enum for Worker Status
class WorkerStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

# Enum for Request Status (updated to clarify workflow)
class RequestStatus(enum.Enum):
    pending = "pending"      # Initial state - open for worker quotes
    accepted = "accepted"    # User accepted a worker's quote, worker assigned
    inprogress = "inprogress"  # Worker has started the work
    completed = "completed"  # Worker marked the job as completed
    cancelled = "cancelled"  # Either user or assigned worker cancelled the request

# Association Table for Worker <-> ServiceCategory
worker_service_categories_table = Table('worker_service_categories', Base.metadata,
    Column('worker_id', Integer, ForeignKey('workers.worker_id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('service_categories.category_id'), primary_key=True)
)

class sRequest(Base):
    __tablename__ = "requests"

    request_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    # worker_id is now only set AFTER a quote is accepted
    worker_id = Column(Integer, ForeignKey("workers.worker_id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=False)
    user_location_id = Column(Integer, ForeignKey("user_locations.location_id"), nullable=False)
    # Status remains pending during bidding, changes to accepted upon user choice
    status = Column(Enum(RequestStatus), default=RequestStatus.pending, nullable=False) # Use Enum
    description = Column(Text, nullable=True)
    urgency_level = Column(String(50), nullable=True)
    additional_notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) # Made non-nullable, added server_default

    # --- User's initial price indication (Optional) ---
    user_quoted_price = Column(Float, nullable=True) # User's initial budget/offer

    # --- Fields moved to RequestQuote or implicit ---
    # worker_quoted_price = Column(Float, nullable=True) # MOVED to RequestQuote
    # worker_comments = Column(Text, nullable=True) # MOVED to RequestQuote
    # user_price_agreed = Column(Boolean, default=False, nullable=False) # REMOVED (implicit on accept)
    # worker_price_agreed = Column(Boolean, default=False, nullable=False) # REMOVED (implicit on accept)

    # --- Final agreed price (from accepted quote) ---
    final_price = Column(Float, nullable=True)

    # Relationships
    user = relationship("User") # Add relationship to User
    user_location = relationship("UserLocation")
    service = relationship("Service") # Add relationship to Service
    worker = relationship("Worker") # Relationship to the assigned worker (once accepted)
    # Relationship to get all quotes for this request
    quotes = relationship("RequestQuote", back_populates="request", cascade="all, delete-orphan")

# New table to store quotes from multiple workers for one request
class RequestQuote(Base):
    __tablename__ = "request_quotes"

    quote_id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.request_id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.worker_id"), nullable=False)
    worker_quoted_price = Column(Float, nullable=False)
    worker_comments = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    request = relationship("sRequest", back_populates="quotes")
    worker = relationship("Worker", back_populates="quotes")


class Worker(Base):
    __tablename__ = "workers"

    worker_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True) # Added unique constraint
    email = Column(String(255), unique=True, nullable=False)
    mobile = Column(String(20), nullable=False)
    employee_number = Column(String(50), nullable=False, unique=True) # Added unique constraint
    password = Column(String(255), nullable=False)
    status = Column(Enum(WorkerStatus), default=WorkerStatus.pending, nullable=False) # Added status field
    pincode = Column(String(20), nullable=True) # Added pincode
    radius = Column(Integer, default=10, nullable=False) # Added radius with default
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Many-to-Many relationship with ServiceCategory
    service_categories = relationship(
        "ServiceCategory",
        secondary=worker_service_categories_table,
        back_populates="workers"
    )
    # Relationship to all quotes submitted by this worker
    quotes = relationship("RequestQuote", back_populates="worker")

class UserLocation(Base):
    __tablename__ = "user_locations"

    location_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    address = Column(Text, nullable=False)
    pincode = Column(String(20), nullable=True)

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    mobile = Column(String(20), nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to requests created by this user
    requests = relationship("sRequest", back_populates="user")
    # Relationship to locations owned by this user
    locations = relationship("UserLocation") # Add backref if needed

class ServiceCategory(Base):
    __tablename__ = "service_categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True) # Added unique constraint

    # Relationship back to Worker
    workers = relationship(
        "Worker",
        secondary=worker_service_categories_table,
        back_populates="service_categories"
    )
    # Relationship to Services within this category
    services = relationship("Service", back_populates="category")

class Service(Base):
    __tablename__ = "services"

    service_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("service_categories.category_id"), nullable=True)

    # Relationship back to ServiceCategory
    category = relationship("ServiceCategory", back_populates="services")

# Remove the old WorkerService class/table
# class WorkerService(Base):
#    __tablename__ = "worker_services"
#    ...

# New Admin Model
class Admin(Base):
    __tablename__ = "admins"

    admin_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False) # Consider hashing passwords in production
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

# Function to migrate existing "negotiating" status records to "pending"
def migrate_negotiating_to_pending(db: Session):
    """
    This function should be called during application startup to migrate
    any requests with 'negotiating' status to 'pending' status.

    Args:
        db: SQLAlchemy database session
    """
    try:
        # Using raw SQL for this operation to handle the enum constraints
        result = db.execute(text("""
            UPDATE requests
            SET status = 'pending'
            WHERE status = 'negotiating'
        """))
        db.commit()
        updated_count = result.rowcount
        print(f"Migration: {updated_count} records updated from 'negotiating' to 'pending'")
        return updated_count
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        return 0
