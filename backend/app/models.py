from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from config import Base

class Request(Base):
    __tablename__ = "requests"

    request_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.worker_id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=False)
    user_location_id = Column(Integer, ForeignKey("user_locations.location_id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)

class Worker(Base):
    __tablename__ = "workers"
    worker_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    mobile = Column(String(20), nullable=False)
    employee_number = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

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
    name = Column(String(100), nullable=False)

class Service(Base):
    __tablename__ = "services"

    service_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("service_categories.category_id"), nullable=True)

class WorkerService(Base):
    __tablename__ = "worker_services"

    worker_id = Column(Integer, ForeignKey("workers.worker_id"), primary_key=True)
    service_id = Column(Integer, ForeignKey("services.service_id"), primary_key=True)
    availability = Column(String(50))
