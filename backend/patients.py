"""
Patient data module with 10 detailed synthetic patient profiles.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

SYNTHETIC_PATIENTS = [
    {
        "patient_id": "PAT001",
        "name": "Amit Kumar Singh",
        "age": 62,
        "gender": "Male",
        "blood_group": "O+",
        "chronic_conditions": ["Hypertension", "Type 2 Diabetes"],
        "phone": "9876543210",
        "email": "amit.singh@email.com",
        "address": "45 MG Road, Bangalore",
        "visit_count": 15,
        "last_visit": "2026-02-20"
    },
    {
        "patient_id": "PAT002",
        "name": "Priya Sharma",
        "age": 45,
        "gender": "Female",
        "blood_group": "A+",
        "chronic_conditions": ["Asthma", "Hypothyroidism"],
        "phone": "9123456789",
        "email": "priya.sharma@email.com",
        "address": "12 Park Lane, Mumbai",
        "visit_count": 8,
        "last_visit": "2026-02-18"
    },
    {
        "patient_id": "PAT003",
        "name": "Rajesh Gupta",
        "age": 58,
        "gender": "Male",
        "blood_group": "B+",
        "chronic_conditions": ["Coronary Artery Disease", "Atrial Fibrillation"],
        "phone": "9988776655",
        "email": "rajesh.gupta@email.com",
        "address": "78 Delhi Gate, Delhi",
        "visit_count": 22,
        "last_visit": "2026-02-21"
    },
    {
        "patient_id": "PAT004",
        "name": "Sunita Pandey",
        "age": 72,
        "gender": "Female",
        "blood_group": "AB-",
        "chronic_conditions": ["Osteoarthritis", "Chronic Kidney Disease Stage 3"],
        "phone": "8765432109",
        "email": "sunita.pandey@email.com",
        "address": "23 Kolkata Avenue, Kolkata",
        "visit_count": 12,
        "last_visit": "2026-02-19"
    },
    {
        "patient_id": "PAT005",
        "name": "Vikram Mehta",
        "age": 51,
        "gender": "Male",
        "blood_group": "O-",
        "chronic_conditions": ["Rheumatoid Arthritis", "Depression"],
        "phone": "9654321098",
        "email": "vikram.mehta@email.com",
        "address": "56 Pune Terrace, Pune",
        "visit_count": 18,
        "last_visit": "2026-02-17"
    },
    {
        "patient_id": "PAT006",
        "name": "Deepa Nair",
        "age": 38,
        "gender": "Female",
        "blood_group": "B-",
        "chronic_conditions": ["PCOS", "Fatty Liver Disease"],
        "phone": "9876543211",
        "email": "deepa.nair@email.com",
        "address": "34 Kochi Square, Kochi",
        "visit_count": 6,
        "last_visit": "2026-02-16"
    },
    {
        "patient_id": "PAT007",
        "name": "Arjun Rao",
        "age": 67,
        "gender": "Male",
        "blood_group": "A-",
        "chronic_conditions": ["COPD", "Emphysema", "Type 2 Diabetes"],
        "phone": "9555666777",
        "email": "arjun.rao@email.com",
        "address": "89 Chennai Heights, Chennai",
        "visit_count": 19,
        "last_visit": "2026-02-22"
    },
    {
        "patient_id": "PAT008",
        "name": "Neha Chopra",
        "age": 41,
        "gender": "Female",
        "blood_group": "AB+",
        "chronic_conditions": ["Migraines", "Anxiety Disorder"],
        "phone": "9345678901",
        "email": "neha.chopra@email.com",
        "address": "67 Jaipur Junction, Jaipur",
        "visit_count": 9,
        "last_visit": "2026-02-15"
    },
    {
        "patient_id": "PAT009",
        "name": "Sanjay Verma",
        "age": 55,
        "gender": "Male",
        "blood_group": "O+",
        "chronic_conditions": ["Metabolic Syndrome", "Sleep Apnea"],
        "phone": "9876543213",
        "email": "sanjay.verma@email.com",
        "address": "91 Lucknow Park, Lucknow",
        "visit_count": 14,
        "last_visit": "2026-02-14"
    },
    {
        "patient_id": "PAT010",
        "name": "Meera Bhat",
        "age": 49,
        "gender": "Female",
        "blood_group": "A+",
        "chronic_conditions": ["Systemic Lupus Erythematosus", "Nephritic Syndrome"],
        "phone": "9123456788",
        "email": "meera.bhat@email.com",
        "address": "15 Bangalore Tech Park, Bangalore",
        "visit_count": 11,
        "last_visit": "2026-02-13"
    }
]


class PatientManager:
    """Manage patient data and directory."""
    
    def __init__(self, patient_file: str = "patients.json"):
        self.patient_file = patient_file
        self.patients = self._load_patients()
    
    def _load_patients(self) -> List[Dict]:
        """Load patients from JSON or initialize with synthetic data."""
        if Path(self.patient_file).exists():
            with open(self.patient_file, 'r') as f:
                return json.load(f)
        
        self._save_patients(SYNTHETIC_PATIENTS)
        return SYNTHETIC_PATIENTS
    
    def _save_patients(self, patients: List[Dict]):
        """Save patients to JSON file."""
        with open(self.patient_file, 'w') as f:
            json.dump(patients, f, indent=4)
    
    def get_all_patients(self) -> List[Dict]:
        """Get all patients."""
        return self.patients
    
    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get a specific patient by ID."""
        for patient in self.patients:
            if patient["patient_id"] == patient_id:
                return patient
        return None
    
    def search_patients(self, query: str) -> List[Dict]:
        """Search patients by name or ID."""
        query_lower = query.lower()
        return [
            p for p in self.patients
            if query_lower in p["name"].lower() or query_lower in p["patient_id"].lower()
        ]
    
    def add_visit(self, patient_id: str):
        """Increment visit count and update last visit date."""
        for patient in self.patients:
            if patient["patient_id"] == patient_id:
                patient["visit_count"] = patient.get("visit_count", 0) + 1
                patient["last_visit"] = datetime.now().strftime("%Y-%m-%d")
                self._save_patients(self.patients)
                return True
        return False
    
    def get_patient_summary(self, patient_id: str) -> Dict:
        """Get a summary of patient info for quick reference."""
        patient = self.get_patient(patient_id)
        if not patient:
            return {}
        
        return {
            "id": patient["patient_id"],
            "name": patient["name"],
            "age": patient["age"],
            "blood_group": patient["blood_group"],
            "conditions": ", ".join(patient["chronic_conditions"]),
            "visit_count": patient["visit_count"],
            "last_visit": patient["last_visit"]
        }
