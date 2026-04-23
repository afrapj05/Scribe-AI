"""
Database module with SQLAlchemy ORM for clinical records.
Supports SQLite (local) and PostgreSQL (production).
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey, LargeBinary, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import sys

# Ensure stdout can handle UTF-8 (emoji) on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ===================== DATABASE SETUP =====================
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # 'sqlite' or 'postgresql'
DB_PATH = os.getenv('DATABASE_URL', 'sqlite:///clinical_records.db')

if DB_TYPE == 'sqlite':
    engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DB_PATH)

Session = sessionmaker(bind=engine)
Base = declarative_base()

# ===================== DATA MODELS =====================

class Patient(Base):
    """Patient demographic and medical history."""
    __tablename__ = "patients"
    
    patient_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    age = Column(Integer)
    gender = Column(String(20))
    phone = Column(String(20), unique=True)
    email = Column(String(255), unique=True)
    blood_group = Column(String(10))
    height = Column(Float)  # in cm
    weight = Column(Float)  # in kg
    
    # Medical history
    chronic_conditions = Column(JSON)  # List of chronic diseases
    allergies = Column(JSON)  # List of allergies
    medications = Column(JSON)  # Current medications
    surgical_history = Column(JSON)  # Previous surgeries
    family_history = Column(JSON)  # Family medical history
    
    # Compliance
    abdm_id = Column(String(100), unique=True)  # ABDM Health ID
    aadhar = Column(String(20), unique=True)  # Aadhar (India specific)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    visit_count = Column(Integer, default=0)
    last_visit = Column(DateTime)
    
    # Relationships
    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "phone": self.phone,
            "email": self.email,
            "blood_group": self.blood_group,
            "height": self.height,
            "weight": self.weight,
            "chronic_conditions": self.chronic_conditions,
            "allergies": self.allergies,
            "abdm_id": self.abdm_id,
            "visit_count": self.visit_count,
            "last_visit": self.last_visit.isoformat() if self.last_visit else None,
            "created_at": self.created_at.isoformat()
        }


class AudioRecording(Base):
    """Audio recording metadata and file reference."""
    __tablename__ = "audio_recordings"
    
    audio_id = Column(String(50), primary_key=True)
    visit_id = Column(String(50), ForeignKey("visits.visit_id"), nullable=False)
    
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    duration = Column(Float)  # in seconds
    sample_rate = Column(Integer)  # 44100, 48000, etc.
    channels = Column(Integer)  # 1 (mono) or 2 (stereo)
    
    # Audio processing
    noise_level = Column(Float)  # Estimated noise level (0-1)
    has_noise_filter = Column(Boolean, default=False)
    filter_type = Column(String(50))  # 'lowpass', 'highpass', 'bandpass', 'spectral_subtraction'
    
    # Transcript
    raw_transcript = Column(Text)
    language = Column(String(10), default='en')
    transcription_confidence = Column(Float)  # 0-1
    
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    visit = relationship("Visit", back_populates="audio_recording")
    
    def to_dict(self):
        return {
            "audio_id": self.audio_id,
            "visit_id": self.visit_id,
            "file_path": self.file_path,
            "duration": self.duration,
            "language": self.language,
            "created_at": self.created_at.isoformat()
        }


class Visit(Base):
    """Clinical visit/encounter record."""
    __tablename__ = "visits"
    
    visit_id = Column(String(50), primary_key=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False)
    clinician_id = Column(String(50), nullable=False, index=True)
    clinician_name = Column(String(255))
    
    # Vital signs
    temperature = Column(Float)  # in Celsius
    blood_pressure_systolic = Column(Integer)
    blood_pressure_diastolic = Column(Integer)
    heart_rate = Column(Integer)  # bpm
    respiratory_rate = Column(Integer)
    oxygen_saturation = Column(Float)  # %
    
    # Chief complaint
    chief_complaint = Column(String(500))
    
    # Timestamps
    visit_date = Column(DateTime, default=datetime.now, index=True)
    duration = Column(Float)  # in seconds
    
    # Metadata
    visit_type = Column(String(50))  # 'OP' (outpatient), 'IP' (inpatient), 'Emergency'
    department = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    patient = relationship("Patient", back_populates="visits")
    audio_recording = relationship("AudioRecording", back_populates="visit", uselist=False, cascade="all, delete-orphan")
    soap_note = relationship("SoapNote", back_populates="visit", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "visit_id": self.visit_id,
            "patient_id": self.patient_id,
            "chief_complaint": self.chief_complaint,
            "visit_date": self.visit_date.isoformat(),
            "duration": self.duration,
            "visit_type": self.visit_type,
            "department": self.department,
            "created_at": self.created_at.isoformat()
        }


class SoapNote(Base):
    """SOAP note structure with ABDM compliance."""
    __tablename__ = "soap_notes"
    
    note_id = Column(String(50), primary_key=True)
    visit_id = Column(String(50), ForeignKey("visits.visit_id"), nullable=False, unique=True)
    
    # SOAP components
    subjective = Column(Text)
    objective = Column(Text)
    assessment = Column(Text)
    plan = Column(Text)
    
    # Clinical coding
    icd10_codes = Column(JSON)  # List of ICD-10 codes with confidence
    medications_prescribed = Column(JSON)  # List of medications

    # Multilingual — always store English canonical + clinician's chosen language copy
    language = Column(String(10), default='en')         # clinician's chosen language code
    subjective_localized = Column(Text)                 # subjective in clinician's language
    objective_localized = Column(Text)                  # objective in clinician's language
    assessment_localized = Column(Text)                 # assessment in clinician's language
    plan_localized = Column(Text)                       # plan in clinician's language

    # Compliance indicators
    abdm_compliant = Column(Boolean, default=False)
    data_privacy_level = Column(String(50))  # 'HIPAA', 'GDPR', 'India DPDP'
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    visit = relationship("Visit", back_populates="soap_note")
    
    def to_dict(self):
        return {
            "note_id": self.note_id,
            "visit_id": self.visit_id,
            "subjective": self.subjective,
            "objective": self.objective,
            "assessment": self.assessment,
            "plan": self.plan,
            "icd10_codes": self.icd10_codes,
            "language": self.language or 'en',
            "subjective_localized": self.subjective_localized,
            "assessment_localized": self.assessment_localized,
            "plan_localized": self.plan_localized,
            "abdm_compliant": self.abdm_compliant,
            "created_at": self.created_at.isoformat()
        }



class Medicine(Base):
    """Medicine/Drug database for prescriptions and interactions."""
    __tablename__ = "medicines"
    
    medicine_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    manufacturer = Column(String(255))
    price = Column(Float)  # in INR
    dosage_form = Column(String(100))  # Tablet, Capsule, Injection, Syrup
    composition = Column(Text)  # Active ingredients
    pack_size = Column(String(100))  # Strip of 10 tablets, etc.
    discontinued = Column(Boolean, default=False)
    category = Column(String(100), index=True)  # Antibiotic, etc.
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            "medicine_id": self.medicine_id,
            "name": self.name,
            "manufacturer": self.manufacturer,
            "price": self.price,
            "dosage_form": self.dosage_form,
            "composition": self.composition
        }


class Prescription(Base):
    """Medicine prescription with dosage and frequency."""
    __tablename__ = "prescriptions"
    
    prescription_id = Column(String(50), primary_key=True)
    visit_id = Column(String(50), nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False)
    
    # Medicine details
    medicine_name = Column(String(255), nullable=False)
    medicine_code = Column(String(50))  # NDC or other national codes
    dosage = Column(String(100))  # e.g., "500mg"
    frequency = Column(String(100))  # e.g., "TDS" (3x daily)
    duration = Column(String(100))  # e.g., "7 days"
    route = Column(String(50))  # 'oral', 'injection', 'topical', etc.
    
    # Additional info
    indication = Column(String(500))
    contraindications = Column(JSON)
    side_effects = Column(JSON)
    interactions = Column(JSON)
    
    # Metadata
    date_prescribed = Column(DateTime, default=datetime.now)
    date_expires = Column(DateTime)
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    
    def to_dict(self):
        return {
            "prescription_id": self.prescription_id,
            "patient_id": self.patient_id,
            "medicine_name": self.medicine_name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "duration": self.duration,
            "date_prescribed": self.date_prescribed.isoformat()
        }


class User(Base):
    """Clinician/Staff user accounts."""
    __tablename__ = "users"
    
    username = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'doctor', 'nurse', 'admin'
    department = Column(String(100))
    email = Column(String(255), unique=True)
    password_hash = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    
    def to_dict(self):
        return {
            "username": self.username,
            "name": self.name,
            "role": self.role,
            "department": self.department,
            "email": self.email
        }


# ===================== DATABASE INITIALIZATION =====================
def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(engine)
    print(f"[OK] Database initialized: {DB_PATH}")


def get_session():
    """Get a new database session."""
    return Session()


def close_session(session):
    """Close a database session."""
    if session:
        session.close()
