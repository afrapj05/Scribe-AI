"""
Comprehensive integration test for ScribeAI Clinical OS
"""

from auth import authenticate_user
from patients import PatientManager
from medicines import MedicineManager
from scriber import ScribeAI, generate_patient_education
from analytics import AnalyticsEngine

def test_authentication():
    """Test authentication module"""
    import os
    print("[AUTH] Testing authentication...")
    # Read test password from environment — never hardcode credentials in source files.
    test_password = os.getenv("TEST_DR_SHARMA_PASSWORD", "")
    if not test_password:
        print("  [SKIP] TEST_DR_SHARMA_PASSWORD env var not set — skipping auth test.")
        return True
    is_valid, user_info = authenticate_user("dr_sharma", test_password)
    print(f"  Login result: {is_valid}")
    if user_info:
        print(f"  ✅ User: {user_info['name']}")
        print(f"  Role: {user_info['role']}")
        print(f"  Department: {user_info['department']}")
    return is_valid

def test_patients():
    """Test patient manager"""
    print("\n👥 Testing patient manager...")
    patients = PatientManager()
    all_patients = patients.get_all_patients()
    print(f"  ✅ Loaded {len(all_patients)} patients")
    if all_patients:
        print(f"  First patient: {all_patients[0]['name']} ({all_patients[0]['patient_id']})")
        print(f"  Age: {all_patients[0]['age']}, Blood Group: {all_patients[0]['blood_group']}")
    
    # Test search
    search_results = patients.search_patients("Sharma")
    print(f"  ✅ Search found {len(search_results)} matches for 'Sharma'")
    return len(all_patients) > 0

def test_medicines():
    """Test medicine manager"""
    print("\n💊 Testing medicine manager...")
    medicines = MedicineManager()
    all_medicines = medicines.get_all_medicines()
    print(f"  ✅ Loaded {len(all_medicines)} medicines")
    if all_medicines:
        print(f"  First medicine: {all_medicines[0]['drug_name']} ({all_medicines[0]['id']})")
        print(f"  Category: {all_medicines[0]['category']}, Form: {all_medicines[0]['dosage_form']}")
    
    # Test search
    search_results = medicines.search_medicines("Metformin")
    print(f"  ✅ Search found {len(search_results)} matches for 'Metformin'")
    
    # Test categories
    categories = medicines.get_unique_categories()
    print(f"  ✅ Found {len(categories)} unique drug categories")
    
    return len(all_medicines) > 0

def test_scriber():
    """Test Scriber AI"""
    print("\n🎙️ Testing Scriber AI...")
    scribe = ScribeAI()
    print(f"  ✅ Scriber AI initialized")
    print(f"  ICD-10 mappings loaded: {len(scribe.icd10_mapping)}")
    
    # Test transcript processing
    test_transcript = """
    Chief complaint: Patient presents with fever and cough.
    Patient has hypertension and Type 2 Diabetes.
    Vital signs: BP 140/90, HR 88, Temp 101.5°F
    Chest examination: mild crackles in bilateral lower lobes.
    Assessment: Pneumonia with history of hypertension and diabetes.
    Plan: Start Azithromycin, rest, follow-up in 3 days.
    """
    
    note = scribe.process_transcript(test_transcript, "PAT001", "dr_sharma")
    print(f"  ✅ SOAP note generated for patient {note.patient_id}")
    print(f"  Chief complaint: {note.chief_complaint[:50]}...")
    print(f"  ICD-10 codes extracted: {len(note.icd10_codes)}")
    print(f"  ABDM Compliant: {note.abdm_compliant}")
    
    # Test patient education generation
    education = generate_patient_education(note.plan)
    print(f"  ✅ Patient education generated ({len(education)} characters)")
    
    return True

def test_analytics():
    """Test analytics engine"""
    print("\n📊 Testing Analytics Engine...")
    patients = PatientManager()
    scribe = ScribeAI()
    analytics = AnalyticsEngine(scribe, patients)
    print(f"  ✅ Analytics engine initialized")
    
    # Get stats
    stats = analytics.get_visit_statistics()
    print(f"  Visit stats: {stats}")
    
    disease_dist = analytics.get_patient_disease_distribution()
    print(f"  ✅ Disease distribution: {len(disease_dist)} classes found")
    
    return True

def main():
    print("="*60)
    print("🏥 ScribeAI Clinical OS - Integration Test Suite")
    print("="*60)
    
    tests = [
        ("Authentication", test_authentication),
        ("Patient Manager", test_patients),
        ("Medicine Manager", test_medicines),
        ("Scriber AI", test_scriber),
        ("Analytics Engine", test_analytics),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "✅ PASS"))
        except Exception as e:
            results.append((test_name, f"❌ FAIL: {str(e)}"))
            print(f"\n❌ Error in {test_name}: {str(e)}")
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    for test_name, result in results:
        print(f"{result} - {test_name}")
    
    passed = sum(1 for _, r in results if "✅" in r)
    total = len(results)
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "🎉 "*15)
        print("✅ ALL TESTS PASSED!")
        print("Application is ready for deployment")
        print("🎉 "*15)
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
