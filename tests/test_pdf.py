
import json
from pdf_report import generate_hospital_report

test_soap = {
    "subjective": "Patient reports chest pain and shortness of breath for 2 days.",
    "objective": "Heart rate 92 bpm, BP 138/88. Clear lungs.",
    "assessment": "Stable angina, rule out MI.",
    "plan": "Schedule stress test, continue aspirin.",
    "icd10_codes": [{"icd10_code": "I20.9", "description": "Angina pectoris, unspecified"}],
    "medications_prescribed": [{"name": "Aspirin", "dosage": "75mg", "frequency": "OD", "duration": "Lifetime", "route": "Oral"}]
}

test_patient = {
    "name": "Calvin Harris",
    "patient_id": "PAT-999",
    "age": 42,
    "gender": "Male",
    "blood_group": "O+",
    "phone": "+91-9876543210",
    "allergies": ["Penicillin"]
}

test_visit = {
    "chief_complaint": "Chest pain",
    "visit_type": "Outpatient",
    "department": "Cardiology"
}

pdf_bytes = generate_hospital_report(test_soap, test_patient, test_visit)
if pdf_bytes:
    with open("test_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("✅ PDF generated successfully: test_report.pdf")
else:
    print("❌ PDF generation failed.")
