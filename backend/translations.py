"""
Multilingual translation engine for ScribeAI Clinical OS.
Uses deep-translator (Google Translate) to support all 22 official Indian languages
plus English. Translations are disk-cached so the API is not hit on every render.
"""

import json
import os
from pathlib import Path
from typing import Optional

# ─── All supported UI strings in English (single source of truth) ─────────────

BASE_STRINGS: dict = {
    # App-level
    "app_title":            "ScribeAI Clinical OS",
    "app_subtitle":         "Ambient Clinical Voice Documentation Platform",
    "login":                "Login",
    "logout":               "Logout",
    "demo_credentials":     "Demo Credentials",
    "username":             "Username",
    "password":             "Password",
    "login_button":         "Login",
    "welcome":              "Welcome",
    "invalid_credentials":  "Invalid username or password",

    # Navigation
    "dashboard":            "Dashboard",
    "patients":             "Patients",
    "medicines":            "Medicines",
    "scriber_ai":           "Scriber AI",
    "analytics":            "Analytics",
    "addons":               "Advanced Features",
    "database_mgmt":        "Database",
    "settings":             "Settings",
    "language":             "Language",
    "select_language":      "Select Language",

    # Dashboard
    "total_patients":       "Total Patients",
    "total_visits":         "Total Visits",
    "total_soap_notes":     "Total SOAP Notes",
    "total_records":        "Total Records",
    "total_audio":          "Audio Recordings",
    "clinical_alerts":      "Clinical Alerts",
    "clinical_workload":    "Clinical Workload",
    "recent_visits":        "Recent Visits",
    "recent_soap":          "Recent SOAP Notes",
    "high_risk":            "High Risk Patients",
    "chronic_conditions":   "Chronic Conditions",
    "database":             "Database Status",

    # Patient management
    "patient_selection":    "Patient Selection",
    "select_patient":       "Select Patient",
    "add_patient":          "Add Patient",
    "patient_name":         "Patient Name",
    "patient_age":          "Age",
    "patient_gender":       "Gender",
    "patient_phone":        "Phone",
    "patient_email":        "Email",
    "blood_group":          "Blood Group",
    "allergies":            "Allergies",
    "create_patient":       "Create New Patient",
    "patient_created":      "Patient created successfully",
    "patient_updated":      "Patient information updated",
    "male":                 "Male",
    "female":               "Female",
    "other":                "Other",

    # Scriber AI
    "record_audio":         "Record Audio",
    "start_recording":      "Start Recording",
    "stop_recording":       "Stop Recording",
    "recording_duration":   "Recording Duration",
    "transcribing":         "Transcribing audio with Whisper...",
    "generating_soap":      "Generating SOAP note with AI...",
    "processing":           "Generate SOAP Note",
    "unlimited":            "Unlimited",
    "filter_type":          "Audio Filter Type",
    "noise_level":          "Noise Level",
    "save":                 "Save Note",
    "chief_complaint":      "Chief Complaint",
    "type_transcript":      "Type Transcript",
    "template":             "Use Template",
    "quick_add":            "Quick Add Patient",

    # SOAP note sections
    "soap_note":            "SOAP Note",
    "subjective":           "Subjective (Chief Complaint & History)",
    "objective":            "Objective (Vital Signs & Findings)",
    "assessment":           "Assessment (Diagnosis)",
    "plan":                 "Plan (Treatment & Follow-up)",
    "icd10_codes":          "ICD-10 Diagnostic Codes",
    "download_soap":        "Download SOAP Note",

    # Vital signs
    "vital_signs":          "Vital Signs",
    "temperature":          "Temperature (°C)",
    "blood_pressure":       "Blood Pressure (mmHg)",
    "heart_rate":           "Heart Rate (bpm)",
    "oxygen_saturation":    "Oxygen Saturation (%)",

    # Prescriptions
    "prescriptions":        "Prescriptions",
    "add_prescription":     "Add Prescription",
    "medicine_name":        "Medicine Name",
    "dosage":               "Dosage",
    "frequency":            "Frequency",
    "duration":             "Duration",
    "route":                "Route",

    # Analytics
    "top_diagnoses":        "Top Diagnoses",
    "top_medications":      "Top Medications",
    "disease_distribution": "Disease Distribution",
    "no_data_yet":          "No clinical data yet. Create a visit in Scriber AI to see analytics.",

    # Status messages
    "success":              "Success",
    "error":                "Error",
    "warning":              "Warning",
    "info":                 "Information",
    "recording_started":    "Recording started",
    "recording_stopped":    "Recording stopped",
    "soap_generated":       "SOAP note generated successfully",
    "no_audio":             "No audio recorded",
    "microphone_error":     "Microphone not detected",
    "db_connected":         "Database Connected",
    "search_placeholder":   "Search...",
    "no_results":           "No results found",
    "save_success":         "Saved successfully",
    "loading":              "Loading...",
}

# ─── Indian Languages (all 22 official + English) ─────────────────────────────

INDIAN_LANGUAGES: dict = {
    "en":       "🇬🇧 English",
    "hi":       "🇮🇳 हिन्दी (Hindi)",
    "bn":       "🇮🇳 বাংলা (Bengali)",
    "te":       "🇮🇳 తెలుగు (Telugu)",
    "mr":       "🇮🇳 मराठी (Marathi)",
    "ta":       "🇮🇳 தமிழ் (Tamil)",
    "ur":       "🇮🇳 اردو (Urdu)",
    "gu":       "🇮🇳 ગુજરાતી (Gujarati)",
    "kn":       "🇮🇳 ಕನ್ನಡ (Kannada)",
    "ml":       "🇮🇳 മലയാളം (Malayalam)",
    "or":       "🇮🇳 ଓଡ଼ିଆ (Odia)",
    "pa":       "🇮🇳 ਪੰਜਾਬੀ (Punjabi)",
    "as":       "🇮🇳 অসমীয়া (Assamese)",
    "ne":       "🇮🇳 नेपाली (Nepali)",
    "sa":       "🇮🇳 संस्कृतम् (Sanskrit)",
    "sd":       "🇮🇳 سنڌي (Sindhi)",
    "ks":       "🇮🇳 كٲشُر (Kashmiri)",
    "mai":      "🇮🇳 मैथिली (Maithili)",
    "kok":      "🇮🇳 कोंकणी (Konkani)",
    "mni-Mtei": "🇮🇳 ꯃꯩꯇꯩ (Manipuri)",
    "sat":      "🇮🇳 ᱥᱟᱱᱛᱟᱲᱤ (Santali)",
    "doi":      "🇮🇳 डोगरी (Dogri)",
    "brx":      "🇮🇳 बड़ो (Bodo)",
}

# Cache file path
_CACHE_PATH = Path(__file__).parent / "translations_cache.json"

# In-memory cache for this process
_mem_cache: dict = {}


# ─── Cache helpers ─────────────────────────────────────────────────────────────

def _load_disk_cache() -> dict:
    """Load cached translations from disk."""
    try:
        if _CACHE_PATH.exists():
            with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_disk_cache(cache: dict):
    """Save translations cache to disk."""
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# Load disk cache into memory on module import
_disk_cache = _load_disk_cache()
_mem_cache.update(_disk_cache)


# ─── Translation engine ────────────────────────────────────────────────────────

def _translate_string(text: str, target_lang: str) -> str:
    """
    Translate a single string to target language using Google Translate.
    Falls back to original English text on any error.
    """
    if target_lang == "en" or not text.strip():
        return text

    cache_key = f"{target_lang}::{text}"
    if cache_key in _mem_cache:
        return _mem_cache[cache_key]

    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="en", target=target_lang).translate(text)
        if translated:
            _mem_cache[cache_key] = translated
            return translated
    except Exception:
        pass

    return text  # fallback to English


def _get_language_strings(lang: str) -> dict:
    """
    Return the full dict of translated UI strings for lang.
    Translates all BASE_STRINGS at once, caching results.
    """
    if lang == "en":
        return BASE_STRINGS.copy()

    result = {}
    needs_save = False

    for key, english_text in BASE_STRINGS.items():
        cache_key = f"{lang}::{english_text}"
        if cache_key in _mem_cache:
            result[key] = _mem_cache[cache_key]
        else:
            translated = _translate_string(english_text, lang)
            result[key] = translated
            if translated != english_text:
                _mem_cache[cache_key] = translated
                needs_save = True

    if needs_save:
        _save_disk_cache(_mem_cache)

    return result


# ─── Public API ────────────────────────────────────────────────────────────────

def get_language_list() -> dict:
    """Return all supported languages with display names."""
    return INDIAN_LANGUAGES


def get_translation(language: str, key: str, default: str = None) -> str:
    """
    Get a single translated string.

    Args:
        language: language code (e.g. 'hi', 'ta', 'en')
        key:      key from BASE_STRINGS
        default:  fallback text if key not found

    Returns:
        Translated string, or default/key if not found
    """
    if language == "en":
        return BASE_STRINGS.get(key, default or key)

    english_text = BASE_STRINGS.get(key, default or key)
    return _translate_string(english_text, language)


def translate_all(language: str) -> dict:
    """Return all translated strings for the given language (used for batch pre-loading)."""
    return _get_language_strings(language)


def preload_language(language: str):
    """
    Pre-translate all BASE_STRINGS for a language in one batch call.
    Call this after user selects a language so subsequent t() calls are instant.
    """
    if language == "en":
        return

    untranslated = [
        text for text in BASE_STRINGS.values()
        if f"{language}::{text}" not in _mem_cache
    ]

    if not untranslated:
        return  # All already cached

    try:
        from deep_translator import GoogleTranslator
        # Batch-translate up to 4500 chars at a time (Google limit)
        translator = GoogleTranslator(source="en", target=language)

        batch = []
        batch_len = 0
        SEPARATOR = " ||| "
        SEP_LEN = len(SEPARATOR)

        def flush(b):
            if not b:
                return
            joined = SEPARATOR.join(b)
            try:
                result = translator.translate(joined) or ""
                parts = result.split(SEPARATOR.strip())
                if len(parts) == len(b):
                    for orig, trs in zip(b, parts):
                        trs = trs.strip()
                        if trs:
                            _mem_cache[f"{language}::{orig}"] = trs
                else:
                    # Fallback: translate individually
                    for orig in b:
                        _translate_string(orig, language)
            except Exception:
                for orig in b:
                    _translate_string(orig, language)

        for text in untranslated:
            if batch_len + len(text) + SEP_LEN > 4000:
                flush(batch)
                batch = []
                batch_len = 0
            batch.append(text)
            batch_len += len(text) + SEP_LEN

        flush(batch)
        _save_disk_cache(_mem_cache)

    except Exception:
        pass  # Graceful degradation — individual calls will happen on demand


# ─── Clinical content translation helpers ──────────────────────────────────────

def translate_to_english(text: str, source_lang: str) -> str:
    """
    Translate clinical transcript from any language to English.
    Used before feeding text into the LLM so the model always receives English.
    Falls back to original text on any error.
    """
    if source_lang == "en" or not text or not text.strip():
        return text

    cache_key = f"to_en::{source_lang}::{text[:80]}"
    if cache_key in _mem_cache:
        return _mem_cache[cache_key]

    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source=source_lang, target="en").translate(text)
        if translated:
            _mem_cache[cache_key] = translated
            _save_disk_cache(_mem_cache)
            return translated
    except Exception:
        pass

    return text  # fallback: return as-is


def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translate AI-generated English clinical text back to the clinician's language.
    Used after BioMistral generates a SOAP note so the output matches the user's language.
    Falls back to original English text on any error.
    """
    if target_lang == "en" or not text or not text.strip():
        return text

    cache_key = f"from_en::{target_lang}::{text[:80]}"
    if cache_key in _mem_cache:
        return _mem_cache[cache_key]

    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="en", target=target_lang).translate(text)
        if translated:
            _mem_cache[cache_key] = translated
            _save_disk_cache(_mem_cache)
            return translated
    except Exception:
        pass

    return text  # fallback: return English
