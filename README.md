# 🏥 ScribeAI Clinical OS

**Ambient Clinical Voice Documentation Platform**

A comprehensive, production-grade clinical documentation and analytics system designed to reduce physician burnout through intelligent SOAP note generation, patient management, and clinical decision support.

---

## ✨ Features

### Core Features
1. **🔐 Multi-Step Authentication**
   - Secure clinician login with hashed passwords
   - Role-based access control (Physician, Cardiologist, Nurse)
   - Session management

2. **👥 Patient Directory & Dashboard**
   - 10 detailed synthetic patient profiles pre-populated
   - Patient_ID, Name, Age, Gender, Blood Group, Chronic Conditions
   - Search and filter capabilities
   - Visit history and medical record tracking

3. **💊 Medicine Directory**
   - 1000+ searchable medicines database
   - Columns: Drug_Name, Category, Dosage_Form, Side_Effects, Typical_Dose
   - Smart search by drug name, category, or ID
   - Medicine filtering by therapeutic category

4. **🎙️ Scriber AI (Core Feature)**
   - Ambient clinical voice documentation
   - Whisper-based audio transcription (future integration)
   - Speaker diarization to identify doctor vs patient
   - Automatic SOAP note generation
   - **ABDM Compliance**: Ayushman Bharat Digital Mission standards
   - **ICD-10 Coding**: Automatic diagnostic code mapping

5. **📊 Analytics Engine**
   - Top diagnoses frequency charts
   - Most prescribed medications dashboard
   - Patient classification by disease/department
   - Visit statistics and trends
   - ABDM compliance metrics
   - ICD-10 code usage summary

6. **📋 Clinical Standards Sidebar**
   - ABDM compliance information
   - HIPAA/GDPR data privacy guidelines
   - ICD-10 coding standards
   - HL7 FHIR interoperability reference

### Advanced Add-ons

1. **🚨 Smart-Risk Alerts**
   - Drug-drug interaction detection
   - Clinical decision support
   - Medication safety monitoring
   - Customizable alert sensitivity

2. **📚 Patient Education Generator**
   - Convert clinical plan to patient-friendly instructions
   - Multi-language support (English, Hindi, Tamil, Telugu)
   - Home care instructions generation
   - Compliance reminder generation

3. **🔍 Auto-ICD-10-Coder**
   - Automatic mapping of assessment to ICD-10 codes
   - Confidence scoring for code suggestions
   - Bulk coding for multiple diagnoses

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip or conda
- FFmpeg (for audio processing)
- Ollama (for local LLM, optional)

### Installation

1. **Clone or download the repository**
   ```bash
   cd impact
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Ollama (for BioMistral LLM)**
   ```bash
   # Download and install from https://ollama.ai
   ollama pull cniongolo/biomistral
   ollama serve  # Run in background or separate terminal
   ```

5. **Run the Streamlit application**
   ```bash
   streamlit run app.py
   ```
   
   The application will open at `http://localhost:8501`

---

## 📚 Usage

### Login

**Demo Credentials:**
- Username: `dr_sharma`
- Password: `password123`

Other available accounts:
- `dr_patel` / `password456` (Cardiologist)
- `nurse_verma` / `password789` (Registered Nurse)

### Workflow Example

1. **Login** as a clinician
2. **View Dashboard** - See visit statistics and top diagnoses
3. **Select Patient** from "Patients" tab
4. **Create SOAP Note** in "Scriber AI" tab
   - Input transcript or use template
   - System auto-generates ABDM-compliant SOAP note
   - ICD-10 codes automatically assigned
   - Patient education instructions generated
5. **Check Drug Interactions** in "Add-ons" tab
6. **Review Analytics** in "Analytics" tab

---

## 📁 Project Structure

```
impact/
├── app.py                  # Main Streamlit application
├── auth.py                 # Authentication & credential management
├── patients.py             # Patient directory & management
├── medicines.py            # Medicine database & search
├── scriber.py              # Scriber AI core module (SOAP generation)
├── analytics.py            # Analytics engine & reporting
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── soap_note.json          # Sample SOAP note (if exists)
├── credentials.json        # User credentials (auto-generated)
├── patients.json           # Patient database (auto-generated)
├── medicines.json          # Medicine database (auto-generated)
└── medical_records.json    # SOAP notes TinyDB (auto-generated)
```

---

## 🔧 Configuration

### Database
- **TinyDB** is used for storing SOAP notes and medical records
- Files are stored as JSON in the workspace directory

### Authentication
- Passwords are hashed using SHA-256 with salt
- Credentials stored in `credentials.json`
- Default clinicians auto-loaded on first run

### Clinical Standards
- **ABDM**: Notes marked compliant when all SOAP sections are populated
- **ICD-10**: Automatic mapping of conditions to diagnostic codes
- **HIPAA/GDPR**: Data privacy guidelines displayed in sidebar

---

## 🤖 AI Components

### Whisper (Audio Transcription)
- Converts ambient clinical audio to text
- Optimized for medical terminology
- Works offline with local models

### BioMistral-7B (LLM)
- Run via Ollama for local processing
- Specialized for clinical text analysis
- SOAP note generation and enhancement
- Medical entity extraction

### pyannote.audio (Speaker Diarization)
- Identifies who is speaking (doctor vs patient)
- Attributes medical observations correctly
- Requires HuggingFace authentication token

---

## 📊 Analytics Features

### Dashboards
- **Doctor Dashboard**: Personal visit metrics and top diagnoses
- **Analytics Tab**: Comprehensive clinic statistics
- **Disease Distribution**: Patient breakdown by department/disease

### Reports
- Top diagnoses frequency
- Most prescribed medications
- ICD-10 code usage
- ABDM compliance metrics
- Clinician performance

---

## 🔐 Security & Compliance

### Data Security
- AES encryption for sensitive fields (implement in production)
- Audit trails for all clinical actions
- Role-based access control

### Compliance
- **ABDM**: Ayushman Bharat Digital Mission standards
- **HIPAA**: Health Insurance Portability and Accountability Act
- **GDPR**: General Data Protection Regulation
- **ICD-10**: Standardized diagnostic coding
- **HL7 FHIR**: Interoperability standards

---

## 🚨 Important Notes

### Current Limitations
1. Audio recording is not yet integrated (template provided)
2. BioMistral integration requires local Ollama setup
3. Drug interaction database is simplified (implement comprehensive DB in production)
4. Uses mock analytics data (connect to real SOAP note database)

### Future Enhancements
- Real-time audio streaming and processing
- Advanced NLP for better entity extraction
- Integration with EHR systems
- Multi-language clinical notes support
- Mobile app for patient follow-up
- Integration with medical imaging systems
- Real-time collaboration for consultations

---

## 🐛 Troubleshooting

### "Could not find module 'libtorchcodec_core*.dll'"
- This is a warning if FFmpeg is not properly installed
- Install FFmpeg: https://ffmpeg.org/download.html

### "Ollama connection refused"
- Ensure Ollama is running: `ollama serve`
- BioMistral model downloaded: `ollama pull cniongolo/biomistral`

### "HuggingFace token error for pyannote"
- Get token from: https://huggingface.co/settings/tokens
- Update HF_TOKEN in `scriber.py` or environment variable

### "ModuleNotFoundError" when running app
- Ensure all packages installed: `pip install -r requirements.txt`
- Verify virtual environment is activated

---

## 📖 API Reference

### ScribeAI Class
```python
from scriber import ScribeAI

scribe = ScribeAI()

# Process transcript to SOAP note
note = scribe.process_transcript(transcript, patient_id, clinician_id)

# Save to database
visit_id = scribe.save_soap_note(note)

# Retrieve notes
patient_notes = scribe.get_patient_notes(patient_id)
```

### PatientManager
```python
from patients import PatientManager

patients = PatientManager()

# Search patients
results = patients.search_patients("Sharma")

# Get patient details
patient = patients.get_patient("PAT001")
```

### MedicineManager
```python
from medicines import MedicineManager

medicines = MedicineManager()

# Search medicines
results = medicines.search_medicines("Metformin")

# Check interactions
interactions = medicines.check_drug_interactions(["MED011", "MED006"])
```

---

## 📞 Support & Contact

For issues, feature requests, or contributions:
- GitHub Issues: [Create Issue]
- Documentation: See README.md
- Email: support@scribeai.com

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

## 🎯 Roadmap

- [ ] Real-time audio processing pipeline
- [ ] Advanced drug interaction database
- [ ] Patient portal for education access
- [ ] Telemedicine integration
- [ ] Mobile app (iOS/Android)
- [ ] Integration with major EHR systems
- [ ] Advanced analytics with ML predictions
- [ ] Multi-language clinical documentation

---

**Built with ❤️ for reducing physician burnout and improving patient care**

ScribeAI Clinical OS - Transforming Clinical Documentation
