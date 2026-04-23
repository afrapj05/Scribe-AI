"""
Medicine directory — loads from A_Z_medicines_dataset_of_India.csv (11 000+ drugs).
Falls back to a small built-in list if the CSV is not found.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional

# ─── CSV-based loader ────────────────────────────────────────────────────────

CSV_PATH = Path(__file__).parent / "A_Z_medicines_dataset_of_India.csv"

def _load_from_csv() -> List[Dict]:
    """Load and normalise medicines from the India A-Z CSV dataset."""
    try:
        import pandas as pd
        df = pd.read_csv(CSV_PATH, dtype=str)
        df = df.fillna("")

        # Normalise column names (strip whitespace)
        df.columns = [c.strip() for c in df.columns]

        medicines = []
        for idx, row in df.iterrows():
            # Derive a usable category from the 'type' column
            category = row.get("type", "").strip() or "General"

            # Build composition string from two composition columns
            comp1 = row.get("short_composition1", "").strip()
            comp2 = row.get("short_composition2", "").strip()
            composition = ", ".join(filter(None, [comp1, comp2]))

            # Dosage form: infer from pack_size_label
            pack = row.get("pack_size_label", "").strip()
            dosage_form = _infer_dosage_form(pack)

            # Price
            raw_price = row.get("price(₹)", "").strip()
            try:
                price = float(raw_price) if raw_price else None
            except ValueError:
                price = None

            # Discontinued flag
            discontinued_raw = row.get("Is_discontinued", "").strip().lower()
            is_discontinued = discontinued_raw in ("true", "1", "yes")

            medicines.append({
                "id": str(row.get("id", idx)).strip(),
                "drug_name": row.get("name", "Unknown").strip(),
                "category": category,
                "dosage_form": dosage_form,
                "manufacturer": row.get("manufacturer_name", "").strip(),
                "pack_size": pack,
                "composition": composition,
                "short_composition1": comp1,
                "short_composition2": comp2,
                "price": price,
                "is_discontinued": is_discontinued,
                # Legacy fields expected by add-ons / drug interaction checker
                "side_effects": [],
                "typical_dose": composition or "As directed",
            })
        return medicines

    except Exception as e:
        print(f"[MedicineManager] CSV load failed: {e}. Falling back to built-in list.")
        return []


def _infer_dosage_form(pack_label: str) -> str:
    """Heuristically extract dosage form from pack_size_label."""
    label = pack_label.lower()
    if "tablet" in label or "tab" in label:
        return "Tablet"
    if "capsule" in label or "cap" in label:
        return "Capsule"
    if "syrup" in label or "suspension" in label:
        return "Syrup"
    if "injection" in label or "vial" in label or "ampoule" in label:
        return "Injection"
    if "cream" in label or "ointment" in label or "gel" in label:
        return "Topical"
    if "drop" in label:
        return "Drops"
    if "inhaler" in label or "inhale" in label:
        return "Inhaler"
    if "patch" in label:
        return "Patch"
    if "solution" in label or "lotion" in label:
        return "Solution"
    if "powder" in label or "sachet" in label:
        return "Powder"
    return "Other"


# ─── Built-in fallback list (26 core drugs) ──────────────────────────────────

_FALLBACK_MEDICINES = [
    {"id": "MED001", "drug_name": "Amoxicillin",        "category": "Antibiotic",              "dosage_form": "Tablet",   "side_effects": ["Rash", "Nausea", "Diarrhea"],                          "typical_dose": "500mg TDS",   "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
    {"id": "MED002", "drug_name": "Metformin",           "category": "Antidiabetic",            "dosage_form": "Tablet",   "side_effects": ["GI upset", "Lactic acidosis"],                        "typical_dose": "500mg BD",    "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
    {"id": "MED003", "drug_name": "Atorvastatin",        "category": "Statin",                  "dosage_form": "Tablet",   "side_effects": ["Myalgia", "Liver enzyme elevation"],                  "typical_dose": "20mg OD",     "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
    {"id": "MED004", "drug_name": "Metoprolol",          "category": "Beta Blocker",            "dosage_form": "Tablet",   "side_effects": ["Bradycardia", "Fatigue", "Cold extremities"],         "typical_dose": "50mg BD",     "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
    {"id": "MED005", "drug_name": "Omeprazole",          "category": "PPI",                     "dosage_form": "Capsule",  "side_effects": ["Headache", "Nausea", "Diarrhea"],                     "typical_dose": "20mg OD",     "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
    {"id": "MED006", "drug_name": "Warfarin",            "category": "Anticoagulant",           "dosage_form": "Tablet",   "side_effects": ["Bleeding", "Bruising"],                               "typical_dose": "Variable",    "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
    {"id": "MED007", "drug_name": "Amlodipine",          "category": "Calcium Channel Blocker", "dosage_form": "Tablet",   "side_effects": ["Ankle edema", "Headache", "Flushing"],                "typical_dose": "5mg OD",      "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
    {"id": "MED008", "drug_name": "Lisinopril",          "category": "ACE Inhibitor",           "dosage_form": "Tablet",   "side_effects": ["Dry cough", "Hyperkalemia", "Dizziness"],             "typical_dose": "10mg OD",     "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
    {"id": "MED009", "drug_name": "Aspirin",             "category": "Antiplatelet",            "dosage_form": "Tablet",   "side_effects": ["GI bleeding", "Tinnitus"],                            "typical_dose": "75mg OD",     "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
    {"id": "MED010", "drug_name": "Paracetamol",         "category": "Analgesic/Antipyretic",   "dosage_form": "Tablet",   "side_effects": ["Hepatotoxicity (overdose)"],                          "typical_dose": "500-1000mg",  "manufacturer": "", "composition": "", "price": None, "is_discontinued": False},
]


# ─── MedicineManager ─────────────────────────────────────────────────────────

class MedicineManager:
    """Manage the medicine directory using the full India A-Z CSV dataset."""

    def __init__(self):
        self.medicines: List[Dict] = []
        self._source = "csv"
        self._load()

    # ── Loader ──────────────────────────────────────────────────────────────

    def _load(self):
        if CSV_PATH.exists():
            self.medicines = _load_from_csv()
            self._source = "csv"
            if not self.medicines:          # CSV parsed but returned empty
                self.medicines = _FALLBACK_MEDICINES
                self._source = "fallback"
        else:
            self.medicines = _FALLBACK_MEDICINES
            self._source = "fallback"

    # ── Public API ──────────────────────────────────────────────────────────

    @property
    def total_count(self) -> int:
        return len(self.medicines)

    @property
    def source_label(self) -> str:
        if self._source == "csv":
            return f"{self.total_count:,} medicines loaded from Indian Medicine Database"
        return f"{self.total_count} medicines (built-in list)"

    def get_all_medicines(self) -> List[Dict]:
        """Return all medicines (full list)."""
        return self.medicines

    def search_medicines(self, query: str) -> List[Dict]:
        """Case-insensitive search by name, composition, category, or manufacturer."""
        q = query.lower().strip()
        if not q:
            return self.medicines
        results = []
        for m in self.medicines:
            if (
                q in m.get("drug_name", "").lower()
                or q in m.get("category", "").lower()
                or q in m.get("composition", "").lower()
                or q in m.get("manufacturer", "").lower()
                or q in m.get("short_composition1", "").lower()
                or q in m.get("short_composition2", "").lower()
            ):
                results.append(m)
        return results

    def get_medicine_by_id(self, med_id: str) -> Optional[Dict]:
        for m in self.medicines:
            if m.get("id") == med_id:
                return m
        return None

    def get_medicines_by_category(self, category: str) -> List[Dict]:
        cat = category.lower()
        return [m for m in self.medicines if m.get("category", "").lower() == cat]

    def get_unique_categories(self) -> List[str]:
        cats = sorted({m.get("category", "Unknown") for m in self.medicines if m.get("category")})
        return cats

    def get_dataframe(self, medicines: List[Dict] = None):
        """Return a pandas DataFrame for display."""
        import pandas as pd
        data = medicines if medicines is not None else self.medicines
        rows = []
        for m in data:
            rows.append({
                "ID":           m.get("id", ""),
                "Name":         m.get("drug_name", ""),
                "Category":     m.get("category", ""),
                "Form":         m.get("dosage_form", ""),
                "Manufacturer": m.get("manufacturer", ""),
                "Composition":  m.get("composition", "") or m.get("typical_dose", ""),
                "Pack Size":    m.get("pack_size", ""),
                "Price (₹)":   m.get("price", ""),
                "Discontinued": "Yes" if m.get("is_discontinued") else "No",
            })
        return pd.DataFrame(rows)

    def check_drug_interactions(self, drug_ids: List[str]) -> List[Dict]:
        """Simplified drug-drug interaction checker."""
        KNOWN_INTERACTIONS = {
            ("Warfarin", "Aspirin"):      ("HIGH",   "Increased bleeding risk. Monitor INR closely."),
            ("Metformin", "Alcohol"):     ("MEDIUM", "Risk of lactic acidosis. Avoid alcohol."),
            ("Lisinopril", "Potassium"):  ("MEDIUM", "Risk of hyperkalaemia. Monitor electrolytes."),
            ("Warfarin", "Amoxicillin"):  ("MEDIUM", "Antibiotic may potentiate anticoagulant effect."),
        }

        selected = [self.get_medicine_by_id(mid) for mid in drug_ids if self.get_medicine_by_id(mid)]
        selected_names = {m["drug_name"] for m in selected}

        interactions = []
        checked = set()
        for pair, (risk, rec) in KNOWN_INTERACTIONS.items():
            d1, d2 = pair
            if d1 in selected_names and d2 in selected_names:
                key = tuple(sorted([d1, d2]))
                if key not in checked:
                    checked.add(key)
                    interactions.append({
                        "drug1": d1,
                        "drug2": d2,
                        "risk_level": risk,
                        "recommendation": rec,
                    })
        return interactions

if __name__ == "__main__":
    print("--- Medicine Manager Diagnostic ---")
    mgr = MedicineManager()
    print(f"Status: {mgr.source_label}")
    
    # Show stats
    cats = mgr.get_unique_categories()
    print(f"Unique Categories: {len(cats)}")
    print(f"Categories Sample: {', '.join(cats[:5])}...")
    
    # Search test
    test_query = "Amoxi"
    results = mgr.search_medicines(test_query)
    print(f"\nSearch Test ('{test_query}'): Found {len(results)} matches.")
    if results:
        sample = results[0]
        print(f"Sample Match: {sample.get('drug_name')} ({sample.get('category')})")
        print(f"Price: ₹{sample.get('price')} | Manufacturer: {sample.get('manufacturer')}")
