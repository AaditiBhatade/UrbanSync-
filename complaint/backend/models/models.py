import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from backend.models.database import Base

class UserRole(str, Enum):
    CITIZEN = "CITIZEN"
    DEPARTMENT_ADMIN = "DEPARTMENT_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
    FIELD_WORKER = "FIELD_WORKER"

class ComplaintStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    ASSIGNED = "ASSIGNED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    REOPENED = "REOPENED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNCLASSIFIED = "UNCLASSIFIED"

class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    mobile = Column(String(20), nullable=True)
    role = Column(String(50), default=UserRole.CITIZEN.value)
    department_code = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), default="Mumbai")
    pincode = Column(String(20), nullable=True)
    profile_photo = Column(String(255), nullable=True)
    provider = Column(String(50), default="local")
    provider_user_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    complaints = relationship("Complaint", back_populates="citizen", foreign_keys="Complaint.citizen_id")
    notifications = relationship("Notification", back_populates="user")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    complaints = relationship("Complaint", back_populates="department", foreign_keys="Complaint.department_id")
    workers = relationship("Worker", back_populates="department", cascade="all, delete-orphan")

class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    worker_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    department_code = Column(String(50), nullable=False, index=True)
    designation = Column(String(150), nullable=False)
    worker_status = Column(Boolean, default=True, nullable=False)  # True = Free/Available, False = Busy/Assigned
    skills = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    department = relationship("Department", back_populates="workers")
    user = relationship("User", foreign_keys=[user_id])
    complaints = relationship("Complaint", back_populates="assigned_worker")

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(50), unique=True, nullable=False, index=True)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    citizen_selected_category = Column(String(100), nullable=True)
    ai_predicted_category = Column(String(100), nullable=True)
    ai_subcategory = Column(String(100), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    assigned_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)
    priority = Column(String(20), default=PriorityLevel.MEDIUM.value)
    impact_level = Column(String(20), default="MEDIUM")
    status = Column(String(50), default=ComplaintStatus.PENDING.value)
    address = Column(Text, nullable=True)
    area = Column(String(150), nullable=True)
    city = Column(String(100), default="Mumbai")
    state = Column(String(100), default="Maharashtra")
    pincode = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    images = Column(Text, nullable=True)
    resolution_description = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(String(50), nullable=True)
    original_prediction = Column(String(100), nullable=True)
    original_confidence = Column(Float, nullable=True)
    override_category = Column(String(100), nullable=True)
    override_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    override_reason = Column(Text, nullable=True)
    overridden_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    overridden_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # ML Component 2 and Manual Assignment
    cluster_id = Column(Integer, nullable=True)
    assigned_department_head = Column(String(150), nullable=True)

    # Relationships
    citizen = relationship("User", foreign_keys=[citizen_id], back_populates="complaints")
    department = relationship("Department", foreign_keys=[department_id], back_populates="complaints")
    assigned_admin = relationship("User", foreign_keys=[assigned_admin_id])
    assigned_worker = relationship("Worker", foreign_keys=[assigned_worker_id], back_populates="complaints")
    override_department = relationship("Department", foreign_keys=[override_department_id])
    status_history = relationship("ComplaintStatusHistory", back_populates="complaint", cascade="all, delete-orphan")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    actor = relationship("User", foreign_keys=[actor_id])

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    status = Column(String(50), nullable=False)
    old_status = Column(String(50), nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_role = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    complaint = relationship("Complaint", back_populates="status_history")
    actor = relationship("User", foreign_keys=[actor_id])
