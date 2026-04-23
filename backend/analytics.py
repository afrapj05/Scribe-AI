"""
Analytics Engine - Generate charts and insights from SQLAlchemy clinical data.
"""

from typing import Dict, List, Tuple, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from sqlalchemy import func
from database import Session, Patient, Visit, SoapNote, Medicine

class AnalyticsEngine:
    """Generate analytics from SQLAlchemy database."""
    
    def __init__(self):
        self.db = Session()
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

    def get_summary(self) -> Dict[str, Any]:
        """Get high-level statistics."""
        week_ago = datetime.now() - timedelta(days=7)
        return {
            "total_patients": self.db.query(Patient).count(),
            "total_visits": self.db.query(Visit).count(),
            "visits_7d": self.db.query(Visit).filter(Visit.visit_date >= week_ago).count(),
            "avg_age": self.db.query(func.avg(Patient.age)).scalar() or 0,
        }

    def get_top_diagnoses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently diagnosed conditions from SOAP assessments or ICD-10."""
        notes = self.db.query(SoapNote).all()
        diagnoses = Counter()
        for note in notes:
            if note.icd10_codes:
                for entry in note.icd10_codes:
                    # Handle both old string format and new refined object format
                    name = entry.get('description') if isinstance(entry, dict) else str(entry)
                    if name: diagnoses[name] += 1
        return [{"name": k, "count": v} for k, v in diagnoses.most_common(limit)]

    def get_demographics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get age and gender distribution."""
        # Age groups
        patients = self.db.query(Patient).all()
        age_groups = Counter()
        for p in patients:
            if p.age < 18: age_groups["0-17"] += 1
            elif p.age < 40: age_groups["18-39"] += 1
            elif p.age < 60: age_groups["40-59"] += 1
            else: age_groups["60+"] += 1
        
        # Gender
        gender_data = self.db.query(Patient.gender, func.count(Patient.patient_id)).group_by(Patient.gender).all()
        
        return {
            "age_distribution": [{"name": k, "count": v} for k, v in age_groups.items()],
            "gender_distribution": [{"name": str(g or "Unknown").title(), "count": c} for g, c in gender_data]
        }

    def get_visit_volume(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily visit volume for the last X days."""
        start_date = datetime.now() - timedelta(days=days)
        visits = self.db.query(
            func.date(Visit.visit_date).label('date'),
            func.count(Visit.visit_id).label('count')
        ).filter(Visit.visit_date >= start_date).group_by(func.date(Visit.visit_date)).all()
        
        return [{"date": str(v.date), "count": v.count} for v in visits]

    def get_department_distribution(self) -> List[Dict[str, Any]]:
        """Distribution of visits by department."""
        data = self.db.query(Visit.department, func.count(Visit.visit_id)).group_by(Visit.department).all()
        return [{"name": str(d or "General").title(), "count": c} for d, c in data]

def get_clinical_analytics():
    """Helper to get all analytics for the dashboard."""
    engine = AnalyticsEngine()
    try:
        return {
            "summary": engine.get_summary(),
            "top_diagnoses": engine.get_top_diagnoses(),
            "demographics": engine.get_demographics(),
            "volume": engine.get_visit_volume(),
            "department": engine.get_department_distribution()
        }
    finally:
        del engine
