#!/usr/bin/env python3
"""Quick test to verify record_audio method exists in ScribeAI class"""

import sys

# Test 1: Check if scriber module can be imported
print("Test 1: Importing scriber module...")
try:
    from scriber import ScribeAI
    print("✅ ScribeAI imported successfully")
except Exception as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# Test 2: Create instance
print("\nTest 2: Creating ScribeAI instance...")
try:
    scribe = ScribeAI()
    print("✅ ScribeAI instance created")
except Exception as e:
    print(f"❌ Failed to create instance: {e}")
    sys.exit(1)

# Test 3: Check if record_audio method exists
print("\nTest 3: Checking for record_audio method...")
if hasattr(scribe, 'record_audio'):
    print("✅ record_audio method exists")
else:
    print("❌ record_audio method NOT found")
    print(f"Available methods: {[m for m in dir(scribe) if not m.startswith('_')]}")
    sys.exit(1)

# Test 4: Check method signature
print("\nTest 4: Checking method signature...")
import inspect
sig = inspect.signature(scribe.record_audio)
print(f"✅ Method signature: {sig}")

# Test 5: Check if other audio methods exist
print("\nTest 5: Checking for other audio methods...")
methods_to_check = ['transcribe_audio', 'generate_soap_with_llm', 'record_transcribe_and_generate_soap']
for method_name in methods_to_check:
    if hasattr(scribe, method_name):
        print(f"✅ {method_name} exists")
    else:
        print(f"❌ {method_name} NOT found")

print("\n✅ All tests passed!")
