from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import UserRole, RequestStatus, RoomType

# ============== USER SCHEMAS ==============

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.PATIENT

class UserResponse(UserBase):
    id: int
    role: UserRole
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ============== SERVICE REQUEST SCHEMAS ==============

class ServiceRequestCreate(BaseModel):
    service_type: str
    description: str  # Medical symptoms/description

# Patient view - includes full medical description
class ServiceRequestPatientView(BaseModel):
    id: int
    service_type: str
    description: str  # Full medical description visible to patient
    status: RequestStatus
    admin_reason: Optional[str]
    assigned_room_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Admin view - EXCLUDES medical description for privacy
class ServiceRequestAdminView(BaseModel):
    id: int
    patient_email: str  # Only email visible to admin
    service_type: str
    status: RequestStatus
    admin_reason: Optional[str]
    assigned_room_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    # NOTE: description field is INTENTIONALLY EXCLUDED for privacy compliance
    
    class Config:
        from_attributes = True

class ServiceRequestUpdate(BaseModel):
    status: RequestStatus
    admin_reason: str  # Mandatory reason for approval/rejection
    assigned_room_id: Optional[int] = None

# ============== MEDICAL REPORT SCHEMAS ==============

class MedicalReportCreate(BaseModel):
    patient_id: int
    service_request_id: Optional[int] = None
    diagnosis: str
    prescription: str
    doctor_notes: Optional[str] = None

class MedicalReportResponse(BaseModel):
    id: int
    patient_id: int
    service_request_id: Optional[int]
    diagnosis: str
    prescription: str
    doctor_notes: Optional[str]
    doctor_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============== ROOM IOT SCHEMAS ==============

class RoomIoTCreate(BaseModel):
    room_number: str
    room_type: RoomType
    api_key: str

class RoomIoTUpdate(BaseModel):
    is_occupied: bool
    current_patient_id: Optional[int] = None

class RoomIoTResponse(BaseModel):
    id: int
    room_number: str
    room_type: RoomType
    is_occupied: bool
    current_patient_id: Optional[int]
    last_updated: datetime
    
    class Config:
        from_attributes = True

# ============== STATISTICS SCHEMAS ==============

class DashboardStats(BaseModel):
    total_requests: int
    pending_requests: int
    approved_requests: int
    completed_requests: int
    rejected_requests: int
    total_patients: int
    available_rooms: int
    occupied_rooms: int

# ============== AUTH SCHEMAS ==============

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
