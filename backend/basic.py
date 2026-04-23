import streamlit as st
import whisper
import ollama
import json
import uuid
import datetime
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from tinydb import TinyDB, Query
import gc

# --- CONFIG & DATABASE ---
db = TinyDB("opd_vault.json")
PatientQuery = Query()
st.set_page_config(page_title="AI Clinical Scribe", layout="wide")

# --- UI HEADER ---
st.title("🩺 AI Clinical Scribe - High-Volume OPD")
st.markdown("*Captured dialogue to International Clinical Standards (ICD-10)*")

# --- SIDEBAR: SEARCH & RECALL ---
with st.sidebar:
    st.header("Search Patient History")
    search_id = st.text_input("Enter Patient ID", "PAT-101")
    if st.button("Recall History"):
        results = db.search(PatientQuery.patient_id == search_id)
        if results:
            for res in reversed(results): # Show latest first
                with st.expander(f"Visit: {res['timestamp']}"):
                    st.json(res['structured_soap'])
        else:
            st.warning("No records found.")

# --- MAIN INTERFACE: RECORDING ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Consultation")
    if st.button("🔴 Start Recording", use_container_width=True):
        fs = 44100
        with st.spinner("Recording... Close the consultation and wait."):
            # Simple duration-based recording for this example (15 seconds)
            # In production, use a threading stop-event
            duration = 15 
            rec = sd.rec(int(duration * fs), samplerate=fs, channels=1)
            sd.wait()
            write("temp.wav", fs, rec)
        st.success("Recording Captured!")

        # --- TRANSCRIPTION ---
        with st.spinner("Transcribing & Translating..."):
            model = whisper.load_model("base")
            result = model.transcribe("temp.wav", task="translate")
            raw_text = result["text"]
            # CLEAR MEMORY FOR OLLAMA
            del model
            gc.collect() 
        
        st.info(f"Transcript: {raw_text}")

        # --- CLINICAL EXTRACTION ---
        with st.spinner("Extracting Clinical Elements..."):
            sys_prompt = (
                "You are an AI Scribe. Convert dialogue into a hospital-approved SOAP JSON. "
                "Output ONLY raw JSON. No markdown."
            )
            user_prompt = f"Transcript: {raw_text}"
            
            try:
                response = ollama.generate(
                    model='cniongolo/biomistral',
                    system=sys_prompt,
                    prompt=user_prompt,
                    format='json'
                )
                soap_data = json.loads(response['response'])
                
                # SAVE TO TINYDB
                record = {
                    "visit_id": str(uuid.uuid4())[:8],
                    "patient_id": search_id,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "structured_soap": soap_data
                }
                db.insert(record)
                
                st.session_state['latest_soap'] = soap_data
            except Exception as e:
                st.error(f"Ollama Error: {e}. Try closing other apps to free RAM.")

with col2:
    st.subheader("Structured Clinical Note")
    if 'latest_soap' in st.session_state:
        st.json(st.session_state['latest_soap'])
        st.button("✅ Approve and Sync to EMR")