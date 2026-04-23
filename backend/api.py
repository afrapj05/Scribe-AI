"""
ScribeAI Clinical OS - FastAPI Backend
REST API that serves the Next.js frontend.
Wraps all existing Python modules (auth, database, medicines, analytics, translations).
"""

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime, timedelta
import re, base64

from auth import authenticate_user
from medicines import MedicineManager
from analytics import AnalyticsEngine
from translations import get_language_list, get_translation, preload_language, BASE_STRINGS
from db_manager import DatabaseManager
from database import Session as DBSession, Patient, Visit, SoapNote, Prescription
from collections import Counter

# ── JWT helpers ────────────────────────────────────────────────────────────────
from jose import jwt, JWTError

# JWT Configuration — loaded from environment ONLY (never hardcoded)
_jwt_secret = os.getenv("JWT_SECRET_KEY")
if not _jwt_secret:
    raise RuntimeError(
        "Missing required environment variable: JWT_SECRET_KEY\n"
        "Add a strong random secret to your .env file:\n"
        "  JWT_SECRET_KEY=<generate with: python -c 'import secrets; print(secrets.token_hex(32))'>"
    )
SECRET_KEY = _jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return decode_token(credentials.credentials)


# ── App init ───────────────────────────────────────────────────────────────────
app = FastAPI(title="ScribeAI Clinical OS API", version="2.0.0")


@app.on_event("startup")
async def _on_startup():
    """Run safe DB migrations whenever the server starts."""
    try:
        from migrate_db import run_migrations
        run_migrations()
    except Exception as e:
        print(f"[startup] Migration warning: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

medicine_mgr = MedicineManager()
db_mgr = DatabaseManager()


# ── Pydantic models ────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str = "Other"
    blood_group: str = "O+"
    phone: str = ""
    email: str = ""
    allergies: List[str] = []
    chronic_conditions: List[str] = []


class SoapRequest(BaseModel):
    patient_id: str
    chief_complaint: str
    transcript: str
    clinician_id: str = "default"
    dept: str = "General"
    language: str = "en"   # clinician's chosen language code for multilingual pipeline


class PrescriptionCreate(BaseModel):
    patient_id: str
    medicine_name: str
    dosage: str
    frequency: str
    duration: str
    route: str = "Oral"


# ── Auth endpoints ─────────────────────────────────────────────────────────────
@app.post("/api/auth/login")
def login(req: LoginRequest):
    is_valid, user_info = authenticate_user(req.username, req.password)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": req.username, "user": user_info})
    return {"token": token, "user": user_info}


@app.get("/api/auth/me")
def me(user=Depends(get_current_user)):
    return user.get("user", {})


# ── Dashboard ──────────────────────────────────────────────────────────────────
@app.get("/api/dashboard")
def dashboard(user=Depends(get_current_user)):
    stats = db_mgr.get_database_stats()
    session = DBSession()
    try:
        week_ago = datetime.now() - timedelta(days=7)
        visits_7d = session.query(Visit).filter(Visit.visit_date >= week_ago).count()
        patients = session.query(Patient).all()
        high_risk = sum(1 for p in patients if len(p.chronic_conditions or []) >= 2)
        chronic = sum(1 for p in patients if p.chronic_conditions)
        return {
            "total_patients": stats.get("total_patients", 0),
            "total_visits": stats.get("total_visits", 0),
            "total_soap_notes": stats.get("total_soap_notes", 0),
            "total_audio": stats.get("total_audio_recordings", 0),
            "visits_7d": visits_7d,
            "high_risk_patients": high_risk,
            "patients_with_chronic": chronic,
        }
    finally:
        session.close()


# ── Patients ───────────────────────────────────────────────────────────────────
@app.get("/api/patients")
def list_patients(search: str = "", user=Depends(get_current_user)):
    session = DBSession()
    try:
        q = session.query(Patient)
        if search:
            q = q.filter(Patient.name.ilike(f"%{search}%"))
        patients = q.order_by(Patient.name).all()
        return [
            {
                "id": p.patient_id,
                "name": p.name,
                "age": p.age,
                "gender": p.gender,
                "blood_group": p.blood_group,
                "phone": p.phone,
                "email": p.email,
                "allergies": p.allergies or [],
                "chronic_conditions": p.chronic_conditions or [],
            }
            for p in patients
        ]
    finally:
        session.close()


@app.post("/api/patients", status_code=201)
def create_patient(req: PatientCreate, user=Depends(get_current_user)):
    success, patient_id = db_mgr.create_patient(
        name=req.name,
        age=req.age,
        gender=req.gender,
        blood_group=req.blood_group,
        phone=req.phone,
        email=req.email,
        allergies=req.allergies,
        chronic_conditions=req.chronic_conditions,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create patient")
    return {"id": patient_id, "name": req.name}


@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: str, user=Depends(get_current_user)):
    session = DBSession()
    try:
        p = session.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Patient not found")
        visits = session.query(Visit).filter(Visit.patient_id == patient_id).order_by(Visit.visit_date.desc()).all()
        return {
            "id": p.patient_id,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "blood_group": p.blood_group,
            "phone": p.phone,
            "email": p.email,
            "allergies": p.allergies or [],
            "chronic_conditions": p.chronic_conditions or [],
            "visits": [
                {
                    "id": v.visit_id,
                    "chief_complaint": v.chief_complaint,
                    "date": v.visit_date.isoformat() if v.visit_date else None,
                    "dept": v.department,
                }
                for v in visits
            ],
        }
    finally:
        session.close()


# ── SOAP / Scriber ─────────────────────────────────────────────────────────────
@app.post("/api/scriber/generate-soap")
def generate_soap(req: SoapRequest, user=Depends(get_current_user)):
    from scriber_enhanced import ScribeAI
    try:
        scribe = ScribeAI()
        success, soap = scribe.generate_soap_with_llm(
            transcript=req.transcript,
            language=req.language,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ScribeAI init/call error: {exc}")

    if not success or not soap:
        raise HTTPException(status_code=500, detail=soap.get("error", "SOAP generation failed") if isinstance(soap, dict) else "SOAP generation failed")

    # Enrich with chief complaint if missing
    if not soap.get("chief_complaint"):
        soap["chief_complaint"] = req.chief_complaint

    # Save to DB
    try:
        success_v, visit_id = db_mgr.create_visit(
            patient_id=req.patient_id,
            clinician_id=req.clinician_id,
            chief_complaint=req.chief_complaint,
            department=req.dept,
        )
        note_id = None
        if success_v:
            _, note_id = db_mgr.save_soap_from_visit(visit_id, soap)
    except Exception:
        visit_id, note_id = None, None

    return {"soap": soap, "visit_id": visit_id, "note_id": note_id}


class PatientEduRequest(BaseModel):
    soap: Dict[str, Any]
    language: str = "en"


@app.post("/api/scriber/patient-education")
def patient_education(req: PatientEduRequest, user=Depends(get_current_user)):
    """Generate a multilingual patient-friendly handout from a SOAP note using BioMistral."""
    from scriber_enhanced import ScribeAI
    try:
        scribe = ScribeAI()
        education = scribe.generate_patient_education(req.soap, language=req.language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Patient education error: {exc}")
    return {"education": education, "language": req.language, "links": []}


# ── Medical Report / Prescription Scanner ──────────────────────────────────────
@app.post("/api/scan-report")
async def scan_report(file: UploadFile = File(...), user=Depends(get_current_user)):
    """
    Accepts an uploaded image (prescription, lab report, discharge summary, etc.)
    and uses qwen2.5vl:3b vision model via Ollama to extract structured clinical data.
    """
    try:
        import ollama as _ollama
    except ImportError:
        raise HTTPException(status_code=503, detail="Ollama not installed on the server.")

    # Read and base64-encode the image
    image_bytes = await file.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Determine MIME type from the upload filename
    fname = (file.filename or "").lower()
    if fname.endswith(".png"):
        mime = "image/png"
    elif fname.endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    elif fname.endswith(".webp"):
        mime = "image/webp"
    else:
        mime = "image/jpeg"  # safe default

    system_prompt = (
        "You are an expert clinical document analyst. "
        "Carefully read the medical document image and extract all information. "
        "Return ONLY valid JSON with EXACTLY these keys:\n"
        "  document_type: string (one of: Prescription, Lab Report, Discharge Summary, Radiology Report, Other)\n"
        "  patient_name: string or null\n"
        "  patient_age: string or null\n"
        "  patient_id: string or null\n"
        "  date: string or null\n"
        "  doctor_name: string or null\n"
        "  hospital: string or null\n"
        "  diagnoses: array of strings\n"
        "  medications: array of objects {name, dose, frequency, duration, route}\n"
        "  lab_values: array of objects {test, value, unit, reference_range, flag} where flag is 'HIGH','LOW','NORMAL', or null\n"
        "  clinical_notes: string (any other important clinical observations)\n"
        "  full_summary: string (2-3 sentence plain-English summary of the document)\n"
        "Do NOT include markdown fences or extra commentary."
    )

    try:
        response = _ollama.chat(
            model="qwen2.5vl:3b",
            messages=[
                {
                    "role": "user",
                    "content": "Extract all clinical information from this medical document and return structured JSON.",
                    "images": [image_b64],
                }
            ],
            options={"temperature": 0.1, "num_predict": 1200},
        )
        raw = response.get("message", {}).get("content", "{}")

        # Strip markdown fences if model adds them
        import re as _re
        raw = _re.sub(r"^```[a-z]*\n?", "", raw.strip())
        raw = _re.sub(r"\n?```$", "", raw.strip())

        import json as _json
        result = _json.loads(raw)
        result["model"] = "qwen2.5vl:3b"
        result["filename"] = file.filename

        # Persist to scan_results table
        try:
            import sqlite3 as _sq, uuid as _uuid, os as _os
            _db = _os.getenv("DATABASE_URL", "sqlite:///clinical_records.db").replace("sqlite:///", "")
            _conn = _sq.connect(_db)
            _conn.execute(
                """INSERT INTO scan_results
                   (scan_id, filename, document_type, patient_name, patient_age,
                    scan_date, doctor_name, hospital_name, diagnoses, medications,
                    lab_values, clinical_notes, full_summary, model_used, created_by)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(_uuid.uuid4()),
                    file.filename,
                    result.get("document_type", ""),
                    result.get("patient_name", ""),
                    result.get("patient_age", ""),
                    result.get("date", ""),
                    result.get("doctor_name", ""),
                    result.get("hospital", ""),
                    _json.dumps(result.get("diagnoses", [])),
                    _json.dumps(result.get("medications", [])),
                    _json.dumps(result.get("lab_values", [])),
                    result.get("clinical_notes", ""),
                    result.get("full_summary", ""),
                    "qwen2.5vl:3b",
                    user.get("sub", "unknown") if isinstance(user, dict) else "unknown",
                )
            )
            _conn.commit()
            _conn.close()
        except Exception as _db_exc:
            print(f"[scan_report] DB persist warning: {_db_exc}")

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Report scanning failed: {str(exc)}"
        )



# ── Scan results history ───────────────────────────────────────────────────────
@app.get("/api/scan-results")
def list_scan_results(limit: int = 20, user=Depends(get_current_user)):
    """Return recent scan results from the database."""
    import sqlite3 as _sq, json as _json, os as _os
    _db = _os.getenv("DATABASE_URL", "sqlite:///clinical_records.db").replace("sqlite:///", "")
    try:
        conn = _sq.connect(_db)
        conn.row_factory = _sq.Row
        rows = conn.execute(
            "SELECT * FROM scan_results ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            for field in ("diagnoses", "medications", "lab_values"):
                try:
                    d[field] = _json.loads(d.get(field) or "[]")
                except Exception:
                    d[field] = []
            results.append(d)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── WhatsApp reminder ──────────────────────────────────────────────────────────
class WhatsAppRequest(BaseModel):
    to_number: str           # E.164 format, e.g. '+91XXXXXXXXXX'
    patient_name: str = ""
    appointment_date: str    # e.g. '12/1'
    appointment_time: str    # e.g. '3pm'


@app.post("/api/notify/whatsapp")
def send_whatsapp(req: WhatsAppRequest, user=Depends(get_current_user)):
    """Send a WhatsApp appointment reminder via Twilio."""
    from whatsapp_helper import send_appointment_reminder
    result = send_appointment_reminder(
        to_number=req.to_number,
        appointment_date=req.appointment_date,
        appointment_time=req.appointment_time,
        patient_name=req.patient_name,
        created_by=user.get("sub", "system") if isinstance(user, dict) else "system",
    )
    if not result["success"]:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


# ── PDF Hospital Report ────────────────────────────────────────────────────────
class PdfReportRequest(BaseModel):
    soap: Dict[str, Any]
    patient: Dict[str, Any]
    visit: Optional[Dict[str, Any]] = None


@app.post("/api/report/pdf")
def generate_pdf_report(req: PdfReportRequest, user=Depends(get_current_user)):
    """Generate and stream a PDF hospital report."""
    from fastapi.responses import Response
    from pdf_report import generate_hospital_report, HAS_REPORTLAB
    if not HAS_REPORTLAB:
        raise HTTPException(
            status_code=503,
            detail="reportlab not installed. Run: pip install reportlab"
        )
    pdf_bytes = generate_hospital_report(
        soap=req.soap,
        patient=req.patient,
        visit=req.visit,
    )
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation failed.")
    patient_name = (req.patient.get("name") or "patient").replace(" ", "_")
    filename = f"Silverline_Report_{patient_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/soap")
def list_soap_notes(limit: int = 10, user=Depends(get_current_user)):
    session = DBSession()
    try:
        notes = session.query(SoapNote).order_by(SoapNote.created_at.desc()).limit(limit).all()
        return [
            {
                "id": n.note_id,
                "visit_id": n.visit_id,
                "subjective": n.subjective,
                "objective": n.objective,
                "assessment": n.assessment,
                "plan": n.plan,
                "icd10_codes": n.icd10_codes or [],
                "language": n.language,
                "subjective_localized": n.subjective_localized,
                "objective_localized": n.objective_localized,
                "assessment_localized": n.assessment_localized,
                "plan_localized": n.plan_localized,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ]
    finally:
        session.close()


# ── Medicines ──────────────────────────────────────────────────────────────────
@app.get("/api/medicines")
def list_medicines(
    search: str = "",
    category: str = "",
    page: int = 1,
    page_size: int = 50,
    include_discontinued: bool = False,
    user=Depends(get_current_user),
):
    if search:
        meds = medicine_mgr.search_medicines(search)
    elif category and category != "All":
        meds = medicine_mgr.get_medicines_by_category(category)
    else:
        meds = medicine_mgr.get_all_medicines()

    if not include_discontinued:
        meds = [m for m in meds if not m.get("is_discontinued")]

    total = len(meds)
    start = (page - 1) * page_size
    page_meds = meds[start : start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "source": medicine_mgr.source_label,
        "items": [
            {
                "id": m.get("id", ""),
                "name": m.get("drug_name", ""),
                "category": m.get("category", ""),
                "form": m.get("dosage_form", ""),
                "manufacturer": m.get("manufacturer", ""),
                "composition": m.get("composition", ""),
                "pack_size": m.get("pack_size", ""),
                "price": m.get("price"),
                "discontinued": m.get("is_discontinued", False),
            }
            for m in page_meds
        ],
    }


@app.get("/api/medicines/categories")
def medicine_categories(user=Depends(get_current_user)):
        return {"categories": medicine_mgr.get_unique_categories()}


# ── Analytics ──────────────────────────────────────────────────────────────────
@app.get("/api/analytics")
def get_analytics(user=Depends(get_current_user)):
    from analytics import get_clinical_analytics
    return get_clinical_analytics()


# ── Prescriptions ──────────────────────────────────────────────────────────────
@app.post("/api/prescriptions", status_code=201)
def add_prescription(req: PrescriptionCreate, user=Depends(get_current_user)):
    success, presc_id = db_mgr.add_prescription(
        patient_id=req.patient_id,
        medicine_name=req.medicine_name,
        dosage=req.dosage,
        frequency=req.frequency,
        duration=req.duration,
        route=req.route,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add prescription")
    return {"id": presc_id}


# ── Translations ───────────────────────────────────────────────────────────────
@app.get("/api/languages")
def languages():
    return {"languages": get_language_list()}


@app.get("/api/translations/{lang}")
def translations(lang: str):
    preload_language(lang)
    strings = {key: get_translation(lang, key) for key in BASE_STRINGS}
    return {"lang": lang, "strings": strings}


# ── Database stats ─────────────────────────────────────────────────────────────
@app.get("/api/database/stats")
def db_stats(user=Depends(get_current_user)):
    return db_mgr.get_database_stats()


@app.get("/api/database/visits")
def db_visits(limit: int = 50, user=Depends(get_current_user)):
    session = DBSession()
    try:
        visits = session.query(Visit).order_by(Visit.visit_date.desc()).limit(limit).all()
        return [
            {
                "id": v.visit_id,
                "patient_id": v.patient_id,
                "chief_complaint": v.chief_complaint,
                "dept": v.department,
                "date": v.visit_date.isoformat() if v.visit_date else None,
                "clinician_id": v.clinician_id,
            }
            for v in visits
        ]
    finally:
        session.close()


@app.get("/api/database/prescriptions")
def db_prescriptions(limit: int = 50, user=Depends(get_current_user)):
    session = DBSession()
    try:
        rows = session.query(Prescription).order_by(Prescription.date_prescribed.desc()).limit(limit).all()
        return [
            {
                "id": p.prescription_id,
                "patient_id": p.patient_id,
                "medicine": p.medicine_name,
                "dosage": p.dosage,
                "frequency": p.frequency,
                "duration": p.duration,
                "route": p.route or "Oral",
                "date": p.date_prescribed.strftime("%Y-%m-%d") if p.date_prescribed else None,
            }
            for p in rows
        ]
    finally:
        session.close()


# ── Public API Proxies (no auth required – data is public) ──────────────────────
import httpx, asyncio

@app.get("/api/public/drug-recalls")
async def drug_recalls(drug: str = "", limit: int = 5):
    """OpenFDA drug enforcement (recall) data."""
    try:
        search = f'&search=product_description:"{drug}"' if drug else ""
        url = f"https://api.fda.gov/drug/enforcement.json?limit={limit}{search}"
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(url)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            return {
                "source": "OpenFDA",
                "total": data.get("meta", {}).get("results", {}).get("total", len(results)),
                "results": [
                    {
                        "product": item.get("product_description", "")[:120],
                        "reason": item.get("reason_for_recall", "")[:200],
                        "status": item.get("status", ""),
                        "class": item.get("classification", ""),
                        "date": item.get("recall_initiation_date", ""),
                        "company": item.get("recalling_firm", ""),
                    }
                    for item in results
                ],
            }
    except Exception:
        pass
    return {"source": "OpenFDA", "total": 0, "results": []}


@app.get("/api/public/rxnorm")
async def rxnorm_search(q: str):
    """NLM RxNorm drug concept lookup."""
    if not q:
        return {"results": []}
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={q}"
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(url)
        if r.status_code == 200:
            data = r.json()
            groups = data.get("drugGroup", {}).get("conceptGroup", [])
            items = []
            for g in groups:
                for prop in g.get("conceptProperties", []):
                    items.append({
                        "rxcui": prop.get("rxcui"),
                        "name": prop.get("name"),
                        "synonym": prop.get("synonym", ""),
                        "tty": prop.get("tty"),
                    })
            return {"query": q, "results": items[:20]}
    except Exception:
        pass
    return {"query": q, "results": []}


@app.get("/api/public/disease-stats")
async def disease_stats():
    """Global disease statistics from disease.sh."""
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get("https://disease.sh/v3/covid-19/all")
        if r.status_code == 200:
            d = r.json()
            return {
                "source": "disease.sh / WHO",
                "covid": {
                    "cases": d.get("cases", 0),
                    "deaths": d.get("deaths", 0),
                    "recovered": d.get("recovered", 0),
                    "active": d.get("active", 0),
                    "updated": d.get("updated", 0),
                },
            }
    except Exception:
        pass
    return {"source": "disease.sh", "covid": {}}


@app.get("/api/public/clinical-trials")
async def clinical_trials(condition: str = "hypertension", limit: int = 5):
    """ClinicalTrials.gov open studies for a condition."""
    try:
        url = (
            f"https://clinicaltrials.gov/api/v2/studies"
            f"?query.cond={condition}&filter.overallStatus=RECRUITING&pageSize={limit}&format=json"
        )
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url)
        if r.status_code == 200:
            studies = r.json().get("studies", [])
            out = []
            for s in studies:
                proto = s.get("protocolSection", {})
                id_mod = proto.get("identificationModule", {})
                status_mod = proto.get("statusModule", {})
                cond_mod = proto.get("conditionsModule", {})
                desc_mod = proto.get("descriptionModule", {})
                out.append({
                    "nct_id": id_mod.get("nctId"),
                    "title": id_mod.get("officialTitle", id_mod.get("briefTitle", ""))[:200],
                    "status": status_mod.get("overallStatus"),
                    "phase": proto.get("designModule", {}).get("phases", ["N/A"])[0] if proto.get("designModule") else "N/A",
                    "conditions": cond_mod.get("conditions", [])[:3],
                    "summary": desc_mod.get("briefSummary", "")[:300],
                })
            return {"condition": condition, "source": "ClinicalTrials.gov", "results": out}
    except Exception:
        pass
    return {"condition": condition, "source": "ClinicalTrials.gov", "results": []}


@app.get("/api/public/medlineplus")
async def medlineplus(condition: str = "diabetes"):
    """NLM MedlinePlus health topic summary."""
    try:
        url = f"https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term={condition}&retmax=3"
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(url)
        if r.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.text)
            docs = []
            for doc in root.findall(".//document"):
                title = doc.find(".//content[@name='title']")
                url_el = doc.find(".//content[@name='organizationName']")
                snippet = doc.find(".//content[@name='FullSummary']")
                docs.append({
                    "title": title.text if title is not None else "",
                    "snippet": (snippet.text or "")[:400] if snippet is not None else "",
                    "url": doc.get("url", ""),
                })
            return {"condition": condition, "source": "NLM MedlinePlus", "results": docs}
    except Exception:
        pass
    return {"condition": condition, "source": "NLM MedlinePlus", "results": []}


@app.post("/api/scriber/patient-education")
def generate_patient_education(req: Dict, user=Depends(get_current_user)):
    """Generate patient-friendly instructions from a SOAP note."""
    from scriber_enhanced import ScribeAI
    scribe = ScribeAI()
    education = scribe.generate_patient_education(req.get("soap", {}))
    
    # Enrich with MedlinePlus links for ICD-10 codes found in SOAP
    soap = req.get("soap", {})
    links = []
    for icd in soap.get("icd10_codes", []):
        code = icd.get("icd10_code") if isinstance(icd, dict) else icd
        desc = icd.get("description") if isinstance(icd, dict) else ""
        if code:
            query = desc or code
            links.append({
                "condition": query,
                "url": f"https://medlineplus.gov/search?query={query.replace(' ', '+')}"
            })
            
    return {"education": education, "links": links}

@app.get("/api/medicines/interactions")
def check_interactions(drugs: str):
    """Check for basic drug-drug interactions (demo implementation)."""
    drug_list = [d.strip().lower() for d in drugs.split(",")]
    interactions = []
    
    # Demo rules
    rules = [
        ({"aspirin", "warfarin"}, "Increased risk of bleeding"),
        ({"lisinopril", "spironolactone"}, "Risk of high potassium (hyperkalemia)"),
        ({"simvastatin", "amiodarone"}, "Increased risk of muscle pain (myopathy)"),
        ({"metformin", "contrast dye"}, "Risk of lactic acidosis"),
    ]
    
    for drug_set, warning in rules:
        if drug_set.issubset(set(drug_list)):
            interactions.append({
                "drugs": list(drug_set),
                "severity": "High",
                "warning": warning
            })
            
    return {"interactions": interactions, "count": len(interactions)}

@app.get("/api/public/icd10-search")
async def icd10_search(q: str = ""):
    """ICD-10 code lookup via CMS API."""
    if not q:
        return {"results": []}
    try:
        url = f"https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?sf=code,name&terms={q}&maxList=10"
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(url)
        if r.status_code == 200:
            data = r.json()
            # Response: [total, codes_list, extra, display_strings]
            codes = data[1] if len(data) > 1 else []
            displays = data[3] if len(data) > 3 else []
            results = []
            for i, code in enumerate(codes):
                display = displays[i] if i < len(displays) else [code, ""]
                results.append({"code": display[0] if display else code, "name": display[1] if len(display) > 1 else ""})
            return {"query": q, "results": results}
    except Exception:
        pass
    return {"query": q, "results": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


