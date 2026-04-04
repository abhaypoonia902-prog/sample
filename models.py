from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    PATIENT = "patient"
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"

class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class RoomType(str, enum.Enum):
    CONSULTATION = "consultation"
    THERAPY = "therapy"
    EMERGENCY = "emergency"
    ICU = "icu"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PATIENT, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    service_requests = relationship("ServiceRequest", back_populates="patient", foreign_keys="ServiceRequest.patient_id")
    medical_reports = relationship("MedicalReport", back_populates="patient", foreign_keys="MedicalReport.patient_id")

class ServiceRequest(Base):
    __tablename__ = "service_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_type = Column(String, nullable=False)  # consultation, therapy, follow-up, emergency
    description = Column(Text, nullable=False)  # Medical description - PATIENT ONLY
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    admin_reason = Column(Text, nullable=True)  # Reason for approval/rejection
    assigned_room_id = Column(Integer, ForeignKey("rooms_iot.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("User", back_populates="service_requests", foreign_keys=[patient_id])
    assigned_room = relationship("RoomIoT", back_populates="service_requests")

class MedicalReport(Base):
    __tablename__ = "medical_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_request_id = Column(Integer, ForeignKey("service_requests.id"), nullable=True)
    diagnosis = Column(Text, nullable=False)
    prescription = Column(Text, nullable=False)
    doctor_notes = Column(Text, nullable=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("User", back_populates="medical_reports", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    service_request = relationship("ServiceRequest")

class RoomIoT(Base):
    __tablename__ = "rooms_iot"
    
    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, nullable=False)
    room_type = Column(Enum(RoomType), nullable=False)
    is_occupied = Column(Boolean, default=False)
    current_patient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    api_key = Column(String, nullable=False)  # For IoT device authentication
    
    # Relationships
    service_requests = relationship("ServiceRequest", back_populates="assigned_room")
    current_patient = relationship("User", foreign_keys=[current_patient_id])
