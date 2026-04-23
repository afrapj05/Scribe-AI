"""
Database Manager - Easy access and editing of clinical data.
Provides functions to manage patients, visits, medicines, and SOAP notes from the SQL database.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import Session, Patient, Visit, SoapNote, AudioRecording, Prescription, init_db
from scriber_enhanced import ScribeAI


class DatabaseManager:
    """Manage database operations for the Streamlit UI."""
    
    def __init__(self):
        self.scribe = ScribeAI()
        self.session = Session()
    
    # ===================== PATIENT OPERATIONS =====================
    
    def get_all_patients_df(self) -> pd.DataFrame:
        """Get all patients as DataFrame."""
        try:
            patients = self.session.query(Patient).all()
            if not patients:
                return pd.DataFrame()
            
            data = []
            for p in patients:
                data.append({
                    "Patient ID": p.patient_id,
                    "Name": p.name,
                    "Age": p.age,
                    "Gender": p.gender,
                    "Blood Group": p.blood_group,
                    "Phone": p.phone,
                    "Email": p.email,
                    "Chronic Conditions": ", ".join(p.chronic_conditions or []),
                    "Allergies": ", ".join(p.allergies or []),
                    "Visits": p.visit_count,
                    "Last Visit": p.last_visit.strftime("%Y-%m-%d") if p.last_visit else "N/A"
                })
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading patients: {e}")
            return pd.DataFrame()
    
    def create_patient(self, name: str, age: int, gender: str, phone: str, email: str,
                      blood_group: str, chronic_conditions: list = None, **kwargs) -> tuple:
        """Create a new patient in database."""
        try:
            success, patient_id = self.scribe.create_patient(
                name=name,
                age=age,
                gender=gender,
                phone=phone,
                email=email,
                blood_group=blood_group,
                chronic_conditions=chronic_conditions or [],
                **kwargs
            )
            return success, patient_id
        except Exception as e:
            st.error(f"Error creating patient: {e}")
            return False, None
    
    def get_patient_by_id(self, patient_id: str) -> dict:
        """Get patient details by ID."""
        try:
            patient = self.session.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not patient:
                return None
            
            return {
                "patient_id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "phone": patient.phone,
                "email": patient.email,
                "blood_group": patient.blood_group,
                "height": patient.height,
                "weight": patient.weight,
                "chronic_conditions": patient.chronic_conditions or [],
                "allergies": patient.allergies or [],
                "medications": patient.medications or [],
                "visit_count": patient.visit_count,
                "last_visit": patient.last_visit
            }
        except Exception as e:
            st.error(f"Error loading patient: {e}")
            return None
    
    # ===================== VISIT OPERATIONS =====================
    
    def create_visit(self, patient_id: str, chief_complaint: str, temperature: float = None,
                    bp_systolic: int = None, bp_diastolic: int = None, 
                    heart_rate: int = None, **kwargs) -> tuple:
        """Create a visit for a patient."""
        try:
            success, visit_id = self.scribe.create_visit(
                patient_id=patient_id,
                clinician_id="DOC-default",  # Should come from logged-in user
                chief_complaint=chief_complaint,
                temperature=temperature,
                bp_systolic=bp_systolic,
                bp_diastolic=bp_diastolic,
                heart_rate=heart_rate,
                **kwargs
            )
            return success, visit_id
        except Exception as e:
            st.error(f"Error creating visit: {e}")
            return False, None
    
    def get_patient_visits_df(self, patient_id: str) -> pd.DataFrame:
        """Get all visits for a patient as DataFrame."""
        try:
            visits = self.session.query(Visit).filter(Visit.patient_id == patient_id).all()
            if not visits:
                return pd.DataFrame()
            
            data = []
            for v in visits:
                data.append({
                    "Visit ID": v.visit_id,
                    "Date": v.visit_date.strftime("%Y-%m-%d %H:%M") if v.visit_date else "N/A",
                    "Chief Complaint": v.chief_complaint,
                    "Temperature": f"{v.temperature}°C" if v.temperature else "N/A",
                    "BP": f"{v.blood_pressure_systolic}/{v.blood_pressure_diastolic}" if v.blood_pressure_systolic else "N/A",
                    "HR": f"{v.heart_rate} bpm" if v.heart_rate else "N/A",
                    "O2 Sat": f"{v.oxygen_saturation}%" if v.oxygen_saturation else "N/A",
                    "Type": v.visit_type or "OP"
                })
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading visits: {e}")
            return pd.DataFrame()
    
    # ===================== SOAP NOTE OPERATIONS =====================
    
    def save_soap_from_visit(self, visit_id: str, soap_data: dict) -> tuple:
        """Save SOAP note for a visit."""
        try:
            success, note_id = self.scribe.save_soap_note(visit_id, soap_data)
            return success, note_id
        except Exception as e:
            st.error(f"Error saving SOAP note: {e}")
            return False, None
    
    def get_visit_soap_df(self, patient_id: str) -> pd.DataFrame:
        """Get all SOAP notes for a patient's visits as DataFrame."""
        try:
            # Get all visits for the patient
            visits = self.session.query(Visit).filter(Visit.patient_id == patient_id).all()
            visit_ids = [v.visit_id for v in visits]
            
            # Get SOAP notes for those visits
            soap_notes = self.session.query(SoapNote).filter(SoapNote.visit_id.in_(visit_ids)).all()
            
            if not soap_notes:
                return pd.DataFrame()
            
            data = []
            for note in soap_notes:
                data.append({
                    "Note ID": note.note_id,
                    "Visit ID": note.visit_id,
                    "Created": note.created_at.strftime("%Y-%m-%d %H:%M") if note.created_at else "N/A",
                    "Assessment": note.assessment[:100] + "..." if len(note.assessment or "") > 100 else note.assessment,
                    "ICD-10 Codes": ", ".join(note.icd10_codes or [])
                })
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading SOAP notes: {e}")
            return pd.DataFrame()
    
    # ===================== AUDIO RECORDING OPERATIONS =====================
    
    def get_audio_recordings_df(self, patient_id: str = None) -> pd.DataFrame:
        """Get audio recordings as DataFrame."""
        try:
            query = self.session.query(AudioRecording)
            
            if patient_id:
                # Filter by patient's visits
                visits = self.session.query(Visit).filter(Visit.patient_id == patient_id).all()
                visit_ids = [v.visit_id for v in visits]
                query = query.filter(AudioRecording.visit_id.in_(visit_ids))
            
            recordings = query.all()
            if not recordings:
                return pd.DataFrame()
            
            data = []
            for rec in recordings:
                data.append({
                    "Audio ID": rec.audio_id,
                    "Visit ID": rec.visit_id,
                    "Duration": f"{rec.duration:.1f}s" if rec.duration else "N/A",
                    "Language": rec.language or "en",
                    "Noise Level": f"{rec.noise_level:.2f}" if rec.noise_level else "N/A",
                    "Filter": rec.filter_type or "None",
                    "Confidence": f"{rec.transcription_confidence:.2f}" if rec.transcription_confidence else "N/A",
                    "Created": rec.created_at.strftime("%Y-%m-%d %H:%M") if rec.created_at else "N/A"
                })
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading audio recordings: {e}")
            return pd.DataFrame()
    
    # ===================== PRESCRIPTION OPERATIONS =====================
    
    def add_prescription(self, patient_id: str, visit_id: str, medicine_name: str,
                        dosage: str, frequency: str, duration: str, route: str = "Oral") -> tuple:
        """Add a prescription for a patient."""
        try:
            success, prescription_id = self.scribe.add_prescription(
                visit_id=visit_id,
                patient_id=patient_id,
                medicine_name=medicine_name,
                dosage=dosage,
                frequency=frequency,
                duration=duration,
                route=route
            )
            return success, prescription_id
        except Exception as e:
            st.error(f"Error adding prescription: {e}")
            return False, None
    
    def get_patient_prescriptions_df(self, patient_id: str) -> pd.DataFrame:
        """Get all prescriptions for a patient as DataFrame."""
        try:
            prescriptions = self.session.query(Prescription).filter(
                Prescription.patient_id == patient_id
            ).all()
            
            if not prescriptions:
                return pd.DataFrame()
            
            data = []
            for presc in prescriptions:
                data.append({
                    "Medicine": presc.medicine_name,
                    "Dosage": presc.dosage,
                    "Frequency": presc.frequency,
                    "Duration": presc.duration,
                    "Route": presc.route or "Oral",
                    "Indication": presc.indication or "N/A",
                    "Date": presc.date_prescribed.strftime("%Y-%m-%d") if presc.date_prescribed else "N/A"
                })
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading prescriptions: {e}")
            return pd.DataFrame()
    
    # ===================== UTILITY OPERATIONS =====================
    
    def get_database_stats(self) -> dict:
        """Get database statistics."""
        try:
            return self.scribe.get_database_stats()
        except Exception as e:
            st.error(f"Error getting stats: {e}")
            return {}
    
    def search_patients(self, search_term: str) -> pd.DataFrame:
        """Search patients by name or ID."""
        try:
            patients = self.session.query(Patient).filter(
                (Patient.name.ilike(f"%{search_term}%")) |
                (Patient.patient_id.ilike(f"%{search_term}%"))
            ).all()
            
            if not patients:
                return pd.DataFrame()
            
            data = []
            for p in patients:
                data.append({
                    "Patient ID": p.patient_id,
                    "Name": p.name,
                    "Age": p.age,
                    "Gender": p.gender,
                    "Phone": p.phone,
                    "Visits": p.visit_count
                })
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error searching patients: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close database session."""
        try:
            self.session.close()
        except:
            pass
