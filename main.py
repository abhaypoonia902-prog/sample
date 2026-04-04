from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import models
import schemas
from database import engine, get_db
from auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_active_user, require_patient, require_admin, 
    require_doctor, require_staff
)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ZetaTech Hospital Management System",
    description="Cloud-Based Secure Hospital Service Management with IoT Integration",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== AUTHENTICATION ENDPOINTS ==============

@app.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user (patient by default)."""
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        phone=user.phone,
        address=user.address
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@app.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token."""
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

# ============== PATIENT ENDPOINTS ==============

@app.post("/patient/requests", response_model=schemas.ServiceRequestPatientView)
def create_service_request(
    request: schemas.ServiceRequestCreate,
    current_user: models.User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """Patient: Create a new service request with medical description."""
    db_request = models.ServiceRequest(
        patient_id=current_user.id,
        service_type=request.service_type,
        description=request.description,
        status=models.RequestStatus.PENDING
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.get("/patient/requests", response_model=List[schemas.ServiceRequestPatientView])
def get_patient_requests(
    current_user: models.User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """Patient: Get all own service requests with FULL medical descriptions."""
    requests = db.query(models.ServiceRequest).filter(
        models.ServiceRequest.patient_id == current_user.id
    ).order_by(models.ServiceRequest.created_at.desc()).all()
    return requests

@app.get("/patient/reports", response_model=List[schemas.MedicalReportResponse])
def get_patient_reports(
    current_user: models.User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """Patient: Get all own medical reports (EXCLUSIVE ACCESS)."""
    reports = db.query(models.MedicalReport).filter(
        models.MedicalReport.patient_id == current_user.id
    ).order_by(models.MedicalReport.created_at.desc()).all()
    return reports

# ============== ADMIN ENDPOINTS (PRIVACY-CONTROLLED) ==============

@app.get("/admin/requests", response_model=List[schemas.ServiceRequestAdminView])
def get_all_requests_admin(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get all service requests - MEDICAL DESCRIPTIONS EXCLUDED for privacy."""
    requests = db.query(models.ServiceRequest).order_by(models.ServiceRequest.created_at.desc()).all()
    
    # Transform to admin view (description excluded)
    admin_views = []
    for req in requests:
        patient = db.query(models.User).filter(models.User.id == req.patient_id).first()
        admin_view = schemas.ServiceRequestAdminView(
            id=req.id,
            patient_email=patient.email if patient else "Unknown",
            service_type=req.service_type,
            status=req.status,
            admin_reason=req.admin_reason,
            assigned_room_id=req.assigned_room_id,
            created_at=req.created_at,
            updated_at=req.updated_at
        )
        admin_views.append(admin_view)
    
    return admin_views

@app.put("/admin/requests/{request_id}", response_model=schemas.ServiceRequestAdminView)
def update_request_status(
    request_id: int,
    update: schemas.ServiceRequestUpdate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Approve/reject request with mandatory reason."""
    db_request = db.query(models.ServiceRequest).filter(models.ServiceRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Require reason for approval/rejection
    if update.status in [models.RequestStatus.APPROVED, models.RequestStatus.REJECTED]:
        if not update.admin_reason or update.admin_reason.strip() == "":
            raise HTTPException(
                status_code=400, 
                detail="Reason is mandatory for approval/rejection"
            )
    
    db_request.status = update.status
    db_request.admin_reason = update.admin_reason
    if update.assigned_room_id:
        db_request.assigned_room_id = update.assigned_room_id
    db_request.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_request)
    
    # Return admin view
    patient = db.query(models.User).filter(models.User.id == db_request.patient_id).first()
    return schemas.ServiceRequestAdminView(
        id=db_request.id,
        patient_email=patient.email if patient else "Unknown",
        service_type=db_request.service_type,
        status=db_request.status,
        admin_reason=db_request.admin_reason,
        assigned_room_id=db_request.assigned_room_id,
        created_at=db_request.created_at,
        updated_at=db_request.updated_at
    )

@app.get("/admin/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get dashboard statistics."""
    total_requests = db.query(models.ServiceRequest).count()
    pending_requests = db.query(models.ServiceRequest).filter(
        models.ServiceRequest.status == models.RequestStatus.PENDING
    ).count()
    approved_requests = db.query(models.ServiceRequest).filter(
        models.ServiceRequest.status == models.RequestStatus.APPROVED
    ).count()
    completed_requests = db.query(models.ServiceRequest).filter(
        models.ServiceRequest.status == models.RequestStatus.COMPLETED
    ).count()
    rejected_requests = db.query(models.ServiceRequest).filter(
        models.ServiceRequest.status == models.RequestStatus.REJECTED
    ).count()
    total_patients = db.query(models.User).filter(models.User.role == models.UserRole.PATIENT).count()
    available_rooms = db.query(models.RoomIoT).filter(models.RoomIoT.is_occupied == False).count()
    occupied_rooms = db.query(models.RoomIoT).filter(models.RoomIoT.is_occupied == True).count()
    
    return schemas.DashboardStats(
        total_requests=total_requests,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        completed_requests=completed_requests,
        rejected_requests=rejected_requests,
        total_patients=total_patients,
        available_rooms=available_rooms,
        occupied_rooms=occupied_rooms
    )

@app.get("/admin/patients", response_model=List[schemas.UserResponse])
def get_all_patients(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get all patients (email and basic info only)."""
    patients = db.query(models.User).filter(models.User.role == models.UserRole.PATIENT).all()
    return patients

# ============== DOCTOR ENDPOINTS ==============

@app.post("/doctor/reports", response_model=schemas.MedicalReportResponse)
def create_medical_report(
    report: schemas.MedicalReportCreate,
    current_user: models.User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """Doctor: Create medical report for a patient."""
    # Verify patient exists
    patient = db.query(models.User).filter(models.User.id == report.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db_report = models.MedicalReport(
        patient_id=report.patient_id,
        service_request_id=report.service_request_id,
        diagnosis=report.diagnosis,
        prescription=report.prescription,
        doctor_notes=report.doctor_notes,
        doctor_id=current_user.id
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

@app.get("/doctor/patients/{patient_id}/reports", response_model=List[schemas.MedicalReportResponse])
def get_patient_reports_doctor(
    patient_id: int,
    current_user: models.User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """Doctor: Get medical reports for a specific patient."""
    reports = db.query(models.MedicalReport).filter(
        models.MedicalReport.patient_id == patient_id
    ).order_by(models.MedicalReport.created_at.desc()).all()
    return reports

# ============== IOT ENDPOINTS ==============

@app.get("/iot/rooms", response_model=List[schemas.RoomIoTResponse])
def get_all_rooms(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all room availability status (all authenticated users)."""
    rooms = db.query(models.RoomIoT).all()
    return rooms

@app.put("/iot/rooms/{room_id}")
def update_room_status(
    room_id: int,
    update: schemas.RoomIoTUpdate,
    api_key: str = Header(..., description="IoT Device API Key"),
    db: Session = Depends(get_db)
):
    """IoT Device: Update room occupancy status (requires API key)."""
    room = db.query(models.RoomIoT).filter(models.RoomIoT.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Verify API key
    if room.api_key != api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    room.is_occupied = update.is_occupied
    room.current_patient_id = update.current_patient_id
    room.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(room)
    
    return {"message": "Room status updated", "room": room}

@app.post("/admin/rooms", response_model=schemas.RoomIoTResponse)
def create_room(
    room: schemas.RoomIoTCreate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Create a new IoT room."""
    db_room = models.RoomIoT(
        room_number=room.room_number,
        room_type=room.room_type,
        api_key=room.api_key,
        is_occupied=False
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

# ============== SEED DATA ENDPOINT ==============

@app.post("/seed")
def seed_data(db: Session = Depends(get_db)):
    """Seed initial data for testing (admin user and rooms)."""
    # Create admin user if not exists
    admin = db.query(models.User).filter(models.User.email == "admin@zetatech.com").first()
    if not admin:
        admin = models.User(
            email="admin@zetatech.com",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role=models.UserRole.ADMIN
        )
        db.add(admin)
    
    # Create doctor user if not exists
    doctor = db.query(models.User).filter(models.User.email == "doctor@zetatech.com").first()
    if not doctor:
        doctor = models.User(
            email="doctor@zetatech.com",
            hashed_password=get_password_hash("doctor123"),
            full_name="Dr. Sarah Johnson",
            role=models.UserRole.DOCTOR
        )
        db.add(doctor)
    
    # Create sample patient
    patient = db.query(models.User).filter(models.User.email == "patient@example.com").first()
    if not patient:
        patient = models.User(
            email="patient@example.com",
            hashed_password=get_password_hash("patient123"),
            full_name="John Doe",
            role=models.UserRole.PATIENT,
            phone="+91 98765 43210"
        )
        db.add(patient)
    
    # Create sample rooms
    rooms = [
        ("101", models.RoomType.CONSULTATION, "iot_key_101"),
        ("102", models.RoomType.CONSULTATION, "iot_key_102"),
        ("201", models.RoomType.THERAPY, "iot_key_201"),
        ("202", models.RoomType.THERAPY, "iot_key_202"),
        ("301", models.RoomType.EMERGENCY, "iot_key_301"),
        ("ICU-1", models.RoomType.ICU, "iot_key_icu1"),
    ]
    
    for room_num, room_type, api_key in rooms:
        existing = db.query(models.RoomIoT).filter(models.RoomIoT.room_number == room_num).first()
        if not existing:
            room = models.RoomIoT(
                room_number=room_num,
                room_type=room_type,
                api_key=api_key,
                is_occupied=False
            )
            db.add(room)
    
    db.commit()
    return {"message": "Seed data created successfully"}

# ============== HEALTH CHECK ==============

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ZetaTech HMS API"}

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
