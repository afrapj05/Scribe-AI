"""
Twilio WhatsApp helper for Silverline Hospital appointment reminders.

Required environment variables (set in .env or OS environment — never hardcode):
  TWILIO_ACCOUNT_SID      Your Twilio Account SID (starts with AC...)
  TWILIO_AUTH_TOKEN       Your Twilio Auth Token
  TWILIO_FROM_WHATSAPP    Sender number, e.g. whatsapp:+14155238886
  TWILIO_CONTENT_SID      Content template SID (starts with HX...)
"""
import os
import uuid
import sqlite3
from datetime import datetime


def _require_env(var: str) -> str:
    """Return the value of an environment variable or raise a clear error."""
    value = os.getenv(var)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {var}\n"
            f"Add it to your .env file before using WhatsApp features."
        )
    return value


# Credentials loaded lazily (only when send_appointment_reminder is called)
DB_FILE = os.getenv("DATABASE_URL", "sqlite:///clinical_records.db").replace("sqlite:///", "")


def send_appointment_reminder(to_number: str, appointment_date: str, appointment_time: str,
                              patient_name: str = "", created_by: str = "system") -> dict:
    """
    Send a WhatsApp appointment reminder.

    Args:
        to_number:        Phone number in E.164 format, e.g. '+91XXXXXXXXXX'
        appointment_date: Date string shown in the message, e.g. '12/1'
        appointment_time: Time string shown in the message, e.g. '3pm'
        patient_name:     Patient name for logging
        created_by:       Clinician username for logging

    Returns:
        {'success': bool, 'message_sid': str | None, 'error': str | None}
    """
    try:
        from twilio.rest import Client  # type: ignore
    except ImportError:
        return {"success": False, "message_sid": None, "error": "twilio package not installed. Run: pip install twilio"}

    to_wa = f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number

    try:
        account_sid  = _require_env("TWILIO_ACCOUNT_SID")
        auth_token   = _require_env("TWILIO_AUTH_TOKEN")
        from_number  = _require_env("TWILIO_FROM_WHATSAPP")
        content_sid  = _require_env("TWILIO_CONTENT_SID")

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_=from_number,
            content_sid=content_sid,
            content_variables=f'{{"1":"{appointment_date}","2":"{appointment_time}"}}',
            to=to_wa,
        )
        _log_whatsapp(to_number, patient_name, message.sid,
                      appointment_date, appointment_time, "sent", created_by)
        return {"success": True, "message_sid": message.sid, "error": None}
    except RuntimeError as exc:
        return {"success": False, "message_sid": None, "error": str(exc)}
    except Exception as exc:
        _log_whatsapp(to_number, patient_name, None,
                      appointment_date, appointment_time, f"failed: {exc}", created_by)
        return {"success": False, "message_sid": None, "error": str(exc)}


def _log_whatsapp(to_number, patient_name, message_sid,
                  appt_date, appt_time, status, created_by):
    """Persist a log row to whatsapp_logs table."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            """INSERT INTO whatsapp_logs
               (log_id, to_number, patient_name, message_sid,
                appointment_date, appointment_time, status, created_at, created_by)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), to_number, patient_name, message_sid,
             appt_date, appt_time, status, datetime.now().isoformat(), created_by)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[whatsapp_log] Could not log: {e}")
