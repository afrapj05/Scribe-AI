"""
Database migration script — run on every server startup.
Safe additive-only: uses IF NOT EXISTS / try-except per column so it never
breaks if columns already exist.
"""
import sqlite3
import os

DB_FILE = os.getenv("DATABASE_URL", "sqlite:///clinical_records.db").replace("sqlite:///", "")


def run_migrations():
    print(f"[migrate] Running migrations on: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # ── soap_notes: add multilingual columns ──────────────────────────────────
    soap_columns = [
        ("language",              "TEXT DEFAULT 'en'"),
        ("subjective_localized",  "TEXT"),
        ("objective_localized",   "TEXT"),
        ("assessment_localized",  "TEXT"),
        ("plan_localized",        "TEXT"),
        ("abdm_compliant",        "INTEGER DEFAULT 0"),
        ("data_privacy_level",    "TEXT"),
    ]
    for col, col_def in soap_columns:
        try:
            cur.execute(f"ALTER TABLE soap_notes ADD COLUMN {col} {col_def}")
            print(f"[migrate] soap_notes.{col} added ✓")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                pass  # already exists, ignore
            else:
                print(f"[migrate] soap_notes.{col}: {e}")

    # ── scan_results table ────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scan_results (
            scan_id          TEXT PRIMARY KEY,
            filename         TEXT,
            document_type    TEXT,
            patient_name     TEXT,
            patient_age      TEXT,
            scan_date        TEXT,
            doctor_name      TEXT,
            hospital_name    TEXT,
            diagnoses        TEXT,   -- JSON list
            medications      TEXT,   -- JSON list
            lab_values       TEXT,   -- JSON list
            clinical_notes   TEXT,
            full_summary     TEXT,
            model_used       TEXT    DEFAULT 'qwen2.5vl:3b',
            created_at       TEXT    DEFAULT (datetime('now')),
            created_by       TEXT
        )
    """)
    print("[migrate] scan_results table ready ✓")

    # ── whatsapp_logs table ───────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_logs (
            log_id          TEXT PRIMARY KEY,
            to_number       TEXT,
            patient_name    TEXT,
            message_sid     TEXT,
            appointment_date TEXT,
            appointment_time TEXT,
            status          TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    print("[migrate] whatsapp_logs table ready ✓")

    conn.commit()
    conn.close()
    print("[migrate] All migrations complete ✓")


if __name__ == "__main__":
    run_migrations()
