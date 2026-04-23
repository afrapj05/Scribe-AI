"""
Quick Database Verification Test
Tests that all database functionality works correctly.
"""

import sys
sys.path.insert(0, 'C:\\Users\\calvi\\OneDrive\\Desktop\\impact')

print("🔍 Testing Database Manager Functionality...\n")

try:
    from db_manager import DatabaseManager
    print("✅ DatabaseManager imported successfully")
except Exception as e:
    print(f"❌ Failed to import DatabaseManager: {e}")
    sys.exit(1)

try:
    db_mgr = DatabaseManager()
    print("✅ DatabaseManager initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize DatabaseManager: {e}")
    sys.exit(1)

# Test 1: Get database stats
print("\n📊 Test 1: Database Stats")
try:
    stats = db_mgr.get_database_stats()
    print(f"  Total Patients: {stats.get('total_patients', 0)}")
    print(f"  Total Visits: {stats.get('total_visits', 0)}")
    print(f"  Total SOAP Notes: {stats.get('total_soap_notes', 0)}")
    print(f"  Total Recordings: {stats.get('total_audio_recordings', 0)}")
    print("✅ Database stats retrieved successfully")
except Exception as e:
    print(f"❌ Failed to get database stats: {e}")

# Test 2: Get all patients
print("\n👥 Test 2: Get All Patients")
try:
    patients_df = db_mgr.get_all_patients_df()
    if patients_df.empty:
        print("  ℹ️ No patients in database yet (this is okay)")
    else:
        print(f"  ✅ Found {len(patients_df)} patients")
        print(f"  Columns: {list(patients_df.columns)}")
except Exception as e:
    print(f"❌ Failed to get patients: {e}")

# Test 3: Create a test patient
print("\n✏️ Test 3: Create Test Patient")
try:
    success, patient_id = db_mgr.create_patient(
        name="Test Patient",
        age=35,
        gender="Male",
        phone="9876543210",
        email="test@example.com",
        blood_group="O+",
        chronic_conditions=["Test Condition"]
    )
    if success:
        print(f"  ✅ Patient created successfully!")
        print(f"  Patient ID: {patient_id}")
    else:
        print(f"  ⚠️ Patient creation returned False: {patient_id}")
except Exception as e:
    print(f"❌ Failed to create patient: {e}")
    patient_id = None

# Test 4: Create a test visit (if we have a patient)
print("\n🏥 Test 4: Create Test Visit")
if patient_id:
    try:
        success, visit_id = db_mgr.create_visit(
            patient_id=patient_id,
            chief_complaint="Test complaint"
        )
        if success:
            print(f"  ✅ Visit created successfully!")
            print(f"  Visit ID: {visit_id}")
        else:
            print(f"  ⚠️ Visit creation returned False: {visit_id}")
    except Exception as e:
        print(f"❌ Failed to create visit: {e}")
        visit_id = None
else:
    print("  ⏭️ Skipped (no patient ID)")
    visit_id = None

# Test 5: Query the created patient back
print("\n🔍 Test 5: Retrieve Created Patient")
if patient_id:
    try:
        patient = db_mgr.get_patient_by_id(patient_id)
        if patient:
            print(f"  ✅ Patient retrieved successfully!")
            print(f"  Name: {patient['name']}")
            print(f"  Age: {patient['age']}")
            print(f"  Email: {patient['email']}")
        else:
            print(f"  ❌ Patient not found in database")
    except Exception as e:
        print(f"❌ Failed to retrieve patient: {e}")

# Test 6: Search patients
print("\n🔎 Test 6: Search Patients")
try:
    search_results = db_mgr.search_patients("Test")
    if search_results.empty:
        print("  ℹ️ No search results (database might be empty)")
    else:
        print(f"  ✅ Found {len(search_results)} matching patients")
except Exception as e:
    print(f"❌ Failed to search patients: {e}")

# Test 7: Database connection
print("\n🔗 Test 7: Database Connection")
try:
    from database import Session
    session = Session()
    result = session.query(Session).first()
    session.close()
    print("  ✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

print("\n" + "="*50)
print("✅ ALL TESTS COMPLETED")
print("="*50)
print("\n🎙️ You're ready to start the Streamlit app!")
print("Command: streamlit run app.py")
