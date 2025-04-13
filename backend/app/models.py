from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Enum, Float, Boolean, Table # Added Float, Boolean, Table
from sqlalchemy.orm import relationship # Import relationship
from sqlalchemy.sql import func, text
from config import Base
import enum
from typing import Optional, List # Import Optional, List

# Enum for Worker Status
class WorkerStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

# Enum for Request Status (optional, but good practice)
class RequestStatus(enum.Enum):
    pending = "pending"
    negotiating = "negotiating" # New status for price negotiation
    accepted = "accepted" # Price agreed, ready for work
    inprogress = "inprogress" # Optional: If worker explicitly starts work
    completed = "completed"
    cancelled = "cancelled"

# Association Table for Worker <-> ServiceCategory
worker_service_categories_table = Table('worker_service_categories', Base.metadata,
    Column('worker_id', Integer, ForeignKey('workers.worker_id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('service_categories.category_id'), primary_key=True)
)

class sRequest(Base):
    __tablename__ = "requests"

    request_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.worker_id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=False)
    user_location_id = Column(Integer, ForeignKey("user_locations.location_id"), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.pending, nullable=False) # Use Enum
    description = Column(Text, nullable=True)
    urgency_level = Column(String(50), nullable=True)
    additional_notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) # Made non-nullable, added server_default

    # --- New Pricing and Negotiation Fields ---
    user_quoted_price = Column(Float, nullable=True)
    worker_quoted_price = Column(Float, nullable=True)
    final_price = Column(Float, nullable=True)
    user_price_agreed = Column(Boolean, default=False, nullable=False)
    worker_price_agreed = Column(Boolean, default=False, nullable=False)
    worker_comments = Column(Text, nullable=True) # Comments from worker during negotiation/rejection

    # Relationship to easily get location details
    user_location = relationship("UserLocation")
    service = relationship("Service") # Add relationship to Service

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
