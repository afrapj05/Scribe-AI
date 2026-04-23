"""
Enhanced Scriber AI module with SQL database, unlimited audio recording, and noise filtering.
Integrates with SQLAlchemy database models and advanced audio processing.
"""

import json
import uuid
import os
import gc
import requests
from datetime import datetime
from typing import Dict, Optional, List, Tuple, Any
import threading
import time

# Database
from database import Session, Patient, Visit, SoapNote, AudioRecording, Prescription, User, init_db
from audio_processor import AudioRecorder, AudioProcessor

# Optional imports for AI
try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


class ScribeAI:
    """
    Enhanced Scriber AI with SQL database backend, unlimited audio recording, and noise filtering.
    """
    
    def __init__(self):
        # Initialize database
        init_db()
        self.session = Session()
        
        # Audio settings
        self.sample_rate = 44100  # 44.1 kHz
        self.audio_recorder = None
        self.audio_processor = AudioProcessor(sample_rate=self.sample_rate)
        
        # ICD-10 mapping
        self.icd10_mapping = self._load_icd10_mappings()
    
    def _load_icd10_mappings(self) -> Dict[str, str]:
        """Load common condition to ICD-10 mappings."""
        return {
            "hypertension": "I10",
            "type 2 diabetes": "E11.9",
            "asthma": "J45.901",
            "copd": "J44.9",
            "pneumonia": "J18.9",
            "bronchitis": "J20.9",
            "cough": "R05.9",
            "fever": "R50.9",
            "flu": "J11.1",
            "common cold": "J00",
            "sinusitis": "J32.90",
            "otitis": "H66.001",
            "urinary tract infection": "N39.0",
            "gastroenteritis": "A09",
            "nausea": "R11.0",
            "vomiting": "R11.10",
            "diarrhea": "A09",
            "abdominal pain": "R10.9",
            "headache": "R51.9",
            "migraine": "G43.909",
            "arthritis": "M19.90",
            "back pain": "M54.5",
            "anxiety": "F41.1",
            "depression": "F32.9",
        }
    
    # ===================== AUDIO RECORDING (UNLIMITED) =====================
    def start_unlimited_recording(self) -> bool:
        """
        Start unlimited audio recording in background.
        User can stop recording at any time via UI button.
        
        Returns:
            bool: Success status
        """
        try:
            self.audio_recorder = AudioRecorder(sample_rate=self.sample_rate, channels=1)
            self.audio_recorder.start_recording()
            return True
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return False
    
    def stop_unlimited_recording(self, output_file: str = "clinical_audio.wav") -> Tuple[bool, str, float]:
        """
        Stop unlimited audio recording and save to file.
        
        Returns:
            Tuple of (success, file_path/error_msg, duration_seconds)
        """
        if not self.audio_recorder or not self.audio_recorder.is_recording:
            return False, "No active recording", 0.0
        
        try:
            duration = self.audio_recorder.stop_recording()
            success, file_path = self.audio_recorder.save_recording(output_file)
            
            if success:
                return True, file_path, duration
            else:
                return False, file_path, duration
        except Exception as e:
            return False, f"Error saving recording: {str(e)}", 0.0
    
    def get_recording_duration(self) -> float:
        """Get current recording duration in seconds."""
        if self.audio_recorder:
            return time.time() - self.audio_recorder.start_time if self.audio_recorder.start_time else 0.0
        return 0.0
    
    # ===================== AUDIO PROCESSING & FILTERING =====================
    def process_recording(
        self,
        audio_file: str,
        filter_type: str = 'bandpass',
        save_processed: bool = True
    ) -> Tuple[bool, Dict]:
        """
        Apply noise filtering to recorded audio.
        
        Args:
            audio_file: Path to audio file
            filter_type: 'bandpass', 'lowpass', 'highpass', or 'noisereduce'
            save_processed: Whether to save processed audio to file
        
        Returns:
            Tuple of (success, processing_metadata)
        """
        try:
            from scipy.io.wavfile import read, write
            import numpy as np
            
            # Load audio
            sample_rate, audio_data = read(audio_file)
            
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32) / 32767
            
            # Process
            processed_audio, metadata = self.audio_processor.process_audio(
                audio_data,
                filter_type=filter_type,
                apply_spectral_subtraction=True
            )
            
            # Save processed audio
            if save_processed:
                processed_file = audio_file.replace('.wav', '_filtered.wav')
                processed_int16 = np.int16(processed_audio * 32767)
                write(processed_file, sample_rate, processed_int16)
                metadata['processed_file'] = processed_file
            
            return True, metadata
        
        except Exception as e:
            return False, {"error": str(e)}
    
    # ===================== TRANSCRIPTION ========================
    def transcribe_audio(self, audio_file: str, language: str = "en") -> Tuple[bool, str, float]:
        """
        Transcribe audio using Whisper with confidence score.
        
        Returns:
            Tuple of (success, transcription, confidence_score)
        """
        if not HAS_WHISPER:
            return False, "Whisper not installed", 0.0
        
        if not os.path.exists(audio_file):
            return False, f"Audio file not found: {audio_file}", 0.0
        
        try:
            print("Transcribing audio with Whisper...")
            model = whisper.load_model("base")
            result = model.transcribe(audio_file, language=language)
            
            transcription = result.get("text", "")
            # Estimate confidence from segments
            segments = result.get("segments", [])
            avg_confidence = sum(seg.get("confidence", 0.8) for seg in segments) / len(segments) if segments else 0.8
            
            # Cleanup
            del model
            gc.collect()
            
            return True, transcription, float(avg_confidence)
        
        except Exception as e:
            return False, f"Transcription error: {str(e)}", 0.0
    
    # ===================== LLM SOAP GENERATION ========================
    def generate_soap_with_llm(self, transcript: str, language: str = "en") -> Tuple[bool, Dict]:
        """Generate SOAP note using BioMistral via Ollama with full multilingual support.

        Pipeline:
          1. If language != 'en', translate transcript → English  (LLM always sees English)
          2. Call BioMistral to generate a structured SOAP note in English
          3. Refine ICD-10 codes via NLM API
          4. If language != 'en', translate SOAP fields back to chosen language
          5. Return both English and localized copies for dual-storage in the database
        """
        import re
        import json
        from datetime import datetime
        from translations import translate_to_english, translate_from_english

        soap_json = {}
        is_multilingual = language not in ("en", "")

        # ── Step 1: Translate transcript to English for the LLM ────────────────
        transcript_en = translate_to_english(transcript, language) if is_multilingual else transcript

        if HAS_OLLAMA:
            try:
                system_prompt = (
                    "You are BioMistral, an expert clinical AI scribe trained on biomedical literature. "
                    "You will receive a clinical encounter transcript in English. "
                    "Produce a structured SOAP note. "
                    "Return ONLY valid JSON with these exact keys: "
                    "subjective (string), objective (string), assessment (string), plan (string), "
                    "chief_complaint (string), icd10_codes (array of strings). "
                    "Be concise, medically accurate, and do NOT include markdown, code fences, or extra commentary."
                )

                response = ollama.generate(
                    model='cniongolo/biomistral:latest',
                    system=system_prompt,
                    prompt=f"Clinical Transcript (English):\n{transcript_en}\n\nReturn ONLY valid JSON:",
                    format='json',
                    options={'temperature': 0.1, 'num_predict': 700}
                )

                raw = response.get('response', '{}')
                soap_json = json.loads(raw)
                soap_json['timestamp'] = datetime.now().isoformat()
                soap_json['source'] = 'biomistral'
                soap_json['language'] = language

                # ── Step 3: Refine ICD-10 codes ────────────────────────────────
                if soap_json.get('icd10_codes'):
                    soap_json['icd10_codes'] = self.refine_icd10_codes(soap_json['icd10_codes'])

                # ── Step 4: Store English SOAP as canonical copy ────────────────
                soap_json['subjective_en']   = soap_json.get('subjective', '')
                soap_json['objective_en']    = soap_json.get('objective', '')
                soap_json['assessment_en']   = soap_json.get('assessment', '')
                soap_json['plan_en']         = soap_json.get('plan', '')
                soap_json['chief_complaint_en'] = soap_json.get('chief_complaint', '')

                # ── Step 5: Translate output back to clinician's language ────────
                if is_multilingual:
                    fields_to_localize = ['subjective', 'objective', 'assessment', 'plan', 'chief_complaint']
                    for field in fields_to_localize:
                        en_text = soap_json.get(field, '')
                        if en_text:
                            soap_json[field] = translate_from_english(en_text, language)
                            soap_json[f'{field}_localized'] = soap_json[field]

                return True, soap_json

            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"Ollama/BioMistral error: {e}")

        # Fallback: Pattern-based SOAP generation (still respects multilingual)
        try:
            from datetime import datetime as _dt
            soap_json = self._parse_soap_from_transcript(transcript_en)
            soap_json['timestamp'] = _dt.now().isoformat()
            soap_json['source'] = 'pattern_matching_fallback'
            soap_json['language'] = language

            if soap_json.get('icd10_codes'):
                soap_json['icd10_codes'] = self.refine_icd10_codes(soap_json['icd10_codes'])

            # Store EN copies
            for field in ['subjective', 'objective', 'assessment', 'plan', 'chief_complaint']:
                soap_json[f'{field}_en'] = soap_json.get(field, '')

            # Translate to user's language
            if is_multilingual:
                for field in ['subjective', 'objective', 'assessment', 'plan', 'chief_complaint']:
                    en_text = soap_json.get(field, '')
                    if en_text:
                        soap_json[field] = translate_from_english(en_text, language)
                        soap_json[f'{field}_localized'] = soap_json[field]

            return True, soap_json
        except Exception as e:
            return False, {"error": f"SOAP generation failed: {str(e)}"}


    def refine_icd10_codes(self, codes: List[str]) -> List[Dict[str, str]]:
        """Refine raw ICD-10 codes by adding descriptions from NLM API (simulated or real)."""
        refined = []
        for code in codes:
            # Clean code
            clean_code = code.strip().upper()
            if not clean_code: continue
            
            # Check internal mapping first
            desc = ""
            for name, icd in self.icd10_mapping.items():
                if icd == clean_code:
                    desc = name.capitalize()
                    break
            
            # If not in internal mapping, we'd normally call the API
            # For this enhancement, we simulate the enrich or use a generic title
            if not desc:
                # Try a quick call to NLM (simulated via local proxy logic)
                try:
                    # Logic matches api.py proxy for ICD-10 search
                    search_url = f"https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?terms={clean_code}"
                    r = requests.get(search_url, timeout=2)
                    data = r.json()
                    if data and len(data) > 3 and data[3]:
                         desc = data[3][0][1] # First match's description
                except:
                    desc = "Clinical Condition"

            refined.append({
                "icd10_code": clean_code,
                "description": desc or "Official ICD-10 Diagnosis"
            })
        return refined

    def generate_patient_education(self, soap: Dict, language: str = "en") -> str:
        """Generate a patient-friendly handout from a SOAP note using BioMistral.
        
        Always generates the handout in English (for clinical quality), then translates
        it back to the clinician's / patient's chosen language.
        """
        from translations import translate_from_english

        # Use English versions of SOAP fields if available (canonical clinical copy)
        subjective = soap.get('subjective_en') or soap.get('subjective', '')
        assessment = soap.get('assessment_en') or soap.get('assessment', '')
        plan = soap.get('plan_en') or soap.get('plan', '')
        chief_complaint = soap.get('chief_complaint_en') or soap.get('chief_complaint', '')

        if not HAS_OLLAMA:
            _doctor_instr = "Follow your doctor's instructions."
            fallback = (
                f"Condition: {assessment or 'See clinical notes.'}"
                + "\n\n"
                + f"Follow-up plan: {plan or _doctor_instr}"
                + "\n\nPlease call your doctor if symptoms worsen."
            )
            return translate_from_english(fallback, language) if language != "en" else fallback

        try:
            prompt = (
                f"Based on this SOAP note, generate a friendly, patient-ready summary in simple English. "
                f"Include: 1. What we found, 2. What you should do, 3. When to call the doctor.\n\n"
                f"Chief Complaint: {chief_complaint}\n"
                f"Subjective: {subjective}\n"
                f"Assessment: {assessment}\n"
                f"Plan: {plan}\n\n"
                f"Patient Instruction:"
            )

            response = ollama.generate(
                model='cniongolo/biomistral:latest',
                prompt=prompt,
                options={'temperature': 0.5, 'num_predict': 500}
            )
            education_en = response.get('response', '').strip()
            if not education_en:
                education_en = "Unable to generate instructions at this time."

            # Translate back to clinician/patient language
            return translate_from_english(education_en, language) if language != "en" else education_en

        except Exception as e:
            return f"Error generating instructions: {str(e)}"

    
    def _parse_soap_from_transcript(self, transcript: str) -> Dict:
        """Extract SOAP components from clinical transcript using pattern matching."""
        import re
        from datetime import datetime
        
        # Case-insensitive cleaning
        text = transcript.lower()
        
        # Extract or create each component
        subjective = self._extract_section(text, r'(chief complaint|cc|cc:|subjective|history)', 'objective')
        if not subjective:
            subjective = transcript[:min(500, len(transcript))]
        
        objective = self._extract_section(text, r'(objective|findings|vitals|bp|heart rate|temperature|pulse)', 'assessment')
        if not objective:
            # Look for vital signs pattern
            vitals = re.findall(r'(?:bp|heart rate|temp|weight|height)[:\s]*[\d\./]+', text)
            if vitals:
                objective = " | ".join(vitals)
            else:
                objective = "Physical examination findings not clearly documented in transcript"
        
        assessment = self._extract_section(text, r'(assessment|diagnosis|impression|dx:|dx)', 'plan')
        if not assessment:
            # Look for disease keywords
            diseases = re.findall(r'(pneumonia|bronchitis|asthma|hypertension|diabetes|fever|cough|cold|flu)', text)
            if diseases:
                assessment = f"Provisional diagnosis: {', '.join(set(diseases))}"
            else:
                assessment = "Assessment pending detailed investigation"
        
        plan = self._extract_section(text, r'(plan|treatment|medication|therapy|follow.?up)', '')
        if not plan:
            plan = "Continue monitoring. Follow-up as needed. Return if symptoms worsen."
        
        # Extract chief complaint
        cc_match = re.search(r'(chief complaint|cc|presenting complaint)[:\s]+([^\.!\n]*)', text)
        chief_complaint = cc_match.group(2).strip() if cc_match else "Not documented"
        
        # Extract or infer ICD-10 codes
        icd10_codes = self._extract_icd10_codes(text)
        
        return {
            "chief_complaint": chief_complaint.title(),
            "subjective": subjective.capitalize(),
            "objective": objective.capitalize(),
            "assessment": assessment.capitalize(),
            "plan": plan.capitalize(),
            "icd10_codes": icd10_codes,
            "confidence": 0.75  # Pattern matching is less confident
        }
    
    def _extract_section(self, text: str, start_pattern: str, end_section: str) -> str:
        """Extract text between section markers."""
        import re
        match = re.search(start_pattern, text)
        if not match:
            return ""
        
        start_pos = match.end()
        
        # Find end of section
        if end_section:
            end_match = re.search(end_section, text[start_pos:])
            if end_match:
                end_pos = start_pos + end_match.start()
            else:
                end_pos = min(start_pos + 500, len(text))
        else:
            end_pos = min(start_pos + 500, len(text))
        
        section_text = text[start_pos:end_pos]
        # Clean up
        section_text = re.sub(r'[^\w\s.,\-/()]', '', section_text)
        return section_text.strip()
    
    def _extract_icd10_codes(self, text: str) -> list:
        """Extract or infer ICD-10 codes from transcript."""
        import re
        
        # Common disease to ICD-10 mapping
        disease_icd10_map = {
            'pneumonia': 'J18.9',
            'bronchitis': 'J20.9',
            'asthma': 'J45.9',
            'hypertension': 'I10',
            'diabetes': 'E11.9',
            'fever': 'R50.9',
            'cough': 'R05.9',
            'cold': 'J00',
            'flu': 'J11.1',
            'infection': 'A49.9',
            'gastritis': 'K29.7',
            'rhinitis': 'J30.9',
            'sinusitis': 'J32.9',
            'urinary tract infection': 'N39.0',
            'uti': 'N39.0',
            'headache': 'R51.9',
            'migraine': 'G43.9',
            'anxiety': 'F41.1',
            'depression': 'F32.9',
            'hypertension': 'I10',
            'high blood pressure': 'I10'
        }
        
        icd10_list = []
        for disease, code in disease_icd10_map.items():
            if disease in text.lower():
                icd10_list.append(code)
        
        # Default if nothing found
        if not icd10_list:
            icd10_list = ['Z00.00']  # General medical examination
        
        return list(set(icd10_list))[:5]  # Return up to 5 unique codes
    
    # ===================== DATABASE OPERATIONS =====================
    def create_patient(
        self,
        name: str,
        age: int,
        gender: str,
        phone: str = "",
        email: str = "",
        blood_group: str = "",
        **kwargs
    ) -> Tuple[bool, str]:
        """Create new patient record in SQL database."""
        try:
            patient = Patient(
                patient_id=str(uuid.uuid4())[:8],
                name=name,
                age=age,
                gender=gender,
                phone=phone,
                email=email,
                blood_group=blood_group,
                chronic_conditions=kwargs.get('chronic_conditions', []),
                allergies=kwargs.get('allergies', []),
                medications=kwargs.get('medications', [])
            )
            
            self.session.add(patient)
            self.session.commit()
            
            return True, patient.patient_id
        
        except Exception as e:
            self.session.rollback()
            return False, f"Error creating patient: {str(e)}"
    
    def create_visit(
        self,
        patient_id: str,
        clinician_id: str,
        chief_complaint: str,
        **kwargs
    ) -> Tuple[bool, str]:
        """Create new visit record."""
        try:
            visit = Visit(
                visit_id=str(uuid.uuid4())[:8],
                patient_id=patient_id,
                clinician_id=clinician_id,
                chief_complaint=chief_complaint,
                visit_type=kwargs.get('visit_type', 'OP'),
                temperature=kwargs.get('temperature'),
                blood_pressure_systolic=kwargs.get('bp_systolic'),
                blood_pressure_diastolic=kwargs.get('bp_diastolic'),
                heart_rate=kwargs.get('heart_rate'),
                oxygen_saturation=kwargs.get('oxygen_saturation')
            )
            
            self.session.add(visit)
            self.session.commit()
            
            return True, visit.visit_id
        
        except Exception as e:
            self.session.rollback()
            return False, f"Error creating visit: {str(e)}"
    
    def save_audio_recording(
        self,
        visit_id: str,
        file_path: str,
        transcript: str,
        noise_level: float,
        filter_type: str
    ) -> Tuple[bool, str]:
        """Save audio recording metadata to database."""
        try:
            from scipy.io.wavfile import read
            
            # Get file info
            sample_rate_actual, audio_data = read(file_path)
            file_size = os.path.getsize(file_path)
            duration = len(audio_data) / sample_rate_actual
            
            audio_rec = AudioRecording(
                audio_id=str(uuid.uuid4())[:8],
                visit_id=visit_id,
                file_path=file_path,
                file_size=file_size,
                duration=duration,
                sample_rate=sample_rate_actual,
                channels=1,
                noise_level=noise_level,
                filter_type=filter_type,
                raw_transcript=transcript
            )
            
            self.session.add(audio_rec)
            self.session.commit()
            
            return True, audio_rec.audio_id
        
        except Exception as e:
            self.session.rollback()
            return False, f"Error saving audio record: {str(e)}"
    
    def save_soap_note(
        self,
        visit_id: str,
        soap_data: Dict
    ) -> Tuple[bool, str]:
        """Save SOAP note to database.
        
        Always stores English as primary content (clinical interoperability).
        Localized versions are stored in *_localized columns.
        """
        try:
            lang = soap_data.get('language', 'en')
            is_multilingual = lang not in ('en', '')

            # Primary columns always hold the English version for clinical integrity
            note = SoapNote(
                note_id=str(uuid.uuid4())[:8],
                visit_id=visit_id,
                subjective=soap_data.get('subjective_en') or soap_data.get('subjective', ''),
                objective=soap_data.get('objective_en') or soap_data.get('objective', ''),
                assessment=soap_data.get('assessment_en') or soap_data.get('assessment', ''),
                plan=soap_data.get('plan_en') or soap_data.get('plan', ''),
                icd10_codes=soap_data.get('icd10_codes', []),
                abdm_compliant=True,
                language=lang,
                subjective_localized=soap_data.get('subjective_localized') if is_multilingual else None,
                objective_localized=soap_data.get('objective_localized') if is_multilingual else None,
                assessment_localized=soap_data.get('assessment_localized') if is_multilingual else None,
                plan_localized=soap_data.get('plan_localized') if is_multilingual else None,
            )

            self.session.add(note)
            self.session.commit()

            return True, note.note_id

        except Exception as e:
            self.session.rollback()
            return False, f"Error saving SOAP note: {str(e)}"

    def add_prescription(
        self,
        visit_id: str,
        patient_id: str,
        medicine_name: str,
        dosage: str,
        frequency: str,
        duration: str,
        route: str = 'oral'
    ) -> Tuple[bool, str]:
        """Add prescription to database."""
        try:
            prescription = Prescription(
                prescription_id=str(uuid.uuid4())[:8],
                visit_id=visit_id,
                patient_id=patient_id,
                medicine_name=medicine_name,
                dosage=dosage,
                frequency=frequency,
                duration=duration,
                route=route
            )
            
            self.session.add(prescription)
            self.session.commit()
            
            return True, prescription.prescription_id
        
        except Exception as e:
            self.session.rollback()
            return False, f"Error adding prescription: {str(e)}"
    
    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Retrieve patient record."""
        try:
            patient = self.session.query(Patient).filter(Patient.patient_id == patient_id).first()
            return patient.to_dict() if patient else None
        except Exception as e:
            print(f"Error retrieving patient: {e}")
            return None
    
    def get_patient_visits(self, patient_id: str) -> List[Dict]:
        """Get all visits for a patient."""
        try:
            visits = self.session.query(Visit).filter(Visit.patient_id == patient_id).all()
            return [v.to_dict() for v in visits]
        except Exception as e:
            print(f"Error retrieving visits: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            total_patients = self.session.query(Patient).count()
            total_visits = self.session.query(Visit).count()
            total_notes = self.session.query(SoapNote).count()
            total_recordings = self.session.query(AudioRecording).count()
            
            return {
                "total_patients": total_patients,
                "total_visits": total_visits,
                "total_soap_notes": total_notes,
                "total_audio_recordings": total_recordings,
                "database_type": "SQLite/PostgreSQL (SQLAlchemy)"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def close(self):
        """Close database session."""
        if self.session:
            self.session.close()
