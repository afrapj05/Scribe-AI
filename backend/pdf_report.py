"""
PDF Hospital Report Generator — Silverline Hospital, Mumbai
Uses ReportLab to produce a standards-compliant, print-ready clinical report.
"""
from __future__ import annotations
import io
import json
import os
from datetime import datetime
from typing import Any, Dict, List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether, Image,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ── Hospital constants ────────────────────────────────────────────────────────
HOSPITAL_NAME = "Silverline Hospital"
HOSPITAL_TAGLINE = "Excellence in Cardiac & General Medicine"
HOSPITAL_ADDRESS = "Andheri West, Mumbai - 400 058, Maharashtra, India"
HOSPITAL_PHONE = "+91-22-4567-8900"
HOSPITAL_EMAIL = "care@silverlinehospital.in"
HOSPITAL_WEBSITE = "www.silverlinehospital.in"
HOSPITAL_REG = "MH/MUM/12345A | NABH Accredited"
NABL_INFO = "ABDM Compliant  ·  ISO 9001:2015 Certified"

DOCTOR_NAME = "Dr. Afra Parveen Jameel"
DOCTOR_QUAL = "MBBS, MD (Cardiology)"
DOCTOR_REG = "Reg. No. MCI-98765"
DOCTOR_DEPT = "Department of Cardiology"

# Brand colours
C_NAVY   = HexColor("#071d3a")
C_TEAL   = HexColor("#0d9488")
C_TEAL_L = HexColor("#99f6e4")
C_BLUE   = HexColor("#0057b8")
C_LIGHT  = HexColor("#f0f6ff")
C_MUTED  = HexColor("#64748b")
C_RED    = HexColor("#b91c1c")
C_AMBER  = HexColor("#b45309")
C_GREEN  = HexColor("#15803d")


def _make_styles():
    base = getSampleStyleSheet()
    styles = {
        "hospital_name": ParagraphStyle("hospital_name",
            fontSize=18, fontName="Helvetica-Bold",
            textColor=C_NAVY, spaceAfter=1*mm, leading=22),
        "hospital_tagline": ParagraphStyle("hospital_tagline",
            fontSize=8, fontName="Helvetica",
            textColor=C_TEAL, spaceAfter=1*mm),
        "hospital_address": ParagraphStyle("hospital_address",
            fontSize=7.5, fontName="Helvetica",
            textColor=C_MUTED, spaceAfter=0.5*mm),
        "section_title": ParagraphStyle("section_title",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=white, spaceAfter=3*mm, spaceBefore=0),
        "field_label": ParagraphStyle("field_label",
            fontSize=7.5, fontName="Helvetica-Bold",
            textColor=C_MUTED, spaceBefore=2*mm),
        "field_value": ParagraphStyle("field_value",
            fontSize=9, fontName="Helvetica",
            textColor=C_NAVY, leading=13, spaceAfter=1.5*mm),
        "body": ParagraphStyle("body",
            fontSize=8.5, fontName="Helvetica",
            textColor=C_NAVY, leading=13, spaceAfter=2*mm),
        "icd_code": ParagraphStyle("icd_code",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=C_RED),
        "footer": ParagraphStyle("footer",
            fontSize=7, fontName="Helvetica",
            textColor=C_MUTED, alignment=TA_CENTER),
        "sig_name": ParagraphStyle("sig_name",
            fontSize=10, fontName="Helvetica-Bold", textColor=C_NAVY),
        "sig_detail": ParagraphStyle("sig_detail",
            fontSize=8, fontName="Helvetica", textColor=C_MUTED),
        "doc_title": ParagraphStyle("doc_title",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=C_NAVY, alignment=TA_CENTER, spaceAfter=0),
    }
    return styles


def _section_header(title: str, styles):
    """Blue bar with white text section header."""
    data = [[Paragraph(f"  {title}", styles["section_title"])]]
    t = Table(data, colWidths=[175*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1),  4),
        ("BOTTOMPADDING", (0, 0), (-1, -1),  4),
        ("LEFTPADDING",   (0, 0), (-1, -1),  6),
        ("RIGHTPADDING",  (0, 0), (-1, -1),  6),
    ]))
    return t


def _info_row(label: str, value: str, styles):
    p_label = Paragraph(label, styles["field_label"])
    p_val   = Paragraph(str(value or "—"), styles["field_value"])
    return [p_label, p_val]


def generate_hospital_report(
    soap: Dict[str, Any],
    patient: Dict[str, Any],
    visit: Dict[str, Any] | None = None,
) -> bytes | None:
    """
    Generate a PDF hospital report as bytes.

    Args:
        soap:    SOAP note dict (subjective, objective, assessment, plan,
                  icd10_codes, medications_prescribed)
        patient: Patient dict (name, age, gender, blood_group, phone, …)
        visit:   Visit dict (chief_complaint, visit_date, visit_type, department)

    Returns:
        Raw PDF bytes or None if reportlab is not installed.
    """
    if not HAS_REPORTLAB:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm,   bottomMargin=20*mm,
    )
    styles = _make_styles()
    story: List[Any] = []
    W = 175*mm   # usable width

    # ── HEADER ───────────────────────────────────────────────────────────────
    header_table = Table([[
        [
            Paragraph(HOSPITAL_NAME,    styles["hospital_name"]),
            Paragraph(HOSPITAL_TAGLINE, styles["hospital_tagline"]),
            Paragraph(HOSPITAL_ADDRESS, styles["hospital_address"]),
            Paragraph(f"☎ {HOSPITAL_PHONE}  ✉ {HOSPITAL_EMAIL}", styles["hospital_address"]),
            Paragraph(HOSPITAL_REG,     styles["hospital_address"]),
        ],
        [
            Spacer(1, 4*mm),
            Paragraph("CLINICAL REPORT", styles["doc_title"]),
            Paragraph(f"Date: {datetime.now().strftime('%d %b %Y  %H:%M')}", styles["footer"]),
            Spacer(1, 2*mm),
        ]
    ]], colWidths=[120*mm, 55*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1),  3),
        ("BOTTOMPADDING",(0, 0), (-1, -1),  3),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width=W, thickness=2, color=C_TEAL, spaceAfter=4*mm))

    # ── PATIENT DEMOGRAPHICS ─────────────────────────────────────────────────
    story.append(_section_header("PATIENT INFORMATION", styles))
    story.append(Spacer(1, 2*mm))

    demo_data = [
        [Paragraph("Patient Name",     styles["field_label"]),
         Paragraph(str(patient.get("name","—")), styles["field_value"]),
         Paragraph("Patient ID",       styles["field_label"]),
         Paragraph(str(patient.get("patient_id","—")), styles["field_value"])],
        [Paragraph("Age / Gender",     styles["field_label"]),
         Paragraph(f"{patient.get('age','—')} yrs / {patient.get('gender','—')}", styles["field_value"]),
         Paragraph("Blood Group",      styles["field_label"]),
         Paragraph(str(patient.get("blood_group","—")), styles["field_value"])],
        [Paragraph("Contact",          styles["field_label"]),
         Paragraph(str(patient.get("phone","—")), styles["field_value"]),
         Paragraph("Visit Type",       styles["field_label"]),
         Paragraph(str((visit or {}).get("visit_type","Outpatient")), styles["field_value"])],
        [Paragraph("Chief Complaint",  styles["field_label"]),
         Paragraph(str((visit or {}).get("chief_complaint", soap.get("chief_complaint","—"))), styles["field_value"]),
         Paragraph("Department",       styles["field_label"]),
         Paragraph(str((visit or {}).get("department","Cardiology")), styles["field_value"])],
    ]
    demo_table = Table(demo_data, colWidths=[35*mm, 52*mm, 35*mm, 53*mm])
    demo_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, HexColor("#dde6f3")),
    ]))
    story.append(demo_table)
    story.append(Spacer(1, 4*mm))

    # ── SOAP NOTE ────────────────────────────────────────────────────────────
    story.append(_section_header("CLINICAL SOAP NOTE", styles))
    story.append(Spacer(1, 2*mm))

    def soap_section(icon: str, label: str, key: str):
        text = soap.get(key) or "—"
        story.append(Paragraph(f"<b>{icon} {label}</b>", styles["field_label"]))
        story.append(Paragraph(text, styles["body"]))
        story.append(Spacer(1, 1*mm))

    soap_section("S", "Subjective (Patient History)",  "subjective")
    soap_section("O", "Objective (Clinical Findings)", "objective")
    soap_section("A", "Assessment (Diagnosis)",        "assessment")
    soap_section("P", "Plan (Treatment)",              "plan")

    # ── ICD-10 CODES ─────────────────────────────────────────────────────────
    icd_codes = soap.get("icd10_codes") or []
    if icd_codes:
        story.append(Spacer(1, 2*mm))
        story.append(_section_header("ICD-10 DIAGNOSTIC CODES", styles))
        story.append(Spacer(1, 2*mm))
        icd_rows = []
        for item in icd_codes:
            if isinstance(item, dict):
                code = item.get("icd10_code", item.get("code", ""))
                desc = item.get("description", "")
            else:
                code = str(item)
                desc = ""
            icd_rows.append([
                Paragraph(code, styles["icd_code"]),
                Paragraph(desc or "—", styles["body"]),
            ])
        icd_table = Table(icd_rows, colWidths=[30*mm, 145*mm])
        icd_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#fff1f2")),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -2), 0.3, HexColor("#fecdd3")),
        ]))
        story.append(icd_table)

    # ── MEDICATIONS ───────────────────────────────────────────────────────────
    meds = soap.get("medications_prescribed") or []
    if meds:
        story.append(Spacer(1, 4*mm))
        story.append(_section_header("MEDICATIONS PRESCRIBED", styles))
        story.append(Spacer(1, 2*mm))

        med_header = [
            Paragraph("Medicine", styles["field_label"]),
            Paragraph("Dosage",   styles["field_label"]),
            Paragraph("Frequency",styles["field_label"]),
            Paragraph("Duration", styles["field_label"]),
            Paragraph("Route",    styles["field_label"]),
        ]
        med_rows = [med_header]
        for m in meds:
            if isinstance(m, dict):
                med_rows.append([
                    Paragraph(str(m.get("name","—")),      styles["body"]),
                    Paragraph(str(m.get("dosage","—")),    styles["body"]),
                    Paragraph(str(m.get("frequency","—")), styles["body"]),
                    Paragraph(str(m.get("duration","—")),  styles["body"]),
                    Paragraph(str(m.get("route","Oral")),  styles["body"]),
                ])
            else:
                med_rows.append([Paragraph(str(m), styles["body"]),
                                 Paragraph("—",    styles["body"]),
                                 Paragraph("—",    styles["body"]),
                                 Paragraph("—",    styles["body"]),
                                 Paragraph("Oral", styles["body"])])
        med_table = Table(med_rows, colWidths=[55*mm, 30*mm, 30*mm, 30*mm, 30*mm])
        med_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
            ("TEXTCOLOR",  (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), C_LIGHT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_LIGHT, white]),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -2), 0.3, HexColor("#dde6f3")),
        ]))
        story.append(med_table)

    # ── ALLERGIES / WARNINGS ──────────────────────────────────────────────────
    allergies = patient.get("allergies") or []
    if allergies:
        story.append(Spacer(1, 4*mm))
        allergy_text = "⚠ ALLERGIES: " + ", ".join(allergies)
        allergy_para = Paragraph(allergy_text,
            ParagraphStyle("allergy",
                fontSize=8.5, fontName="Helvetica-Bold",
                textColor=C_AMBER, borderColor=C_AMBER, borderWidth=1,
                borderPadding=4, backColor=HexColor("#fffbeb")))
        story.append(allergy_para)

    # ── DIGITAL SIGNATURE ─────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    sig_date = datetime.now().strftime("%d %b %Y")
    sig_table = Table([[
        "",
        [
            Paragraph("━" * 22, styles["sig_detail"]),
            Paragraph(DOCTOR_NAME, styles["sig_name"]),
            Paragraph(DOCTOR_QUAL, styles["sig_detail"]),
            Paragraph(DOCTOR_DEPT, styles["sig_detail"]),
            Paragraph(DOCTOR_REG,  styles["sig_detail"]),
            Spacer(1, 2*mm),
            Paragraph(f"Date: <b>{sig_date}</b>", styles["sig_detail"]),
            Paragraph("Silverline Hospital, Mumbai", styles["sig_detail"]),
        ],
    ]], colWidths=[100*mm, 75*mm])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(sig_table)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width=W, thickness=0.5, color=C_MUTED, spaceAfter=2*mm))
    story.append(Paragraph(
        f"{NABL_INFO}  ·  {HOSPITAL_WEBSITE}  ·  Emergency: {HOSPITAL_PHONE}",
        styles["footer"]))
    story.append(Paragraph(
        "This report is confidential and intended solely for the named patient and their authorised practitioners.",
        styles["footer"]))

    doc.build(story)
    return buf.getvalue()
