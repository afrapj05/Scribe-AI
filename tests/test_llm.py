import sys
import os
import json
sys.path.append(os.getcwd())
from scriber_enhanced import ScribeAI

def test_llama3():
    print("--- Llama 3 Clinical OS Verification ---")
    scribe = ScribeAI()
    
    transcript = "Patient reports a headache and dizziness for two days. Blood pressure is 140/90. I recommend paracetamol and rest."
    print(f"\nTesting Transcript: {transcript}")
    
    success, soap = scribe.generate_soap_with_llm(transcript)
    print(f"SOAP Generation Success: {success}")
    
    if success:
        print(f"Model ID: {soap.get('source')}")
        print(f"Chief Complaint: {soap.get('chief_complaint')}")
        print(f"ICD-10 (Refined): {soap.get('icd10_codes')}")
        
        print("\nTesting Patient Education Generation...")
        edu = scribe.generate_patient_education(soap)
        print("-" * 30)
        print(edu)
        print("-" * 30)
    else:
        print("Model call failed. Check if Ollama and llama3 are running.")

if __name__ == "__main__":
    test_llama3()
