"""
ScribeAI Clinical OS - Main Streamlit Application
A comprehensive clinical documentation and analytics platform.
"""

import sys
import os
import re

# --- Windows UTF-8 stdout fix (must be before any emoji prints) ---
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import uuid

# Import custom modules
from auth import authenticate_user
from medicines import MedicineManager
from scriber_enhanced import ScribeAI
from analytics import AnalyticsEngine
from translations import get_translation, get_language_list, translate_all, preload_language
from db_manager import DatabaseManager

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="ScribeAI Clinical OS",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== CUSTOM CSS =====================
st.markdown("""
<style>
    .main { padding-top: 2rem; }
    .metric-card { 
        background-color: #f0f2f6; 
        border-radius: 10px; 
        padding: 20px; 
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        border-radius: 5px;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ===================== SESSION STATE INITIALIZATION =====================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_info = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

# Multilingual support
if "language" not in st.session_state:
    st.session_state.language = "en"
if "preloaded_langs" not in st.session_state:
    st.session_state.preloaded_langs = {"en"}

# Audio recording state
if "recording_active" not in st.session_state:
    st.session_state.recording_active = False
if "recording_duration" not in st.session_state:
    st.session_state.recording_duration = 0.0


def t(key: str, default: str = None) -> str:
    """Shorthand for translation function."""
    return get_translation(st.session_state.language, key, default or key)


# ===================== INITIALIZE MANAGERS =====================
@st.cache_resource
def init_managers():
    medicine_mgr = MedicineManager()
    scribe = ScribeAI()
    db_mgr = DatabaseManager()
    return db_mgr, medicine_mgr, scribe

db_mgr, medicine_mgr, scribe = init_managers()

# ===================== HELPER FUNCTIONS =====================
def display_soap_note(soap_data):
    """Display SOAP note as formatted clinical text instead of JSON."""
    if not soap_data:
        st.warning("No SOAP data available")
        return

    # Guard: if LLM returned a raw string, wrap it
    if isinstance(soap_data, str):
        soap_data = {"subjective": "", "objective": "", "assessment": soap_data, "plan": ""}

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📝 Subjective")
        st.info(soap_data.get('subjective') or "No subjective information recorded")

        st.markdown("### 📋 Assessment")
        st.success(soap_data.get('assessment') or "No assessment recorded")

    with col2:
        st.markdown("### 🔍 Objective")
        st.info(soap_data.get('objective') or "No objective findings recorded")

        st.markdown("### 💊 Plan")
        st.success(soap_data.get('plan') or "No treatment plan recorded")

    # ICD-10 codes (if present)
    codes = soap_data.get('icd10_codes') or soap_data.get('icd_codes')
    if codes:
        st.markdown("### 🏷️ ICD-10 Codes")
        for c in codes:
            if isinstance(c, dict):
                st.write(f"• **{c.get('icd10_code', '')}** — {c.get('condition', '')}")
            else:
                st.write(f"• {c}")


def _format_soap_as_text(soap_data: dict, patient_name: str = "", visit_id: str = "") -> str:
    """Produce a clean, printable plain-text SOAP note."""
    if isinstance(soap_data, str):
        soap_data = {"assessment": soap_data}
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "=" * 60,
        "  SCRIBEAI CLINICAL OS — SOAP NOTE",
        "=" * 60,
        f"Patient  : {patient_name or 'N/A'}",
        f"Visit ID : {visit_id or 'N/A'}",
        f"Generated: {now}",
        "",
        "─" * 60,
        "S — SUBJECTIVE",
        "─" * 60,
        soap_data.get('subjective') or "Not recorded.",
        "",
        "─" * 60,
        "O — OBJECTIVE",
        "─" * 60,
        soap_data.get('objective') or "Not recorded.",
        "",
        "─" * 60,
        "A — ASSESSMENT",
        "─" * 60,
        soap_data.get('assessment') or "Not recorded.",
        "",
        "─" * 60,
        "P — PLAN",
        "─" * 60,
        soap_data.get('plan') or "Not recorded.",
        "",
    ]

    codes = soap_data.get('icd10_codes') or soap_data.get('icd_codes', [])
    if codes:
        lines.append("─" * 60)
        lines.append("ICD-10 CODES")
        lines.append("─" * 60)
        for c in codes:
            if isinstance(c, dict):
                lines.append(f"  {c.get('icd10_code', '')}  {c.get('condition', '')}")
            else:
                lines.append(f"  {c}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("END OF NOTE — ScribeAI Clinical OS")
    return "\n".join(lines)


def display_audio_metadata(metadata):
    """Display audio processing metadata as formatted info instead of JSON."""
    if not metadata:
        st.warning("No metadata available")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Duration", f"{metadata.get('duration', 0):.1f}s")
        st.metric("Sample Rate", f"{metadata.get('sample_rate', 0)} Hz")

    with col2:
        st.metric("Noise Level", f"{metadata.get('noise_level', 0):.2f}")
        st.metric("Filter Type", metadata.get('filter_type', 'None'))

    with col3:
        st.metric("Channels", metadata.get('channels', 0))
        st.metric("Bit Depth", f"{metadata.get('bit_depth', 0)} bit")


def generate_patient_education(clinical_plan, language="en"):
    """Generate patient-friendly educational content from clinical plan, in any Indian language."""
    from translations import _translate_string

    def tl(text):
        if language == "en":
            return text
        return _translate_string(text, language)

    education = f"""
## {tl("Instructions to Follow:")}
{clinical_plan}

---

### {tl("Contact doctor if you experience:")}
- {tl("Severe pain or worsening symptoms")}
- {tl("Fever above 101°F (38.3°C)")}
- {tl("Difficulty breathing")}
- {tl("Persistent vomiting")}

### {tl("Follow-up Appointment:")}
{tl("Please schedule a follow-up visit in 1 week.")}

**{tl("Important:")}** {tl("Follow these instructions carefully and take all medications as prescribed.")}
"""
    return education.strip()


# ===================== LOGIN PAGE =====================
def show_login_page():
    """Display login page with full multilingual support."""
    # Language picker on the login screen too
    lang_list = get_language_list()
    lang_keys = list(lang_list.keys())

    col_top = st.columns([3, 1])
    with col_top[1]:
        login_lang = st.selectbox(
            "🌐",
            lang_keys,
            format_func=lambda x: lang_list[x],
            index=lang_keys.index(st.session_state.language),
            key="login_lang_selector",
            label_visibility="collapsed",
        )
        if login_lang != st.session_state.language:
            st.session_state.language = login_lang
            st.rerun()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"## 🏥 {t('app_title')}")
        st.markdown(f"**{t('app_subtitle')}**")
        st.markdown("---")

        username = st.text_input(t("username"), placeholder="e.g., dr_sharma")
        password = st.text_input(t("password"), type="password")

        col_login, col_demo = st.columns(2)
        with col_login:
            if st.button(f"🔐 {t('login_button')}", use_container_width=True):
                is_valid, user_info = authenticate_user(username, password)
                if is_valid:
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    st.success(f"{t('welcome')}, {user_info['name']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {t('invalid_credentials')}")

        with col_demo:
            if st.button(f"📌 {t('demo_credentials')}", use_container_width=True):
                st.info("Contact your system administrator for login credentials.")

        st.markdown("---")
        st.markdown("""
        ### 🎯 Available Accounts
        - **dr_sharma** — Senior Physician
        - **dr_patel** — Cardiologist
        - **nurse_verma** — Registered Nurse

        *Contact your administrator to set or reset passwords.*
        """)

# ===================== CLINICAL STANDARDS SIDEBAR =====================
def show_standards_sidebar():
    """Display clinical standards in sidebar."""
    with st.sidebar:
        st.markdown("---")
        with st.expander("📋 Clinical Standards"):
            st.markdown("""
            ### Compliance Standards
            - **ABDM**: Ayushman Bharat Digital Mission compliance
            - **HIPAA**: Health Insurance Portability and Accountability Act
            - **GDPR**: General Data Protection Regulation
            - **ICD-10**: International Classification of Diseases
            - **HL7 FHIR**: Fast Healthcare Interoperability Resources
            
            ### Data Privacy
            - All patient data encrypted at rest
            - HIPAA/GDPR compliant
            - Role-based access control
            
            ### Documentation Standards
            - Structured SOAP notes (ABDM format)
            - ICD-10 diagnostic coding
            - Drug interaction checking
            - Prescription audit trail
            """)

# ===================== DOCTOR DASHBOARD PAGE =====================
def show_dashboard():
    """Medical-focused clinical dashboard."""
    name = st.session_state.user_info['name']
    st.title(f"🏥 {t('dashboard')} — {name}")

    db_stats = db_mgr.get_database_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(f"🏥 {t('total_patients')}", db_stats.get('total_patients', 0))
    with col2:
        st.metric(f"📋 {t('total_visits')}", db_stats.get('total_visits', 0))
    with col3:
        st.metric(f"📝 {t('total_soap_notes')}", db_stats.get('total_soap_notes', 0))
    with col4:
        st.metric(f"🎙️ {t('total_audio')}", db_stats.get('total_audio_recordings', 0))

    st.markdown("---")

    # Clinical alerts and important info
    col_alerts, col_workload = st.columns(2)
    
    with col_alerts:
        st.subheader("⚠️ Clinical Alerts")
        try:
            from database import Session as SessionClass, Patient
            session = SessionClass()
            patients = session.query(Patient).all()
            
            # Count patients with chronic conditions
            chronic_count = sum(1 for p in patients if p.chronic_conditions)
            high_risk_count = sum(1 for p in patients if len(p.chronic_conditions or []) >= 2)
            
            st.markdown(f"### 🔴 {t('high_risk')}")
            st.write(f"{t('high_risk')}: **{high_risk_count}**")

            st.markdown(f"### 🟡 {t('chronic_conditions')}")
            st.write(f"{t('chronic_conditions')}: **{chronic_count}**")
            
            session.close()
        except Exception as e:
            st.info("Load data to see alerts")
    
    with col_workload:
        st.subheader(f"📊 {t('clinical_workload')}")
        try:
            from database import Session as SessionClass, Visit
            from datetime import timedelta
            session = SessionClass()
            
            # Recent visits (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_visits = session.query(Visit).filter(Visit.visit_date >= week_ago).count()
            
            st.write(f"**This Week's Visits:** {recent_visits}")
            st.write(f"**Avg. Notes/Day:** {recent_visits // 7 if recent_visits > 0 else 0}")
            st.write(f"**Database Status:** ✅ Connected")
            
            session.close()
        except Exception as e:
            st.info("Database not yet initialized")
    
    st.markdown("---")
    
    # Recent visits and SOAP notes
    col_visits, col_notes = st.columns(2)
    
    with col_visits:
        st.subheader(f"📋 {t('recent_visits')}")
        try:
            from database import Session as SessionClass, Visit
            session = SessionClass()
            visits = session.query(Visit).order_by(Visit.visit_date.desc()).limit(5).all()
            
            if visits:
                for v in visits:
                    st.markdown(f"""
                    **Visit ID:** {v.visit_id}  
                    **Chief Complaint:** {v.chief_complaint}  
                    **Date:** {v.visit_date.strftime('%Y-%m-%d %H:%M') if v.visit_date else 'N/A'}
                    """)
                    st.divider()
            else:
                st.info("No visits yet")
            
            session.close()
        except Exception as e:
            st.info("No visit data available")
    
    with col_notes:
        st.subheader(f"📝 {t('recent_soap')}")
        try:
            from database import Session as SessionClass, SoapNote
            session = SessionClass()
            notes = session.query(SoapNote).order_by(SoapNote.created_at.desc()).limit(5).all()
            
            if notes:
                for n in notes:
                    st.markdown(f"""
                    **Note ID:** {n.note_id}  
                    **Assessment:** {n.assessment[:60]}...  
                    **Created:** {n.created_at.strftime('%Y-%m-%d %H:%M') if n.created_at else 'N/A'}
                    """)
                    st.divider()
            else:
                st.info("No SOAP notes yet")
            
            session.close()
        except Exception as e:
            st.info("No SOAP note data available")
    
    st.markdown("---")
    
    # Medical conditions summary
    st.subheader("🏥 Common Conditions in Patient Base")
    try:
        from database import Session as SessionClass, Patient
        session = SessionClass()
        patients = session.query(Patient).all()
        
        condition_count = {}
        for p in patients:
            for cond in p.chronic_conditions or []:
                condition_count[cond] = condition_count.get(cond, 0) + 1
        
        if condition_count:
            df_conditions = pd.DataFrame(list(condition_count.items()), columns=["Condition", "Count"])
            df_conditions = df_conditions.sort_values("Count", ascending=False)
            
            fig = px.bar(df_conditions, x="Count", y="Condition", orientation="h", 
                        title="Patient Conditions Distribution")
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No patient data yet - Create patients to see health trends")
        
        session.close()
    except Exception as e:
        st.info("Add patients to see medical trends")

# ===================== PATIENT DIRECTORY PAGE =====================
def show_patient_directory():
    """Patient directory and management (SQL Database)."""
    st.title(f"👥 {t('patients')}")

    col_search, col_add = st.columns([4, 1])
    with col_search:
        search_query = st.text_input(f"🔍 {t('search_placeholder')}")
    with col_add:
        if st.button(f"➕ {t('add_patient')}", use_container_width=True):
            st.session_state.show_add_patient = not st.session_state.get('show_add_patient', False)

    st.markdown("---")

    # Add patient form
    if st.session_state.get('show_add_patient', False):
        st.subheader(t("add_patient"))
        with st.form("add_patient_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(t("patient_name"), key="new_pat_name")
                age = st.number_input(t("patient_age"), min_value=0, max_value=150, key="new_pat_age")
                blood_group = st.selectbox(t("blood_group"), ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], key="new_pat_bg")
                phone = st.text_input(t("patient_phone"), key="new_pat_phone")
            
            with col2:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="new_pat_gender")
                email = st.text_input("Email", key="new_pat_email")
                chronic = st.multiselect("Chronic Conditions", ["Hypertension", "Diabetes", "Asthma", "Heart Disease", "None"], key="new_pat_chronic")
                allergies_text = st.text_input("Allergies (comma-separated)", key="new_pat_allergies")
            
            if st.form_submit_button("💾 Save Patient to Database"):
                if name and email:
                    allergies = [a.strip() for a in allergies_text.split(",")] if allergies_text else []
                    chronic_clean = [c for c in chronic if c != "None"]
                    
                    success, patient_id = db_mgr.create_patient(
                        name=name, age=age, gender=gender, phone=phone, email=email,
                        blood_group=blood_group, chronic_conditions=chronic_clean,
                        allergies=allergies
                    )
                    if success:
                        st.success(f"✅ Patient created with ID: {patient_id}")
                        st.session_state.show_add_patient = False
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create patient")
                else:
                    st.warning("Please enter patient name and email")
    
    st.markdown("---")
    
    # Get patients from SQL database
    if search_query:
        df_patients = db_mgr.search_patients(search_query)
    else:
        df_patients = db_mgr.get_all_patients_df()
    
    if not df_patients.empty:
        st.dataframe(df_patients, width='stretch')
        
        # Patient detail view
        st.markdown("---")
        selected_patient_id = st.selectbox(
            "View patient details:",
            df_patients["Patient ID"].tolist(),
            format_func=lambda x: f"{df_patients[df_patients['Patient ID']==x]['Name'].values[0]} ({x})"
        )
        
        if selected_patient_id:
            patient = db_mgr.get_patient_by_id(selected_patient_id)
            if patient:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"### {patient['name']}")
                    st.write(f"**ID:** {patient['patient_id']}")
                    st.write(f"**Age:** {patient['age']} years")
                    st.write(f"**Gender:** {patient['gender']}")
                
                with col2:
                    st.write(f"**Blood Group:** {patient['blood_group']}")
                    st.write(f"**Phone:** {patient['phone']}")
                    st.write(f"**Email:** {patient['email']}")
                
                with col3:
                    st.write(f"**Total Visits:** {patient['visit_count']}")
                    st.write(f"**Last Visit:** {patient['last_visit'] or 'N/A'}")
                
                st.markdown("**Chronic Conditions:**")
                for condition in patient['chronic_conditions']:
                    st.write(f"• {condition}")
                
                st.markdown("**Allergies:**")
                for allergy in patient['allergies']:
                    st.write(f"⚠️ {allergy}")
                
                # Show patient's visits and SOAP notes
                st.markdown("---")
                st.subheader(f"📋 Visits & SOAP Notes for {patient['name']}")
                
                visits_df = db_mgr.get_patient_visits_df(selected_patient_id)
                if not visits_df.empty:
                    st.write("**Recent Visits:**")
                    st.dataframe(visits_df, width='stretch')
                else:
                    st.info("No visits recorded yet for this patient")
                
                # Prescriptions
                st.markdown("---")
                st.subheader(f"💊 Prescriptions for {patient['name']}")
                prescriptions_df = db_mgr.get_patient_prescriptions_df(selected_patient_id)
                if not prescriptions_df.empty:
                    st.dataframe(prescriptions_df, width='stretch')
                else:
                    st.info("No prescriptions on file")
    else:
        st.info("📭 No patients found in database. Click '➕ Add Patient' to create one.")

# ===================== MEDICINE DIRECTORY PAGE =====================
def show_medicine_directory():
    """Medicine directory powered by the full A-Z India medicines CSV."""
    st.title("💊 Medicine Directory")

    # Source banner
    st.success(f"📦 {medicine_mgr.source_label}")

    col_search, col_filter = st.columns([3, 1])

    with col_search:
        search_query = st.text_input("🔍 Search by name, composition, category, or manufacturer")

    with col_filter:
        categories = ["All"] + medicine_mgr.get_unique_categories()
        category_filter = st.selectbox("Filter by category", categories)

    # Show only active (non-discontinued) by default
    show_discontinued = st.checkbox("Include discontinued medicines", value=False)

    st.markdown("---")

    # ── Filter medicines ──────────────────────────────────────────────────
    if search_query:
        medicines = medicine_mgr.search_medicines(search_query)
    elif category_filter != "All":
        medicines = medicine_mgr.get_medicines_by_category(category_filter)
    else:
        medicines = medicine_mgr.get_all_medicines()

    if not show_discontinued:
        medicines = [m for m in medicines if not m.get("is_discontinued")]

    if not medicines:
        st.info("No medicines found matching your filters.")
        return

    st.write(f"**Showing {len(medicines):,} medicines**")

    # ── Paginated table view ──────────────────────────────────────────────
    PAGE_SIZE = 50
    total_pages = max(1, (len(medicines) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    start = (page - 1) * PAGE_SIZE
    page_meds = medicines[start: start + PAGE_SIZE]

    df = medicine_mgr.get_dataframe(page_meds)
    st.dataframe(df, use_container_width=True, height=500)
    st.caption(f"Page {page} of {total_pages}  •  {len(medicines):,} results total")

    # ── Detail view ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔎 Medicine Detail")
    med_names = [m["drug_name"] for m in page_meds]
    selected_name = st.selectbox("Select a medicine for full details:", ["— select —"] + med_names)

    if selected_name and selected_name != "— select —":
        med = next((m for m in page_meds if m["drug_name"] == selected_name), None)
        if med:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Category", med.get("category", ""))
                st.metric("Dosage Form", med.get("dosage_form", ""))
            with c2:
                st.metric("Manufacturer", med.get("manufacturer", "") or "N/A")
                price = med.get("price")
                st.metric("Price", f"₹{price:.2f}" if price else "N/A")
            with c3:
                st.metric("Pack Size", med.get("pack_size", "") or "N/A")
                st.metric("Discontinued", "Yes" if med.get("is_discontinued") else "No")

            comp = med.get("composition", "")
            if comp:
                st.markdown(f"**Composition:** {comp}")
            side = med.get("side_effects", [])
            if side:
                st.markdown("**Side Effects:** " + ", ".join(side))

# ===================== SCRIBER AI PAGE =====================
def show_scriber_ai():
    """Enhanced Scriber AI with unlimited recording, patient linking, and database saving."""
    st.title(t("scriber_ai"))
    
    # ===== Database stats =====
    db_stats = db_mgr.get_database_stats()
    st.markdown(f"""
    ### {t('database')}
    - **{t('total_patients')}:** {db_stats.get('total_patients', 0)}
    - **{t('total_visits')}:** {db_stats.get('total_visits', 0)}
    - **{t('total_soap_notes')}:** {db_stats.get('total_soap_notes', 0)}
    - **{t('total_records')}:** {db_stats.get('total_audio_recordings', 0)} audio recordings
    """)
    
    st.markdown("---")
    
    # ===== PATIENT SELECTION =====
    st.subheader(f"👥 {t('patient_selection')}")
    
    # Get all patients from database
    patients_df = db_mgr.get_all_patients_df()
    
    col_sel, col_new = st.columns([2, 1])
    
    with col_sel:
        if not patients_df.empty:
            patient_options = {row['Patient ID']: f"{row['Name']} ({row['Patient ID']})" 
                              for _, row in patients_df.iterrows()}
            selected_patient_id = st.selectbox(
                t("select_patient"),
                list(patient_options.keys()),
                format_func=lambda x: patient_options.get(x, "Select patient")
            )
        else:
            selected_patient_id = None
            st.warning("⚠️ No patients in database. Create a patient using the button on the left.")
    
    with col_new:
        st.write("")  # Spacing
        st.write("")
        if st.button("➕ Quick Add"):
            st.session_state.show_quick_patient = not st.session_state.get('show_quick_patient', False)
    
    # Quick add patient
    if st.session_state.get('show_quick_patient', False):
        with st.expander("Add Patient Quickly", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                quick_name = st.text_input("Name", key="quick_name")
                quick_age = st.number_input("Age", 1, 150, 30, key="quick_age")
                quick_gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="quick_gender")
            with col2:
                quick_phone = st.text_input("Phone", key="quick_phone")
                quick_email = st.text_input("Email", key="quick_email")
                quick_bg = st.selectbox("Blood Group", ["A+", "B+", "O+", "AB+"], key="quick_bg")
            
            if st.button("Save & Select"):
                if quick_name and quick_email:
                    success, new_patient_id = db_mgr.create_patient(
                        name=quick_name, age=quick_age, gender=quick_gender,
                        phone=quick_phone, email=quick_email, blood_group=quick_bg
                    )
                    if success:
                        st.success(f"✅ Patient {quick_name} created!")
                        st.session_state.show_quick_patient = False
                        st.rerun()
    
    if not selected_patient_id:
        st.warning("Please select or create a patient first")
        return
    
    # Show selected patient details
    selected_patient = db_mgr.get_patient_by_id(selected_patient_id)
    if selected_patient:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Patient", selected_patient['name'])
        with col2:
            st.metric("Age", f"{selected_patient['age']} years")
        with col3:
            st.metric("Blood Group", selected_patient['blood_group'])
    
    st.markdown("---")
    
    # ===== INPUT METHOD SELECTION =====
    input_method = st.radio(
        "How would you like to input clinical data?",
        ["📝 Type Transcript", "🎙️ Record Audio (Unlimited)", "📋 Template"]
    )
    
    # ===== METHOD 1: TYPE TRANSCRIPT =====
    if input_method == "📝 Type Transcript":
        st.subheader(t("chief_complaint"))
        chief_complaint = st.text_input("Chief Complaint", placeholder="Fever, cough, etc.")
        transcript = st.text_area(
            "Clinical Encounter Transcript:",
            height=250,
            placeholder="Doctor: How are you feeling?\nPatient: I have a fever...",
        )
        
        if st.button(t("processing"), type="primary"):
            if transcript and chief_complaint and selected_patient_id:
                # Create visit in database
                with st.spinner("Creating visit in database..."):
                    success, visit_id = db_mgr.create_visit(
                        patient_id=selected_patient_id,
                        chief_complaint=chief_complaint
                    )
                
                if success:
                    # Generate SOAP
                    with st.spinner(t("generating_soap")):
                        soap_success, soap_json = scribe.generate_soap_with_llm(transcript)
                    
                    if soap_success:
                        st.success(t("soap_generated"))
                        
                        # Display SOAP in readable format
                        st.markdown("---")
                        st.subheader("📄 SOAP Note")
                        display_soap_note(soap_json)
                        st.markdown("---")
                        
                        # Save SOAP to database
                        with st.spinner("Saving SOAP note to database..."):
                            save_success, note_id = db_mgr.save_soap_from_visit(visit_id, soap_json)

                        if save_success:
                            st.success(f"✅ SOAP Note saved! Note ID: {note_id}")

                            # Download as plain-text report
                            patient_name = selected_patient.get('name', '') if selected_patient else ''
                            soap_txt = _format_soap_as_text(soap_json, patient_name, visit_id)
                            st.download_button(
                                label="📥 Download SOAP Note (.txt)",
                                data=soap_txt,
                                file_name=f"soap_{note_id}.txt",
                                mime="text/plain"
                            )
                    else:
                        st.error(f"Failed to generate SOAP: {soap_json}")
                else:
                    st.error("Failed to create visit")
            else:
                st.warning("Please fill in all fields and select a patient")
    
    # ===== METHOD 2: RECORD AUDIO =====
    elif input_method == "🎙️ Record Audio (Unlimited)":
        st.subheader(f"{t('record_audio')} - {t('unlimited')} Duration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                t("filter_type"),
                ["bandpass", "lowpass", "highpass", "noisereduce"]
            )
        
        with col2:
            audio_lang = st.selectbox(
                t("language"),
                ["en", "es", "fr", "de", "hi", "zh", "pt", "ar"]
            )
        
        with col3:
            st.metric(t("recording_duration"), f"{st.session_state.recording_duration:.1f}s" if st.session_state.recording_active else "Ready")
        
        st.markdown("---")
        
        chief_complaint_audio = st.text_input("Chief Complaint", placeholder="Fever, cough, etc.")
        
        col_start, col_stop = st.columns(2)
        
        with col_start:
            if st.button(f"🎤 {t('start_recording')}", type="primary", key="start_rec"):
                st.session_state.recording_active = True
                success = scribe.start_unlimited_recording()
                if success:
                    st.success(t("recording_started"))
                else:
                    st.error("Microphone not detected")
        
        with col_stop:
            if st.button(f"⏹️ {t('stop_recording')}", type="secondary", key="stop_rec"):
                if st.session_state.recording_active:
                    success, file_path, duration = scribe.stop_unlimited_recording("clinical_audio.wav")
                    st.session_state.recording_active = False
                    
                    if success:
                        st.session_state.recording_duration = duration
                        st.success(f"{t('recording_stopped')}: {duration:.2f}s")
                        
                        # Process audio
                        st.markdown("---")
                        with st.spinner(f"Applying {filter_type} filter..."):
                            success, metadata = scribe.process_recording(file_path, filter_type=filter_type)
                        
                        if success:
                            st.success(f"✅ Audio processed successfully")
                            st.info(f"Noise Level: {metadata.get('noise_level', 0):.2f} | Filters: {', '.join(metadata.get('filters_applied', []))}")
                            
                            # Audio comparison
                            col_org, col_filt = st.columns(2)
                            with col_org:
                                st.markdown("**Original Audio**")
                                st.audio(file_path)
                            
                            if 'processed_file' in metadata:
                                with col_filt:
                                    st.markdown("**Filtered Audio**")
                                    st.audio(metadata['processed_file'])
                            
                            audio_file_to_transcribe = metadata.get('processed_file', file_path)
                            
                            # Transcribe
                            st.markdown("---")
                            with st.spinner(f"{t('transcribing')}..."):
                                trans_success, transcript, confidence = scribe.transcribe_audio(
                                    audio_file_to_transcribe,
                                    language=audio_lang
                                )
                            
                            if trans_success:
                                st.success(f"✅ Transcription complete (Confidence: {confidence:.2f})")
                                st.markdown("**Transcript:**")
                                st.text_area("Transcript", value=transcript, height=150, disabled=True, label_visibility="collapsed")
                                
                                # Generate SOAP
                                st.markdown("---")
                                with st.spinner(f"{t('generating_soap')}..."):
                                    soap_success, soap_json = scribe.generate_soap_with_llm(transcript)
                                
                                if soap_success:
                                    st.success(t("soap_generated"))
                                    
                                    # Display SOAP in readable format
                                    st.markdown("---")
                                    st.subheader("📄 SOAP Note")
                                    display_soap_note(soap_json)
                                    st.markdown("---")
                                    
                                    # AUTO-SAVE to database
                                    with st.spinner("Auto-saving to database..."):
                                        # Create visit and save automatically
                                        v_success, visit_id = db_mgr.create_visit(
                                            patient_id=selected_patient_id,
                                            chief_complaint=chief_complaint_audio or "Audio consultation"
                                        )
                                        
                                        if v_success:
                                            # Save SOAP
                                            soap_saved, note_id = db_mgr.save_soap_from_visit(visit_id, soap_json)
                                            
                                            if soap_saved:
                                                # Save audio metadata
                                                scribe.save_audio_recording(
                                                    visit_id=visit_id,
                                                    file_path=audio_file_to_transcribe,
                                                    transcript=transcript,
                                                    noise_level=metadata.get('noise_level', 0),
                                                    filter_type=filter_type
                                                )
                                                
                                                st.success(f"✅ Auto-saved! Visit ID: {visit_id} | Note ID: {note_id}")

                                                # Download as plain-text report
                                                p_name = selected_patient.get('name', '') if selected_patient else ''
                                                soap_txt = _format_soap_as_text(soap_json, p_name, visit_id)
                                                st.download_button(
                                                    label="📥 Download SOAP Note (.txt)",
                                                    data=soap_txt,
                                                    file_name=f"soap_{note_id}.txt",
                                                    mime="text/plain"
                                                )
                                            else:
                                                st.error("Failed to save SOAP note")
                                        else:
                                            st.error("Failed to create visit")
                                else:
                                    st.error(f"Failed to generate SOAP: {soap_json}")
                            else:
                                st.error(f"Transcription failed: {transcript}")
                        else:
                            st.error("Audio processing failed")
    
    # ===== METHOD 3: TEMPLATE =====
    elif input_method == "📋 Template":
        st.subheader("SOAP Note Template")
        
        with st.form("soap_template_form"):
            chief_complaint = st.text_input("Chief Complaint")
            
            col1, col2 = st.columns(2)
            with col1:
                subjective = st.text_area("Subjective (Chief Complaint & History)", height=100)
                assessment = st.text_area("Assessment (Diagnosis)", height=100)
            
            with col2:
                objective = st.text_area("Objective (Findings & Vitals)", height=100)
                plan = st.text_area("Plan (Treatment & Medications)", height=100)
            
            if st.form_submit_button("💾 Save SOAP Note", type="primary"):
                # Create visit
                with st.spinner("Creating visit..."):
                    v_success, visit_id = db_mgr.create_visit(
                        patient_id=selected_patient_id,
                        chief_complaint=chief_complaint
                    )
                
                if v_success:
                    # Save SOAP
                    soap_data = {
                        "subjective": subjective,
                        "objective": objective,
                        "assessment": assessment,
                        "plan": plan
                    }
                    
                    with st.spinner("Saving SOAP note..."):
                        soap_saved, note_id = db_mgr.save_soap_from_visit(visit_id, soap_data)
                    
                    if soap_saved:
                        st.success(f"✅ SOAP Note saved! Visit ID: {visit_id} | Note ID: {note_id}")

                        # Download as plain-text report
                        p_name = selected_patient.get('name', '') if selected_patient else ''
                        soap_txt = _format_soap_as_text(soap_data, p_name, visit_id)
                        st.download_button(
                            label="📥 Download SOAP Note (.txt)",
                            data=soap_txt,
                            file_name=f"soap_{note_id}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error("Failed to save SOAP note")
                else:
                    st.error("Failed to create visit")

# ===================== ANALYTICS PAGE =====================
def show_analytics():
    """Analytics and reporting — 100% driven by real database data."""
    st.title("📊 Analytics & Reports")

    from database import Session as DBSession, Patient, Visit, SoapNote, Prescription
    from collections import Counter
    from datetime import timedelta

    session = DBSession()
    try:
        total_patients = session.query(Patient).count()
        total_visits   = session.query(Visit).count()
        total_soaps    = session.query(SoapNote).count()
        total_presc    = session.query(Prescription).count()
        week_ago       = datetime.now() - timedelta(days=7)
        visits_7d      = session.query(Visit).filter(Visit.visit_date >= week_ago).count()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏥 Total Patients", total_patients)
        with col2:
            st.metric("📋 Total Visits", total_visits)
        with col3:
            st.metric("📝 SOAP Notes", total_soaps)
        with col4:
            st.metric("📅 Visits (7 days)", visits_7d)

        st.markdown("---")

        if total_visits == 0:
            st.info("📭 No clinical data recorded yet. Create a visit in **Scriber AI** to see analytics here.")
            return

        tab1, tab2, tab3, tab4 = st.tabs(["🩺 Diagnoses", "💊 Medications", "🏥 Disease Distribution", "🏷️ ICD-10 Codes"])

        # ── Tab 1: Top diagnoses from assessment field ─────────────────────
        with tab1:
            st.subheader("Top Diagnoses (from SOAP Assessments)")
            notes = session.query(SoapNote).all()
            diag_counter = Counter()
            for note in notes:
                raw = (note.assessment or "").strip()
                if raw:
                    # Split on common delimiters
                    for part in re.split(r'[,;\n]+', raw):
                        part = part.strip()
                        if 3 < len(part) < 80:
                            diag_counter[part] += 1
            if diag_counter:
                df_diag = pd.DataFrame(diag_counter.most_common(15), columns=["Diagnosis", "Count"])
                fig = px.bar(df_diag, x="Count", y="Diagnosis", orientation="h",
                             title="Most Frequent Diagnoses", color="Count",
                             color_continuous_scale="Blues")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_diag, use_container_width=True)
            else:
                st.info("No assessment data yet. Generate SOAP notes to see diagnosis trends.")

        # ── Tab 2: Top medications from Prescription table ─────────────────
        with tab2:
            st.subheader("Top Prescribed Medications")
            prescriptions = session.query(Prescription).all()
            med_counter = Counter()
            for p in prescriptions:
                name = (p.medicine_name or "").strip()
                if name:
                    med_counter[name] += 1
            if med_counter:
                df_meds = pd.DataFrame(med_counter.most_common(15), columns=["Medication", "Count"])
                fig = px.bar(df_meds, x="Count", y="Medication", orientation="h",
                             title="Most Prescribed Medications", color="Count",
                             color_continuous_scale="Greens")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_meds, use_container_width=True)
            else:
                st.info("No prescription data yet. Add prescriptions in the Patients tab.")

        # ── Tab 3: Disease distribution from Patient chronic_conditions ────
        with tab3:
            st.subheader("Patient Disease Distribution")
            disease_map = {
                "Cardiology":      ["heart", "cardiac", "hypertension", "atrial", "coronary"],
                "Endocrinology":   ["diabetes", "thyroid", "metabolic"],
                "Pulmonology":     ["asthma", "copd", "lung", "pneumonia", "bronchitis"],
                "Nephrology":      ["kidney", "renal"],
                "Rheumatology":    ["arthritis", "lupus"],
                "Gastroenterology":["liver", "fatty", "digestive"],
                "Neurology":       ["migraine", "neuropathy", "epilepsy"],
                "Psychiatry":      ["depression", "anxiety", "mental"],
            }
            patients_all = session.query(Patient).all()
            dept_counter = Counter()
            for p in patients_all:
                for cond in (p.chronic_conditions or []):
                    matched = "General Medicine"
                    cl = cond.lower()
                    for dept, kws in disease_map.items():
                        if any(kw in cl for kw in kws):
                            matched = dept
                            break
                    dept_counter[matched] += 1
            if dept_counter:
                df_dist = pd.DataFrame(dept_counter.most_common(), columns=["Department", "Patients"])
                fig = px.pie(df_dist, values="Patients", names="Department",
                             title="Patient Distribution by Department")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_dist, use_container_width=True)
            else:
                st.info("No chronic condition data yet. Add patients with conditions.")

        # ── Tab 4: ICD-10 codes from SoapNote icd10_codes JSON ────────────
        with tab4:
            st.subheader("ICD-10 Code Usage")
            icd_counter = Counter()
            for note in notes:
                codes = note.icd10_codes or []
                for c in codes:
                    if isinstance(c, dict):
                        code = c.get("icd10_code", "")
                        cond = c.get("condition", "")
                    else:
                        code, cond = str(c), str(c)
                    if code:
                        icd_counter[f"{code} — {cond}"] += 1
            if icd_counter:
                df_icd = pd.DataFrame(icd_counter.most_common(20), columns=["ICD-10 Code", "Count"])
                fig = px.bar(df_icd, x="Count", y="ICD-10 Code", orientation="h",
                             title="Most Used ICD-10 Codes", color="Count",
                             color_continuous_scale="Reds")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_icd, use_container_width=True)
            else:
                st.info("No ICD-10 codes extracted yet. Generate SOAP notes to see ICD-10 usage.")

    finally:
        session.close()

# ===================== ADD-ONS PAGE =====================
def show_addons():
    """Feature add-ons."""
    st.title("🎯 Advanced Features & Add-ons")
    
    tab1, tab2, tab3 = st.tabs(["🚨 Drug Interactions", "📚 Patient Education", "🔍 ICD-10 Auto-Mapper"])
    
    with tab1:
        st.subheader("Smart-Risk Alerts: Drug-Drug Interaction Checker")
        
        st.markdown("Check for potential drug interactions in the current patient's regimen.")
        
        # Select drugs to check
        all_medicines = medicine_mgr.get_all_medicines()[:50]
        drug_names = [m['drug_name'] for m in all_medicines]
        
        selected_drugs = st.multiselect(
            "Select drugs to check for interactions:",
            drug_names
        )
        
        if st.button("⚠️ Check Interactions"):
            if selected_drugs:
                # Map drug names to IDs
                selected_ids = []
                for drug_name in selected_drugs:
                    for med in all_medicines:
                        if med['drug_name'] == drug_name:
                            selected_ids.append(med['id'])
                            break
                
                interactions = medicine_mgr.check_drug_interactions(selected_ids)
                
                if interactions:
                    st.markdown("<div class='warning-box'>⚠️ Potential Drug Interactions Detected</div>", unsafe_allow_html=True)
                    for interaction in interactions:
                        st.warning(f"**{interaction['drug1']}** + **{interaction['drug2']}**")
                        st.write(f"Risk Level: **{interaction['risk_level']}**")
                        st.write(f"Recommendation: {interaction['recommendation']}")
                else:
                    st.markdown("<div class='success-box'>✅ No significant interactions detected</div>", unsafe_allow_html=True)
            else:
                st.info("Select at least 2 drugs to check interactions")
    
    with tab2:
        st.subheader("Patient Education Generator")
        
        clinical_plan = st.text_area(
            "Enter the clinical plan from SOAP note:",
            placeholder="Rest for 3 days. Take Amoxicillin 500mg TDS for 5 days. Follow-up in 1 week.",
            height=150
        )
        
        language = st.selectbox("Select language:", ["English", "Hindi", "Tamil", "Telugu"])
        
        if st.button("📚 Generate Patient Instructions"):
            if clinical_plan:
                education = generate_patient_education(clinical_plan, language.lower())
                st.markdown("### 📋 Patient Instructions to Take Home:")
                st.info(education)
            else:
                st.warning("Please enter a clinical plan")
    
    with tab3:
        st.subheader("Auto-ICD-10-Coder")
        
        st.markdown("Automatically map clinical assessment to ICD-10 codes")
        
        assessment = st.text_area(
            "Enter clinical assessment:",
            placeholder="Patient with hypertension and Type 2 Diabetes presents with fever",
            height=150
        )
        
        if st.button("🔍 Find ICD-10 Codes"):
            if assessment:
                codes = scribe._extract_icd10_codes(assessment)
                if codes:
                    st.success("✅ ICD-10 codes found:")
                    df_codes = pd.DataFrame(codes)
                    st.dataframe(df_codes, width='stretch')
                else:
                    st.info("No recognized conditions in the assessment")
            else:
                st.warning("Please enter an assessment")

# ===================== DATABASE MANAGEMENT PAGE =====================
def show_database_management():
    """Easy access to view and manage database records."""
    st.title("🗄️ Database Management & Records")
    
    st.markdown("**Easy access to all clinical records stored in the SQL database.**")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Patients", "Visits", "SOAP Notes", "Audio Records", "Prescriptions"])
    
    # ===== PATIENTS TAB =====
    with tab1:
        st.subheader("Patient Records")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("Search patients", key="db_search_patient")
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        if search:
            patients_df = db_mgr.search_patients(search)
        else:
            patients_df = db_mgr.get_all_patients_df()
        
        if not patients_df.empty:
            st.dataframe(patients_df, width='stretch', height=400)
            st.write(f"**Total: {len(patients_df)} patients**")
        else:
            st.info("No patient records found")
    
    # ===== VISITS TAB =====
    with tab2:
        st.subheader("Visit Records")
        
        # Get all visits
        try:
            from database import Session as SessionClass
            session = SessionClass()
            from database import Visit
            visits = session.query(Visit).all()
            session.close()
            
            if visits:
                visits_data = []
                for v in visits:
                    visits_data.append({
                        "Visit ID": v.visit_id,
                        "Patient ID": v.patient_id,
                        "Date": v.visit_date.strftime("%Y-%m-%d %H:%M") if v.visit_date else "N/A",
                        "Chief Complaint": v.chief_complaint,
                        "Type": v.visit_type or "OP",
                        "Duration (s)": f"{v.duration:.1f}" if v.duration else "N/A"
                    })
                
                df_visits = pd.DataFrame(visits_data)
                st.dataframe(df_visits, width='stretch', height=400)
                st.write(f"**Total: {len(visits_data)} visits**")
            else:
                st.info("No visit records found")
        except Exception as e:
            st.error(f"Error loading visits: {e}")
    
    # ===== SOAP NOTES TAB =====
    with tab3:
        st.subheader("SOAP Note Records")
        
        try:
            from database import SoapNote
            session = SessionClass()
            soap_notes = session.query(SoapNote).all()
            session.close()
            
            if soap_notes:
                soap_data = []
                for s in soap_notes:
                    soap_data.append({
                        "Note ID": s.note_id,
                        "Visit ID": s.visit_id,
                        "Created": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "N/A",
                        "Assessment": (s.assessment[:60] + "...") if len(s.assessment or "") > 60 else s.assessment,
                        "ICD-10": ", ".join(s.icd10_codes or [])[:50]
                    })
                
                df_soap = pd.DataFrame(soap_data)
                st.dataframe(df_soap, width='stretch', height=400)
                st.write(f"**Total: {len(soap_data)} SOAP notes**")
            else:
                st.info("No SOAP note records found")
        except Exception as e:
            st.error(f"Error loading SOAP notes: {e}")
    
    # ===== AUDIO RECORDINGS TAB =====
    with tab4:
        st.subheader("Audio Recording Records")
        
        try:
            from database import AudioRecording
            session = SessionClass()
            recordings = session.query(AudioRecording).all()
            session.close()
            
            if recordings:
                audio_data = []
                for a in recordings:
                    audio_data.append({
                        "Audio ID": a.audio_id,
                        "Visit ID": a.visit_id,
                        "Duration (s)": f"{a.duration:.1f}" if a.duration else "N/A",
                        "Language": a.language or "en",
                        "Noise Level": f"{a.noise_level:.2f}" if a.noise_level else "N/A",
                        "Filter Applied": a.filter_type or "None",
                        "Confidence": f"{a.transcription_confidence:.2f}" if a.transcription_confidence else "N/A",
                        "Created": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "N/A"
                    })
                
                df_audio = pd.DataFrame(audio_data)
                st.dataframe(df_audio, width='stretch', height=400)
                st.write(f"**Total: {len(audio_data)} audio recordings**")
            else:
                st.info("No audio recording records found")
        except Exception as e:
            st.error(f"Error loading audio records: {e}")
    
    # ===== PRESCRIPTIONS TAB =====
    with tab5:
        st.subheader("Prescription Records")
        
        try:
            from database import Prescription
            session = SessionClass()
            prescriptions = session.query(Prescription).all()
            session.close()
            
            if prescriptions:
                presc_data = []
                for p in prescriptions:
                    presc_data.append({
                        "Prescription ID": p.prescription_id,
                        "Patient ID": p.patient_id,
                        "Medicine": p.medicine_name,
                        "Dosage": p.dosage,
                        "Frequency": p.frequency,
                        "Duration": p.duration,
                        "Route": p.route or "Oral",
                        "Date": p.date_prescribed.strftime("%Y-%m-%d") if p.date_prescribed else "N/A"
                    })
                
                df_presc = pd.DataFrame(presc_data)
                st.dataframe(df_presc, width='stretch', height=400)
                st.write(f"**Total: {len(presc_data)} prescriptions**")
            else:
                st.info("No prescription records found")
        except Exception as e:
            st.error(f"Error loading prescriptions: {e}")
    
    st.markdown("---")
    st.info("💡 **Tip:** Click on 'Patients' page to add new patients and manage their detailed records.")

# ===================== SETTINGS PAGE =====================
def show_settings():
    """User settings and preferences."""
    st.title("⚙️ Settings & Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Profile")
        st.write(f"**Name:** {st.session_state.user_info['name']}")
        st.write(f"**Role:** {st.session_state.user_info['role']}")
        st.write(f"**Department:** {st.session_state.user_info['department']}")
        st.write(f"**Clinic ID:** {st.session_state.user_info['clinic_id']}")
    
    with col2:
        st.subheader("🔔 Notifications")
        enable_notifications = st.checkbox("Enable drug interaction alerts", value=True)
        enable_reminders = st.checkbox("Enable follow-up reminders", value=True)
        alert_level = st.selectbox("Alert sensitivity", ["Low", "Medium", "High"])
    
    st.markdown("---")
    
    st.subheader("📋 Documentation Preferences")
    default_template = st.selectbox("Default SOAP template", ["Standard", "Minimal", "Extended"])
    auto_icd10 = st.checkbox("Auto-suggest ICD-10 codes", value=True)
    abdm_mode = st.checkbox("Strict ABDM compliance mode", value=True)
    
    st.markdown("---")
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully")
    
    if st.button("🚪 Logout", type="secondary"):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.rerun()

# ===================== MAIN APP LOGIC =====================
def main():
    # Show login if not authenticated
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"### 👋 {t('welcome')}, {st.session_state.user_info['name']}")
        st.markdown(f"**{st.session_state.user_info['role']}**")
        st.markdown("---")

        # ── Language selector (top of sidebar, prominent) ──────────────────
        lang_list = get_language_list()
        lang_keys = list(lang_list.keys())
        current_idx = lang_keys.index(st.session_state.language) if st.session_state.language in lang_keys else 0

        st.markdown("### � भाषा / Language")
        selected_lang = st.selectbox(
            "Select language",
            lang_keys,
            format_func=lambda x: lang_list[x],
            index=current_idx,
            key="global_lang_selector",
            label_visibility="collapsed",
        )

        # When language changes, pre-load all translations in the background
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            if selected_lang not in st.session_state.preloaded_langs:
                with st.spinner("Loading translations…"):
                    preload_language(selected_lang)
                st.session_state.preloaded_langs.add(selected_lang)
            st.rerun()
        elif selected_lang not in st.session_state.preloaded_langs:
            # First run for this lang — preload silently
            preload_language(selected_lang)
            st.session_state.preloaded_langs.add(selected_lang)

        st.markdown("---")

        # ── Navigation ────────────────────────────────────────────────────
        nav_options = [
            ("📊", t("dashboard")),
            ("👥", t("patients")),
            ("💊", t("medicines")),
            ("🎙️", t("scriber_ai")),
            ("📈", t("analytics")),
            ("🗄️", t("database_mgmt")),
            ("🎯", t("addons")),
            ("⚙️", t("settings")),
        ]
        nav_labels = [f"{icon} {label}" for icon, label in nav_options]

        page = st.radio(
            t("settings"),
            nav_labels,
            label_visibility="collapsed",
        )

    # Show clinical standards
    show_standards_sidebar()

    # ── Route to pages ────────────────────────────────────────────────────────
    page_idx = nav_labels.index(page) if page in nav_labels else 0
    if page_idx == 0:
        show_dashboard()
    elif page_idx == 1:
        show_patient_directory()
    elif page_idx == 2:
        show_medicine_directory()
    elif page_idx == 3:
        show_scriber_ai()
    elif page_idx == 4:
        show_analytics()
    elif page_idx == 5:
        show_database_management()
    elif page_idx == 6:
        show_addons()
    elif page_idx == 7:
        show_settings()

if __name__ == "__main__":
    main()
