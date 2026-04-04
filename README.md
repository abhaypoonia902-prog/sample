# ZetaTech Hospital Management System

A Cloud-Based Secure Hospital Service Management System with IoT Integration, built with FastAPI backend and vanilla JavaScript frontend.

## Features

### Privacy-First Architecture
- **Patients** have exclusive access to their medical descriptions and reports
- **Administrators** can only see email addresses and request statuses (never medical data)
- **IoT integration** provides simple room availability without exposing health information
- **Cloud-based deployment** ensures scalability and accessibility

### Role-Based Access Control
- **Patient Portal**: Create service requests, view medical reports, track status
- **Admin Portal**: Process requests (approve/reject with mandatory reasons), view statistics, room assignment
- **Doctor Portal**: Create medical reports, view patient history
- **Nurse Portal**: Patient monitoring, room status tracking

### IoT Room Monitoring
- Real-time room availability tracking
- Simulated IoT devices for demonstration
- API key authentication for device security

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Database (can be migrated to PostgreSQL)
- **JWT**: JSON Web Tokens for authentication
- **bcrypt**: Password hashing

### Frontend
- **HTML5/CSS3**: Modern, responsive design
- **Vanilla JavaScript**: No framework dependencies
- **Font Awesome**: Icons
- **Google Fonts**: Inter font family

## Project Structure

```
zetatech-backend/
├── main.py              # FastAPI application with all endpoints
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic data validation schemas
├── auth.py              # JWT authentication utilities
├── database.py          # Database configuration
├── iot_simulator.py     # IoT device simulator script
├── requirements.txt     # Python dependencies
└── README.md           # This file

zetatech-frontend/
├── index.html          # Role selection page
├── login.html          # Login page
├── patient-dashboard.html
├── admin-dashboard.html
├── doctor-dashboard.html
├── styles.css          # All styles
└── main.js             # Shared JavaScript utilities
```

## Quick Start

### 1. Start the Backend

```bash
cd zetatech-backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### 2. Seed Initial Data

```bash
# In a new terminal
python iot_simulator.py --seed
```

This creates:
- Admin user: `admin@zetatech.com` / `admin123`
- Doctor user: `doctor@zetatech.com` / `doctor123`
- Sample patient: `patient@example.com` / `patient123`
- Sample rooms with IoT API keys

### 3. Start the IoT Simulator (Optional)

```bash
python iot_simulator.py
```

This simulates IoT devices randomly updating room occupancy.

### 4. Open the Frontend

Open `zetatech-frontend/index.html` in your browser, or serve it with a simple HTTP server:

```bash
cd zetatech-frontend
python -m http.server 3000
```

Then visit `http://localhost:3000`

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@zetatech.com | admin123 |
| Doctor | doctor@zetatech.com | doctor123 |
| Patient | patient@example.com | patient123 |

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `GET /me` - Get current user info

### Patient Endpoints
- `POST /patient/requests` - Create service request
- `GET /patient/requests` - Get all own requests (with medical descriptions)
- `GET /patient/reports` - Get all own medical reports

### Admin Endpoints
- `GET /admin/requests` - Get all requests (medical descriptions EXCLUDED)
- `PUT /admin/requests/{id}` - Update request status (with mandatory reason)
- `GET /admin/stats` - Get dashboard statistics
- `GET /admin/patients` - Get all patients
- `POST /admin/rooms` - Create new room

### Doctor Endpoints
- `POST /doctor/reports` - Create medical report
- `GET /doctor/patients/{id}/reports` - Get patient's medical reports

### IoT Endpoints
- `GET /iot/rooms` - Get all room status
- `PUT /iot/rooms/{id}` - Update room status (requires API key)

## Privacy Compliance

This system implements architectural data segregation:

1. **Database Level**: Medical reports exist in a separate table with user identification fields
2. **API Level**: Different Pydantic response models control what data each role receives
3. **Endpoint Level**: Dependencies verify user identity and role before executing queries

### Example Privacy Enforcement

When a patient creates a service request:
- The `description` field containing symptoms is stored in the database
- When the patient views their requests, the API returns the complete record
- When an administrator views the same request, the `description` field is EXCLUDED from the response

## IoT Simulator

The IoT simulator demonstrates room monitoring without physical hardware:

```bash
# Run indefinitely
python iot_simulator.py

# Run for 5 minutes
python iot_simulator.py -d 5

# Quiet mode
python iot_simulator.py -q
```

## Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./zetatech_hms.db
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## Team

**Team Avengers** - BCA (Hons) CS&CL Project

- Prakash Singh (Team Lead)
- Pragyansh Nakoti
- Abhay Poonia

## License

This project is for academic purposes.
