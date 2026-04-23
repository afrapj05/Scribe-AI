"""
Initialize the database with medicines from CSV and demo patients.
Run this once to populate the database.
"""

import pandas as pd
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import Base, engine, Session, Medicine, Patient, User
from db_manager import DatabaseManager

def init_medicines_from_csv():
    """Load medicines from A_Z_medicines_dataset_of_India.csv into database."""
    print("Loading medicines from CSV...")
    
    csv_path = Path(__file__).parent / "A_Z_medicines_dataset_of_India.csv"
    
    if not csv_path.exists():
        print(f"CSV file not found at {csv_path}")
        return
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path, encoding='utf-8')
        print(f"Found {len(df)} medicines in CSV")
        
        session = Session()
        
        # Check if medicines already exist
        existing_count = session.query(Medicine).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} medicines. Skipping CSV import.")
            session.close()
            return
        
        # Add medicines in batches
        batch_size = 1000
        added = 0
        
        for idx, row in df.iterrows():
            try:
                medicine = Medicine(
                    medicine_id=f"MED_{row['id']}" if pd.notna(row.get('id')) else f"MED_{idx:06d}",
                    name=str(row.get('name', 'Unknown'))[:255],
                    manufacturer=str(row.get('manufacturer_name', 'Unknown'))[:255],
                    price=float(row.get('price(₹)', 0)) if pd.notna(row.get('price(₹)')) else 0,
                    dosage_form=str(row.get('type', 'Allopathy'))[:100],
                    composition=f"{row.get('short_composition1', '')}, {row.get('short_composition2', '')}".strip(', ')[:500],
                    pack_size=str(row.get('pack_size_label', ''))[:100],
                    discontinued=str(row.get('Is_discontinued', 'FALSE')).upper() == 'TRUE',
                    created_at=datetime.now()
                )
                session.add(medicine)
                added += 1
                
                if added % batch_size == 0:
                    session.commit()
                    print(f"Imported {added} medicines...")
            
            except Exception as e:
                print(f"Error importing medicine {idx}: {str(e)}")
                continue
        
        session.commit()
        session.close()
        print(f"✅ Successfully imported {added} medicines from CSV")
        
    except Exception as e:
        print(f"❌ Error loading medicines: {str(e)}")


def init_demo_patients():
    """Initialize demo patients in database."""
    print("\nInitializing demo patients...")
    
    demo_patients = [
        {
            "name": "Amit Kumar Singh",
            "age": 62,
            "gender": "Male",
            "blood_group": "O+",
            "chronic_conditions": ["Hypertension", "Type 2 Diabetes"],
            "phone": "9876543210",
            "email": "amit.singh@email.com",
            "address": "45 MG Road, Bangalore"
        },
        {
            "name": "Priya Sharma",
            "age": 45,
            "gender": "Female",
            "blood_group": "A+",
            "chronic_conditions": ["Asthma", "Hypothyroidism"],
            "phone": "9123456789",
            "email": "priya.sharma@email.com",
            "address": "12 Park Lane, Mumbai"
        },
        {
            "name": "Rajesh Gupta",
            "age": 58,
            "gender": "Male",
            "blood_group": "B+",
            "chronic_conditions": ["Coronary Artery Disease"],
            "phone": "9988776655",
            "email": "rajesh.gupta@email.com",
            "address": "78 Delhi Gate, Delhi"
        }
    ]
    
    db_mgr = DatabaseManager()
    
    for patient_data in demo_patients:
        try:
            success, patient_id = db_mgr.create_patient(
                name=patient_data['name'],
                age=patient_data['age'],
                gender=patient_data['gender'],
                blood_group=patient_data.get('blood_group', ''),
                phone=patient_data.get('phone', ''),
                email=patient_data.get('email', ''),
                address=patient_data.get('address', ''),
                chronic_conditions=patient_data.get('chronic_conditions', [])
            )
            if success:
                print(f"✅ Created patient: {patient_data['name']} (ID: {patient_id})")
            else:
                print(f"⚠️ Patient already exists: {patient_data['name']}")
        except Exception as e:
            print(f"❌ Error creating patient {patient_data['name']}: {str(e)}")


def init_demo_users():
    """Initialize demo users in database."""
    print("\nInitializing demo users...")
    
    # SECURITY: Do NOT hardcode real passwords here.
    # Set passwords using the add_clinician() API or by editing credentials.json directly.
    # The accounts below are created with LOCKED (empty) password hashes.
    demo_users = [
        {
            "username": "dr_sharma",
            "password": "",
            "name": "Dr. Sharma",
            "role": "physician",
            "email": "dr.sharma@clinic.com"
        },
        {
            "username": "dr_patel",
            "password": "",
            "name": "Dr. Patel",
            "role": "physician",
            "email": "dr.patel@clinic.com"
        },
        {
            "username": "nurse_verma",
            "password": "",
            "name": "Nurse Verma",
            "role": "nurse",
            "email": "nurse.verma@clinic.com"
        }
    ]
    
    session = Session()
    
    for user_data in demo_users:
        try:
            existing = session.query(User).filter_by(username=user_data['username']).first()
            if existing:
                print(f"⚠️ User already exists: {user_data['username']}")
                continue
            
            user = User(
                username=user_data['username'],
                password=user_data['password'],  # Note: In production, hash passwords!
                name=user_data['name'],
                role=user_data['role'],
                email=user_data['email'],
                created_at=datetime.now()
            )
            session.add(user)
            print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
        except Exception as e:
            print(f"❌ Error creating user {user_data['username']}: {str(e)}")
    
    session.commit()
    session.close()


def main():
    """Initialize the entire database."""
    print("=" * 60)
    print("🏥 Clinical OS - Database Initialization")
    print("=" * 60)
    
    # Create tables
    print("\nCreating database tables...")
    Base.metadata.create_all(engine)
    print("✅ Database tables created")
    
    # Load data
    init_medicines_from_csv()
    init_demo_patients()
    init_demo_users()
    
    print("\n" + "=" * 60)
    print("[OK] Database initialization complete!")
    print("=" * 60)
    print("\n[SETUP] User accounts created with LOCKED passwords.")
    print("  Set passwords via credentials.json or the add_clinician() API.")
    print("  Accounts: dr_sharma, dr_patel, nurse_verma")


if __name__ == "__main__":
    main()
