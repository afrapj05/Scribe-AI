'use client';
import { useEffect, useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Languages, Search, Download, Trash2, AlertCircle, CheckCircle, Mic, MicOff, Send, Info, ScanLine, Upload, X, Pill, FlaskConical, Building2, Calendar, ChevronDown, ChevronUp, Copy, FileText, MessageSquare } from 'lucide-react';
import AppLayout from '../../components/AppLayout';
import { Scriber } from '../../lib/api';
import api from '../../lib/api';

/* ── Scanner types ── */
interface ScanMed { name: string; dose?: string; frequency?: string; duration?: string; route?: string; }
interface ScanLab { test: string; value: string; unit?: string; reference_range?: string; flag?: 'HIGH' | 'LOW' | 'NORMAL' | null; }
interface ScanResult {
    document_type: string; patient_name?: string; patient_age?: string; date?: string;
    doctor_name?: string; hospital?: string; diagnoses?: string[];
    medications?: ScanMed[]; lab_values?: ScanLab[];
    clinical_notes?: string; full_summary?: string; model?: string; filename?: string;
}

interface SoapNote {
    subjective?: string; objective?: string;
    assessment?: string; plan?: string;
    chief_complaint?: string;
    icd10_codes?: Array<{ icd10_code: string; description: string }>;
    source?: string; timestamp?: string; language?: string;
    subjective_en?: string; objective_en?: string;
    assessment_en?: string; plan_en?: string;
    subjective_localized?: string; objective_localized?: string;
    assessment_localized?: string; plan_localized?: string;
}

const DOC_COLORS: Record<string, { bg: string; color: string; border: string }> = {
    Prescription: { bg: '#eef6ff', color: '#1d4ed8', border: '#bfdbfe' },
    'Lab Report': { bg: '#f0fdf4', color: '#15803d', border: '#86efac' },
    'Discharge Summary': { bg: '#fdf4ff', color: '#7c3aed', border: '#d8b4fe' },
    'Radiology Report': { bg: '#fffbeb', color: '#92400e', border: '#fcd34d' },
    Other: { bg: '#f8fafc', color: '#475569', border: '#cbd5e1' },
};
const flagColor = (f?: string | null) => f === 'HIGH' ? '#b91c1c' : f === 'LOW' ? '#1d4ed8' : '#15803d';
const flagBg = (f?: string | null) => f === 'HIGH' ? '#fee2e2' : f === 'LOW' ? '#dbeafe' : '#dcfce7';

const SPEECH_LANGS = [
    { code: 'en-IN', label: 'English (India)', native: 'English' },
    { code: 'hi-IN', label: 'Hindi', native: 'हिन्दी' },
    { code: 'ta-IN', label: 'Tamil', native: 'தமிழ்' },
    { code: 'te-IN', label: 'Telugu', native: 'తెలుగు' },
    { code: 'ml-IN', label: 'Malayalam', native: 'മലയാളം' },
    { code: 'kn-IN', label: 'Kannada', native: 'ಕನ್ನಡ' },
    { code: 'mr-IN', label: 'Marathi', native: 'मराठी' },
    { code: 'bn-IN', label: 'Bengali', native: 'বাংলা' },
    { code: 'gu-IN', label: 'Gujarati', native: 'ગુજરાતી' },
    { code: 'pa-IN', label: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
];

export default function ScriberPage() {
    // ── tab state ──
    const [scriberTab, setScriberTab] = useState<'soap' | 'scan'>('soap');

    // ── SOAP state ──
    const [patientId, setPatientId] = useState('');
    const [complaint, setComplaint] = useState('');
    const [finalText, setFinalText] = useState('');
    const [interim, setInterim] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [speechLang, setSpeechLang] = useState('en-IN');
    const [loading, setLoading] = useState(false);
    const [soap, setSoap] = useState<SoapNote | null>(null);
    const [error, setError] = useState('');
    const [savedInfo, setSavedInfo] = useState('');
    const [rxQuery, setRxQuery] = useState('');
    const [rxResults, setRxResults] = useState<{ name: string; rxcui: string }[]>([]);
    const [rxLoading, setRxLoading] = useState(false);
    const [micStatus, setMicStatus] = useState<'unknown' | 'granted' | 'denied'>('unknown');
    const [viewMode, setViewMode] = useState<'clinician' | 'patient'>('clinician');
    const [patientEdu, setPatientEdu] = useState('');
    const [eduLinks, setEduLinks] = useState<{ condition: string; url: string }[]>([]);
    const [eduLoading, setEduLoading] = useState(false);
    const [showLocalized, setShowLocalized] = useState(true);

    // ── Scanner state ──
    const [scanDragOver, setScanDragOver] = useState(false);
    const [scanFile, setScanFile] = useState<File | null>(null);
    const [scanPreview, setScanPreview] = useState<string | null>(null);
    const [scanning, setScanning] = useState(false);
    const [scanResult, setScanResult] = useState<ScanResult | null>(null);
    const [scanError, setScanError] = useState('');
    const [showRawJson, setShowRawJson] = useState(false);
    const [copiedJson, setCopiedJson] = useState(false);
    const [pdfLoading, setPdfLoading] = useState(false);
    const [waLoading, setWaLoading] = useState(false);
    const scanFileRef = useRef<HTMLInputElement>(null);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognitionRef = useRef<any>(null);
    const boxRef = useRef<HTMLDivElement>(null);

    // Check mic permission on mount
    useEffect(() => {
        if (navigator.permissions) {
            navigator.permissions.query({ name: 'microphone' as PermissionName })
                .then(p => {
                    setMicStatus(p.state as 'unknown' | 'granted' | 'denied');
                    p.onchange = () => setMicStatus(p.state as 'unknown' | 'granted' | 'denied');
                }).catch(() => { });
        }
    }, []);

    useEffect(() => {
        if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight;
    }, [finalText, interim]);

    // RxNorm debounce
    useEffect(() => {
        if (!rxQuery.trim()) { setRxResults([]); return; }
        const id = setTimeout(async () => {
            setRxLoading(true);
            try {
                const r = await api.get('/api/public/rxnorm', { params: { q: rxQuery } });
                setRxResults((r.data.results || []).slice(0, 8));
            } catch { setRxResults([]); }
            finally { setRxLoading(false); }
        }, 380);
        return () => clearTimeout(id);
    }, [rxQuery]);

    const requestMicAndRecord = useCallback(async () => {
        setError('');
        // Explicitly request mic permission first — this triggers the browser prompt
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(t => t.stop()); // we only needed permission
            setMicStatus('granted');
        } catch {
            setMicStatus('denied');
            setError('Microphone access denied. Click the lock icon in your browser address bar → Allow microphone → refresh the page.');
            return;
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const w = window as any;
        const SR = w.SpeechRecognition || w.webkitSpeechRecognition;
        if (!SR) {
            setError('Web Speech API not supported. Please use Google Chrome or Microsoft Edge.');
            return;
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const rec: any = new SR();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = speechLang;
        rec.maxAlternatives = 1;

        rec.onresult = (e: SpeechRecognitionEvent) => {
            let interimBuf = '';
            let finalBuf = '';
            for (let i = e.resultIndex; i < e.results.length; i++) {
                const t = e.results[i][0].transcript;
                if (e.results[i].isFinal) finalBuf += t + ' ';
                else interimBuf += t;
            }
            if (finalBuf) setFinalText(p => p + finalBuf);
            setInterim(interimBuf);
        };
        rec.onerror = (e: SpeechRecognitionErrorEvent) => {
            if (e.error === 'not-allowed') {
                setMicStatus('denied');
                setError('Microphone blocked. Click the lock icon in your browser address bar → Allow microphone access.');
            } else if (e.error !== 'aborted') {
                setError(`Speech recognition error: ${e.error}`);
            }
        };
        rec.onend = () => { setIsRecording(false); setInterim(''); };

        rec.start();
        recognitionRef.current = rec;
        setIsRecording(true);
    }, [speechLang]);

    const stopRecording = useCallback(() => {
        recognitionRef.current?.stop();
        setIsRecording(false);
    }, []);

    const generateSoap = async () => {
        const transcript = (finalText + ' ' + interim).trim();
        if (!transcript) { setError('Please record or type a transcript first.'); return; }
        stopRecording();
        setLoading(true); setError(''); setSoap(null); setSavedInfo('');
        setPatientEdu(''); setEduLinks([]); setShowLocalized(true);
        // Derive backend language code from Web Speech lang (e.g. 'hi-IN' → 'hi')
        const backendLang = speechLang.split('-')[0];
        try {
            const res = await Scriber.generateSoap({
                patient_id: patientId || 'demo',
                chief_complaint: complaint || 'Not specified',
                transcript,
                language: backendLang,
            });
            setSoap(res.soap);
            if (res.visit_id) setSavedInfo(`Saved · Visit ${res.visit_id.slice(0, 8)}…`);
        } catch {
            setError('SOAP generation failed. Ensure FastAPI is running on port 8000 and Ollama has biomistral.');
        } finally { setLoading(false); }
    };

    const generateEducation = async () => {
        if (!soap) return;
        const backendLang = speechLang.split('-')[0];
        setEduLoading(true); setViewMode('patient');
        try {
            const res = await api.post('/api/scriber/patient-education', { soap, language: backendLang });
            setPatientEdu(res.data.education);
            setEduLinks(res.data.links || []);
        } catch {
            setError('Failed to generate patient instructions.');
        } finally { setEduLoading(false); }
    };

    const downloadSoap = () => {
        if (!soap) return;
        const icd = (soap.icd10_codes || []).map(c => typeof c === 'string' ? c : (c as Record<string, string>).icd10_code || '').join(', ');
        const txt = [
            '═══════════════════════════════════',
            '   ScribeAI SOAP NOTE',
            '═══════════════════════════════════',
            `Date: ${new Date().toLocaleString('en-IN')}`,
            `Patient ID: ${patientId || 'N/A'}`,
            `Chief Complaint: ${soap.chief_complaint || complaint}`,
            `ICD-10 Codes: ${icd}`,
            `AI Model: ${soap.source || 'phi3:mini'}`,
            '───────────────────────────────────',
            '', 'SUBJECTIVE:', soap.subjective || '',
            '', 'OBJECTIVE:', soap.objective || '',
            '', 'ASSESSMENT:', soap.assessment || '',
            '', 'PLAN:', soap.plan || '',
        ].join('\n');
        const a = Object.assign(document.createElement('a'), {
            href: URL.createObjectURL(new Blob([txt], { type: 'text/plain' })),
            download: `SOAP_${patientId || 'patient'}_${Date.now()}.txt`,
        });
        a.click();
    };

    const downloadPdf = async () => {
        if (!soap) return;
        setPdfLoading(true);
        try {
            const res = await api.post('/api/report/pdf', {
                soap,
                patient: { name: patientId || 'Patient', patient_id: patientId || 'N/A', age: 'N/A', gender: 'N/A' },
                visit: { chief_complaint: soap.chief_complaint || complaint, department: 'Cardiology' }
            }, { responseType: 'blob' });

            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `Silverline_Report_${patientId || 'Patient'}_${Date.now()}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch {
            setError('Failed to generate PDF report.');
        } finally { setPdfLoading(false); }
    };

    const sendWhatsApp = async () => {
        if (!soap) return;
        const phone = prompt('Enter WhatsApp Number (e.g. +918489179077):', '+918489179077');
        if (!phone) return;
        setWaLoading(true);
        try {
            await api.post('/api/notify/whatsapp', {
                to_number: phone,
                patient_name: patientId || 'Patient',
                appointment_date: new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'numeric' }),
                appointment_time: new Date().toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' })
            });
            setSavedInfo('WhatsApp Sent!');
            setTimeout(() => setSavedInfo(''), 3000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to send WhatsApp.');
        } finally { setWaLoading(false); }
    };

    // ── Scanner helpers ──
    const handleScanFile = useCallback((file: File) => {
        if (!file.type.startsWith('image/')) { setScanError('Please upload an image file (JPG, PNG, WebP).'); return; }
        setScanFile(file); setScanError(''); setScanResult(null);
        const reader = new FileReader();
        reader.onload = e => setScanPreview(e.target?.result as string);
        reader.readAsDataURL(file);
    }, []);

    const clearScan = () => { setScanFile(null); setScanPreview(null); setScanResult(null); setScanError(''); };

    const scanImage = async () => {
        if (!scanFile) return;
        setScanning(true); setScanError(''); setScanResult(null);
        const form = new FormData();
        form.append('file', scanFile);
        try {
            const res = await api.post('/api/scan-report', form, { headers: { 'Content-Type': 'multipart/form-data' } });
            setScanResult(res.data);
        } catch (err: unknown) {
            setScanError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Scan failed. Ensure Ollama is running with qwen2.5vl:3b.');
        } finally { setScanning(false); }
    };

    const downloadScanResult = () => {
        if (!scanResult) return;
        const lines = [
            'ScribeAI — Medical Document Analysis',
            `Scanned: ${new Date().toLocaleString('en-IN')}`,
            `File: ${scanResult.filename || 'unknown'}`,
            '═══════════════════════════════════════',
            `Type: ${scanResult.document_type}`,
            `Patient: ${scanResult.patient_name || 'N/A'} | Age: ${scanResult.patient_age || 'N/A'}`,
            `Date: ${scanResult.date || 'N/A'} | Doctor: ${scanResult.doctor_name || 'N/A'}`,
            `Hospital: ${scanResult.hospital || 'N/A'}`,
            '───────────────────────────────────────',
            'DIAGNOSES:', ...(scanResult.diagnoses || []).map(d => `  • ${d}`),
            '', 'MEDICATIONS:', ...(scanResult.medications || []).map(m => `  • ${m.name}${m.dose ? ' — ' + m.dose : ''}${m.frequency ? ' | ' + m.frequency : ''}`),
            '', 'LAB VALUES:', ...(scanResult.lab_values || []).map(l => `  • ${l.test}: ${l.value}${l.unit ? ' ' + l.unit : ''}${l.flag ? ' [' + l.flag + ']' : ''}`),
            '', `NOTES: ${scanResult.clinical_notes || 'None'}`,
            '', 'SUMMARY:', scanResult.full_summary || '',
        ].join('\n');
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([lines], { type: 'text/plain' }));
        a.download = 'scan_report.txt'; a.click();
    };

    const currentLang = SPEECH_LANGS.find(l => l.code === speechLang);

    return (
        <AppLayout>
            {/* Header */}
            <div className="page-header">
                <div>
                    <p className="breadcrumb">Scriber AI &rsaquo; {scriberTab === 'soap' ? 'New Note' : 'Scan Report'}</p>
                    <h1 className="page-title">Scriber AI</h1>
                    <p className="page-subtitle">Ambient speech-to-SOAP documentation · BioMistral · Fully local AI</p>
                </div>
                {/* Language selector — only shown for SOAP tab */}
                {scriberTab === 'soap' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', background: '#fff', border: '1px solid var(--border)', borderRadius: 12, padding: '0.5rem 0.875rem', boxShadow: 'var(--shadow-sm)' }}>
                        <Languages size={15} color="var(--blue-500)" />
                        <select className="input" style={{ border: 'none', padding: 0, background: 'transparent', width: 'auto', fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.85rem' }}
                            value={speechLang} onChange={e => setSpeechLang(e.target.value)}>
                            {SPEECH_LANGS.map(l => <option key={l.code} value={l.code}>{l.native} — {l.label}</option>)}
                        </select>
                    </div>
                )}
            </div>

            {/* ── Tab bar ── */}
            <div style={{ display: 'flex', gap: '0.25rem', background: '#fff', border: '1px solid var(--border)', borderRadius: 14, padding: '0.3rem', marginBottom: '1.5rem', boxShadow: 'var(--shadow-sm)', width: 'fit-content' }}>
                <button
                    onClick={() => setScriberTab('soap')}
                    style={{
                        display: 'flex', alignItems: 'center', gap: '0.45rem',
                        padding: '0.55rem 1.1rem', borderRadius: 10, border: 'none', cursor: 'pointer',
                        fontSize: '0.85rem', fontWeight: 600, fontFamily: 'inherit',
                        background: scriberTab === 'soap' ? 'var(--grad-blue)' : 'transparent',
                        color: scriberTab === 'soap' ? '#fff' : 'var(--text-secondary)',
                        boxShadow: scriberTab === 'soap' ? '0 2px 8px rgba(0,87,184,0.25)' : 'none',
                        transition: 'all 0.18s',
                    }}
                >
                    <Mic size={14} /> SOAP Generator
                </button>
                <button
                    onClick={() => setScriberTab('scan')}
                    style={{
                        display: 'flex', alignItems: 'center', gap: '0.45rem',
                        padding: '0.55rem 1.1rem', borderRadius: 10, border: 'none', cursor: 'pointer',
                        fontSize: '0.85rem', fontWeight: 600, fontFamily: 'inherit',
                        background: scriberTab === 'scan' ? 'linear-gradient(135deg, #006689 0%, #0891b2 100%)' : 'transparent',
                        color: scriberTab === 'scan' ? '#fff' : 'var(--text-secondary)',
                        boxShadow: scriberTab === 'scan' ? '0 2px 8px rgba(0,102,137,0.25)' : 'none',
                        transition: 'all 0.18s',
                    }}
                >
                    <ScanLine size={14} /> Scan Report
                    <span style={{ fontSize: '0.65rem', background: 'rgba(255,255,255,0.25)', padding: '0.1rem 0.4rem', borderRadius: 999 }}>qwen2.5vl</span>
                </button>
            </div>
            <AnimatePresence mode="wait">
                {scriberTab === 'soap' ? (
                    <motion.div key="soap-tab" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>

                        {/* Mic permission banner */}
                        {micStatus === 'denied' && (
                            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
                                className="alert alert-error" style={{ marginBottom: '1.25rem', borderRadius: 10 }}>
                                <AlertCircle size={16} style={{ flexShrink: 0 }} />
                                <div>
                                    <strong>Microphone Blocked.</strong> Click the lock icon in the browser address bar → Site settings → Allow Microphone → Refresh.
                                </div>
                            </motion.div>
                        )}
                        {micStatus === 'unknown' && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                className="alert alert-info" style={{ marginBottom: '1.25rem', borderRadius: 10 }}>
                                <Info size={16} style={{ flexShrink: 0 }} />
                                Click <strong>Start Recording</strong> — your browser will ask for microphone permission. Click <em>Allow</em>.
                            </motion.div>
                        )}

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', alignItems: 'start' }}>
                            {/* ─── LEFT PANEL ─── */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

                                {/* Visit details card */}
                                <div className="card card-blue" style={{ padding: '1.375rem' }}>
                                    <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ width: 22, height: 22, borderRadius: 6, background: 'var(--blue-50)', border: '1px solid #c7ddf7', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>01</span>
                                        Visit Details
                                    </h3>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }}>
                                        <div className="form-group">
                                            <label className="form-label">Patient ID</label>
                                            <input className="input" placeholder="e.g. PAT-001" value={patientId} onChange={e => setPatientId(e.target.value)} />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Chief Complaint</label>
                                            <input className="input" placeholder="e.g. chest pain" value={complaint} onChange={e => setComplaint(e.target.value)} />
                                        </div>
                                    </div>
                                </div>

                                {/* Recording card */}
                                <div className="card card-red">
                                    <div style={{ padding: '1.375rem' }}>
                                        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'space-between' }}>
                                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <span style={{ width: 22, height: 22, borderRadius: 6, background: '#fff0f2', border: '1px solid #fca5a5', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', color: 'var(--red-600)' }}>02</span>
                                                {isRecording ? (
                                                    <span className="rec-indicator"><span className="rec-dot" />REC · {currentLang?.native}</span>
                                                ) : 'Transcript'}
                                            </span>
                                            {(finalText || interim) && (
                                                <button className="btn btn-ghost btn-sm" onClick={() => { setFinalText(''); setInterim(''); setSoap(null); setSavedInfo(''); }}>
                                                    <Trash2 size={12} /> Clear
                                                </button>
                                            )}
                                        </h3>

                                        {/* Live transcript display */}
                                        <div ref={boxRef} className={`transcript-area${isRecording ? ' recording' : ''}`}>
                                            {!finalText && !interim ? (
                                                <span className="transcript-placeholder">
                                                    {isRecording
                                                        ? `Listening in ${currentLang?.label}… speak clearly`
                                                        : `Press Start Recording to capture in ${currentLang?.native}. You can also type below.`}
                                                </span>
                                            ) : (
                                                <>
                                                    {finalText}
                                                    {interim && <span className="transcript-interim">{interim}</span>}
                                                    {isRecording && <span className="cursor-blink" />}
                                                </>
                                            )}
                                        </div>

                                        {/* Manual input */}
                                        <div className="form-group" style={{ marginTop: '0.875rem' }}>
                                            <label className="form-label">Manual / Paste Transcript</label>
                                            <textarea className="input" rows={3} placeholder="Or paste a transcript here…"
                                                value={finalText} onChange={e => setFinalText(e.target.value)} />
                                        </div>

                                        {/* Buttons */}
                                        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                                            {!isRecording ? (
                                                <motion.button className="btn btn-danger" style={{ flex: 1, justifyContent: 'center' }}
                                                    onClick={requestMicAndRecord} whileTap={{ scale: 0.97 }}>
                                                    <Mic size={15} /> Start Recording
                                                </motion.button>
                                            ) : (
                                                <motion.button className="btn btn-ghost" style={{ flex: 1, justifyContent: 'center', borderColor: 'var(--red-600)', color: 'var(--red-600)' }}
                                                    onClick={stopRecording} whileTap={{ scale: 0.97 }}
                                                    animate={{ opacity: [1, 0.75, 1] }} transition={{ duration: 1.1, repeat: Infinity }}>
                                                    <MicOff size={15} /> Stop Recording
                                                </motion.button>
                                            )}
                                            <motion.button className="btn btn-success" style={{ flex: 1, justifyContent: 'center' }}
                                                onClick={generateSoap} disabled={loading} whileTap={{ scale: 0.97 }}>
                                                {loading
                                                    ? <><span style={{ width: 14, height: 14, border: '2px solid #fff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} /> Generating…</>
                                                    : <><Send size={14} /> Generate SOAP</>
                                                }
                                            </motion.button>
                                        </div>

                                        {/* Error */}
                                        <AnimatePresence>
                                            {error && (
                                                <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                                                    className="alert alert-error" style={{ marginTop: '0.875rem' }}>
                                                    <AlertCircle size={15} style={{ flexShrink: 0 }} />
                                                    <span>{error}</span>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                </div>

                                {/* RxNorm card */}
                                <div className="card card-purple">
                                    <div className="section-header">
                                        <div className="section-header-icon" style={{ background: 'var(--purple-100)' }}>
                                            <Search size={14} color="var(--purple-600)" />
                                        </div>
                                        <h2>Drug Lookup</h2>
                                        <span className="badge badge-purple" style={{ marginLeft: 'auto' }}>NLM RxNorm</span>
                                    </div>
                                    <div style={{ padding: '1rem' }}>
                                        <input className="input" placeholder="Search drug name (e.g. metformin)…"
                                            value={rxQuery} onChange={e => setRxQuery(e.target.value)} />
                                        <div style={{ marginTop: '0.75rem', maxHeight: 180, overflowY: 'auto' }}>
                                            {rxLoading ? (
                                                [1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: 30, marginBottom: '0.4rem' }} />)
                                            ) : rxResults.length === 0 && rxQuery ? (
                                                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '0.5rem' }}>No results found</p>
                                            ) : rxResults.map(r => (
                                                <div key={r.rxcui} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.45rem 0', borderBottom: '1px solid #eef2f8' }}>
                                                    <span className="badge badge-purple mono" style={{ minWidth: 72, justifyContent: 'center', fontSize: '0.7rem' }}>{r.rxcui}</span>
                                                    <span style={{ fontSize: '0.82rem', color: 'var(--text-primary)' }}>{r.name}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* ─── RIGHT PANEL ─── */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                <AnimatePresence mode="wait">
                                    {loading ? (
                                        <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                            className="card" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
                                            <div style={{ display: 'flex', justifyContent: 'center', gap: 5, marginBottom: '1.5rem' }}>
                                                {[0, 1, 2, 3, 4, 5, 6, 7].map(i => (
                                                    <div key={i} style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--blue-500)', animation: `bounce 0.8s ease ${i * 0.1}s infinite` }} />
                                                ))}
                                            </div>
                                            <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>BioMistral is generating…</p>
                                            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Processing multilingual clinical transcript</p>
                                        </motion.div>
                                    ) : soap ? (
                                        <motion.div key="soap" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                                            {/* Header row */}
                                            <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                                                <div>
                                                    <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.5rem' }}>
                                                        <button className={`btn btn-sm ${viewMode === 'clinician' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setViewMode('clinician')}>Clinician View</button>
                                                        <button className={`btn btn-sm ${viewMode === 'patient' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => { if (!patientEdu) generateEducation(); else setViewMode('patient'); }}>Patient View</button>
                                                    </div>
                                                    <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                                                        {savedInfo && <span className="badge badge-green"><CheckCircle size={10} /> {savedInfo}</span>}
                                                        {soap.source && <span className="badge badge-blue">{soap.source}</span>}
                                                        {soap.language && soap.language !== 'en' && (
                                                            <span className="badge" style={{ background: '#f0fdf4', color: '#166534', border: '1px solid #86efac' }}>
                                                                🌐 {soap.language.toUpperCase()}
                                                            </span>
                                                        )}
                                                        <span className="badge badge-navy">{new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</span>
                                                        {soap.language && soap.language !== 'en' && soap.subjective_localized && (
                                                            <button
                                                                className="btn btn-sm btn-ghost"
                                                                style={{ fontSize: '0.72rem', padding: '0.2rem 0.6rem', border: '1px solid var(--blue-200)' }}
                                                                onClick={() => setShowLocalized(v => !v)}
                                                            >
                                                                {showLocalized ? '🇬🇧 Show English' : `🌍 Show ${soap.language?.toUpperCase()}`}
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                                <div style={{ display: 'flex', gap: '0.4rem' }}>
                                                    <button className="btn btn-outline btn-sm" onClick={downloadSoap}>
                                                        <Download size={13} /> .txt
                                                    </button>
                                                    <button className="btn btn-primary btn-sm" onClick={downloadPdf} disabled={pdfLoading}>
                                                        {pdfLoading ? <><span className="spin" />ing...</> : <><FileText size={13} /> PDF Report</>}
                                                    </button>
                                                    <button className="btn btn-success btn-sm" style={{ background: '#25D366', borderColor: '#25D366' }} onClick={sendWhatsApp} disabled={waLoading}>
                                                        <MessageSquare size={13} /> WhatsApp
                                                    </button>
                                                </div>
                                            </div>

                                            <AnimatePresence mode="wait">
                                                {viewMode === 'clinician' ? (
                                                    <motion.div key="clinician" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                                        {/* Chief complaint banner */}
                                                        {soap.chief_complaint && (
                                                            <div className="alert alert-info" style={{ marginBottom: '0.875rem', borderRadius: 10 }}>
                                                                <strong>Chief Complaint:</strong>&nbsp;{soap.chief_complaint}
                                                            </div>
                                                        )}

                                                        {/* SOAP sections */}
                                                        {[
                                                            { label: 'S', title: 'Subjective — Patient report', enContent: soap.subjective_en || soap.subjective, localContent: soap.subjective_localized || soap.subjective, cls: 'soap-s' },
                                                            { label: 'O', title: 'Objective — Clinical findings', enContent: soap.objective_en || soap.objective, localContent: soap.objective_localized || soap.objective, cls: 'soap-o' },
                                                            { label: 'A', title: 'Assessment — Diagnosis', enContent: soap.assessment_en || soap.assessment, localContent: soap.assessment_localized || soap.assessment, cls: 'soap-a' },
                                                            { label: 'P', title: 'Plan — Treatment', enContent: soap.plan_en || soap.plan, localContent: soap.plan_localized || soap.plan, cls: 'soap-p' },
                                                        ].map(({ label, title, enContent, localContent, cls }, i) => {
                                                            const displayContent = (soap.language && soap.language !== 'en' && showLocalized)
                                                                ? localContent
                                                                : enContent;
                                                            return (
                                                                <motion.div key={label} className={`soap-block ${cls}`}
                                                                    initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }}
                                                                    transition={{ delay: i * 0.08 }}>
                                                                    <p className="soap-label">
                                                                        <span style={{ width: 20, height: 20, borderRadius: 5, background: 'rgba(255,255,255,0.7)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: '0.7rem' }}>{label}</span>
                                                                        {title}
                                                                    </p>
                                                                    <p>{displayContent || <em style={{ opacity: 0.6 }}>Not documented</em>}</p>
                                                                </motion.div>
                                                            );
                                                        })}

                                                        {/* ICD-10 */}
                                                        {(soap.icd10_codes || []).length > 0 && (
                                                            <div className="card" style={{ padding: '1rem 1.25rem' }}>
                                                                <p style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.6rem' }}>Identified ICD-10 Codes</p>
                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                                                    {(soap.icd10_codes || []).map((c, i) => (
                                                                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingBottom: '0.4rem', borderBottom: i < (soap.icd10_codes?.length || 0) - 1 ? '1px solid #f1f5f9' : 'none' }}>
                                                                            <span className="badge badge-purple mono" style={{ minWidth: 72, justifyContent: 'center' }}>{c.icd10_code}</span>
                                                                            <span style={{ fontSize: '0.82rem', color: 'var(--text-primary)' }}>{c.description}</span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </motion.div>
                                                ) : (
                                                    <motion.div key="patient" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                                        <div className="card card-blue" style={{ padding: '1.5rem' }}>
                                                            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--blue-500)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                                Patient Education & Instructions
                                                            </h3>
                                                            {eduLoading ? (
                                                                <div style={{ textAlign: 'center', padding: '2rem' }}>
                                                                    <div style={{ display: 'flex', justifyContent: 'center', gap: 4, marginBottom: '1rem' }}>
                                                                        {[1, 2, 3].map(i => <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--blue-500)', animation: 'bounce 0.8s infinite' }} />)}
                                                                    </div>
                                                                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>AI is simplifying your medical notes…</p>
                                                                </div>
                                                            ) : (
                                                                <div style={{ fontSize: '0.95rem', lineHeight: 1.8, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                                                                    {patientEdu}
                                                                </div>
                                                            )}
                                                        </div>

                                                        {eduLinks.length > 0 && (
                                                            <div className="card" style={{ marginTop: '1rem', padding: '1.25rem' }}>
                                                                <h4 style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>Reliable Health Resources</h4>
                                                                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.6rem' }}>
                                                                    {eduLinks.map((link, i) => (
                                                                        <a key={i} href={link.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost" style={{ justifyContent: 'flex-start', padding: '0.75rem', fontSize: '0.85rem' }}>
                                                                            <Info size={14} color="var(--blue-500)" /> Learn more about: <strong>{link.condition}</strong>
                                                                        </a>
                                                                    ))}
                                                                </div>
                                                                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '1rem', fontStyle: 'italic' }}>Powered by NLM MedlinePlus</p>
                                                            </div>
                                                        )}
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </motion.div>
                                    ) : (
                                        <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                            className="card" style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)', border: '2px dashed var(--border)' }}>
                                            <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'var(--bg-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem' }}>
                                                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" opacity={0.4}>
                                                    <rect x="9" y="2" width="6" height="20" rx="2" fill="var(--blue-500)" />
                                                    <rect x="2" y="9" width="20" height="6" rx="2" fill="var(--blue-500)" />
                                                </svg>
                                            </div>
                                            <p style={{ fontWeight: 600, marginBottom: '0.4rem', color: 'var(--text-secondary)' }}>SOAP Note Preview</p>
                                            <p style={{ fontSize: '0.82rem' }}>Record or paste a clinical transcript, then click <strong>Generate SOAP</strong></p>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', justifyContent: 'center', marginTop: '1.25rem' }}>
                                                {SPEECH_LANGS.slice(0, 5).map(l => <span key={l.code} className="badge badge-blue">{l.native}</span>)}
                                                <span className="badge badge-gray">+5 more</span>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </motion.div>
                ) : (
                    /* ══════════════════════════════════════════════════════
                       SCAN REPORT TAB
                       ══════════════════════════════════════════════════════ */
                    <motion.div key="scan-tab" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>

                        {/* Scanner header */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #006689, #0891b2)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(0,102,137,0.3)' }}>
                                    <ScanLine size={18} color="#fff" />
                                </span>
                                <div>
                                    <p style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>Medical Report Scanner</p>
                                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Upload a prescription, lab report, or discharge summary</p>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '0.4rem', marginLeft: 'auto' }}>
                                <span className="badge badge-teal">qwen2.5vl:3b</span>
                                <span className="badge badge-navy">Vision AI</span>
                                <span className="badge badge-green">Local · No PHI Leak</span>
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '1.25rem', alignItems: 'start' }}>

                            {/* LEFT — drop zone */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                <div className="card card-teal" style={{ padding: '1.25rem' }}>
                                    <h3 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-primary)' }}>Upload Document Image</h3>

                                    {!scanPreview ? (
                                        <div
                                            className={`report-drop-zone${scanDragOver ? ' active' : ''}`}
                                            onDragOver={e => { e.preventDefault(); setScanDragOver(true); }}
                                            onDragLeave={() => setScanDragOver(false)}
                                            onDrop={e => { e.preventDefault(); setScanDragOver(false); if (e.dataTransfer.files[0]) handleScanFile(e.dataTransfer.files[0]); }}
                                            onClick={() => scanFileRef.current?.click()}
                                            style={{
                                                border: `2px dashed ${scanDragOver ? 'var(--teal-600)' : 'var(--border)'}`,
                                                borderRadius: 12, padding: '2rem 1rem', textAlign: 'center',
                                                cursor: 'pointer', background: scanDragOver ? '#f0fbff' : '#fafcff',
                                                transition: 'all 0.18s ease',
                                            }}
                                        >
                                            <div style={{ width: 54, height: 54, borderRadius: 14, background: 'linear-gradient(135deg, #d4e8ff, #b3ecff)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 0.875rem', border: '1px solid #89d8f0' }}>
                                                <Upload size={22} color="var(--teal-600)" />
                                            </div>
                                            <p style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                                                {scanDragOver ? 'Drop it here!' : 'Drag & drop or click to upload'}
                                            </p>
                                            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>JPG, PNG, WebP · prescriptions, lab reports, discharge summaries</p>
                                            <input ref={scanFileRef} type="file" accept="image/*" style={{ display: 'none' }}
                                                onChange={e => { if (e.target.files?.[0]) handleScanFile(e.target.files[0]); }} />
                                        </div>
                                    ) : (
                                        <div style={{ position: 'relative' }}>
                                            <img src={scanPreview} alt="Uploaded" style={{ width: '100%', borderRadius: 10, border: '1.5px solid var(--border)', maxHeight: 260, objectFit: 'contain', background: '#f9fafb' }} />
                                            <button onClick={clearScan} style={{ position: 'absolute', top: 6, right: 6, background: 'rgba(0,0,0,0.5)', border: 'none', borderRadius: '50%', width: 26, height: 26, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                <X size={13} color="#fff" />
                                            </button>
                                            <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.4rem', textAlign: 'center' }}>{scanFile?.name}</p>
                                        </div>
                                    )}

                                    <AnimatePresence>
                                        {scanError && (
                                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                                className="alert alert-error" style={{ marginTop: '0.75rem' }}>
                                                <AlertCircle size={13} style={{ flexShrink: 0 }} /><span style={{ fontSize: '0.8rem' }}>{scanError}</span>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>

                                    <motion.button
                                        className="btn btn-w100" whileTap={{ scale: 0.97 }}
                                        disabled={!scanFile || scanning}
                                        onClick={scanImage}
                                        style={{ marginTop: '1rem', justifyContent: 'center', background: 'var(--grad-teal)', color: '#fff', boxShadow: '0 2px 8px rgba(0,102,137,0.3)', borderRadius: 10, fontFamily: 'inherit', border: 'none', cursor: !scanFile || scanning ? 'not-allowed' : 'pointer', opacity: !scanFile || scanning ? 0.6 : 1 }}
                                    >
                                        {scanning ? (
                                            <><motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }} style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid rgba(255,255,255,0.35)', borderTopColor: '#fff', borderRadius: '50%' }} /> Analysing…</>
                                        ) : (<><ScanLine size={14} /> Scan Document</>)}
                                    </motion.button>
                                </div>

                                {/* Doc type legend */}
                                <div className="card" style={{ padding: '1rem 1.25rem' }}>
                                    <p style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.6rem' }}>Supported Types</p>
                                    {[{ icon: '💊', l: 'Prescription', d: 'Medications, dosages' }, { icon: '🧪', l: 'Lab Report', d: 'CBC, LFT, RFT…' }, { icon: '🏥', l: 'Discharge Summary', d: 'Diagnoses, follow-up' }, { icon: '📡', l: 'Radiology Report', d: 'X-ray, MRI, CT' }].map(({ icon, l, d }) => (
                                        <div key={l} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0.4rem 0.5rem', borderRadius: 8, marginBottom: '0.3rem', background: '#fafcff', border: '1px solid #eef2f8' }}>
                                            <span style={{ fontSize: '1rem' }}>{icon}</span>
                                            <div><p style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)' }}>{l}</p><p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{d}</p></div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* RIGHT — results */}
                            <div>
                                <AnimatePresence mode="wait">
                                    {scanning ? (
                                        <motion.div key="sc-loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                            className="card" style={{ padding: '3.5rem 2rem', textAlign: 'center' }}>
                                            <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginBottom: '1.25rem' }}>
                                                {[0, 1, 2, 3, 4, 5, 6, 7].map(i => <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--teal-600)', animation: `bounce 0.8s ease ${i * 0.1}s infinite` }} />)}
                                            </div>
                                            <p style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.3rem' }}>qwen2.5vl:3b is reading the document…</p>
                                            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Extracting medications, lab values, diagnoses</p>
                                        </motion.div>
                                    ) : scanResult ? (
                                        <motion.div key="sc-result" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                                            {/* Result top bar */}
                                            {(() => {
                                                const ds = DOC_COLORS[scanResult.document_type] || DOC_COLORS.Other; return (
                                                    <div className="card" style={{ padding: '0.875rem 1.25rem', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                            <CheckCircle size={15} color="#15803d" />
                                                            <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>Extraction Complete</span>
                                                            <span style={{ padding: '0.18rem 0.65rem', borderRadius: 999, background: ds.bg, color: ds.color, border: `1px solid ${ds.border}`, fontSize: '0.72rem', fontWeight: 700 }}>{scanResult.document_type}</span>
                                                            {scanResult.model && <span className="badge badge-teal">{scanResult.model}</span>}
                                                        </div>
                                                        <div style={{ display: 'flex', gap: '0.4rem' }}>
                                                            <button className="btn btn-ghost btn-sm" onClick={() => { navigator.clipboard.writeText(JSON.stringify(scanResult, null, 2)); setCopiedJson(true); setTimeout(() => setCopiedJson(false), 2000); }}>
                                                                {copiedJson ? <CheckCircle size={12} /> : <Copy size={12} />}{copiedJson ? 'Copied!' : 'Copy JSON'}
                                                            </button>
                                                            <button className="btn btn-outline btn-sm" onClick={downloadScanResult}><Download size={12} /> .txt</button>
                                                        </div>
                                                    </div>
                                                );
                                            })()}

                                            {/* Patient info strip */}
                                            {(scanResult.patient_name || scanResult.doctor_name || scanResult.date || scanResult.hospital) && (
                                                <div className="card" style={{ padding: '0.75rem 1.25rem', marginBottom: '1rem', display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                                                    {scanResult.patient_name && <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Patient</span><span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{scanResult.patient_name}{scanResult.patient_age ? `, ${scanResult.patient_age}` : ''}</span></div>}
                                                    {scanResult.date && <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><Calendar size={12} color="var(--text-muted)" /><span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{scanResult.date}</span></div>}
                                                    {scanResult.doctor_name && <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Dr.</span><span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{scanResult.doctor_name}</span></div>}
                                                    {scanResult.hospital && <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><Building2 size={12} color="var(--text-muted)" /><span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{scanResult.hospital}</span></div>}
                                                </div>
                                            )}

                                            {/* Summary alert */}
                                            {scanResult.full_summary && (
                                                <div className="alert alert-info" style={{ marginBottom: '1rem', borderRadius: 10 }}>
                                                    <Info size={13} style={{ flexShrink: 0 }} /><span style={{ fontSize: '0.83rem' }}>{scanResult.full_summary}</span>
                                                </div>
                                            )}

                                            {/* Diagnoses */}
                                            {(scanResult.diagnoses || []).length > 0 && (
                                                <div className="card card-purple" style={{ padding: '0.875rem 1.25rem', marginBottom: '1rem' }}>
                                                    <p style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--purple-600)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>Diagnoses</p>
                                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                                                        {scanResult.diagnoses!.map((d, i) => <span key={i} className="badge badge-purple" style={{ fontSize: '0.78rem' }}>{d}</span>)}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Medications table */}
                                            {(scanResult.medications || []).length > 0 && (
                                                <div className="card card-blue" style={{ marginBottom: '1rem', overflow: 'hidden' }}>
                                                    <div className="section-header">
                                                        <div className="section-header-icon" style={{ background: 'var(--blue-100)' }}><Pill size={13} color="var(--blue-600)" /></div>
                                                        <h2>Medications</h2>
                                                        <span className="badge badge-blue" style={{ marginLeft: 'auto' }}>{scanResult.medications!.length}</span>
                                                    </div>
                                                    <div className="table-wrap">
                                                        <table><thead><tr><th>Drug</th><th>Dose</th><th>Frequency</th><th>Duration</th><th>Route</th></tr></thead>
                                                            <tbody>{scanResult.medications!.map((m, i) => <tr key={i}><td style={{ fontWeight: 600 }}>{m.name}</td><td>{m.dose || '—'}</td><td>{m.frequency || '—'}</td><td>{m.duration || '—'}</td><td>{m.route || '—'}</td></tr>)}</tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Lab values table */}
                                            {(scanResult.lab_values || []).length > 0 && (
                                                <div className="card card-green" style={{ marginBottom: '1rem', overflow: 'hidden' }}>
                                                    <div className="section-header">
                                                        <div className="section-header-icon" style={{ background: 'var(--green-100)' }}><FlaskConical size={13} color="var(--green-600)" /></div>
                                                        <h2>Lab Values</h2>
                                                        <span className="badge badge-green" style={{ marginLeft: 'auto' }}>{scanResult.lab_values!.length}</span>
                                                    </div>
                                                    <div className="table-wrap">
                                                        <table><thead><tr><th>Test</th><th>Value</th><th>Unit</th><th>Reference</th><th>Flag</th></tr></thead>
                                                            <tbody>{scanResult.lab_values!.map((l, i) => (
                                                                <tr key={i}>
                                                                    <td style={{ fontWeight: 600 }}>{l.test}</td>
                                                                    <td style={{ fontWeight: 700, color: l.flag === 'HIGH' ? '#b91c1c' : l.flag === 'LOW' ? '#1d4ed8' : 'inherit' }}>{l.value}</td>
                                                                    <td>{l.unit || '—'}</td>
                                                                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{l.reference_range || '—'}</td>
                                                                    <td>{l.flag && <span style={{ padding: '0.12rem 0.5rem', borderRadius: 999, background: flagBg(l.flag), color: flagColor(l.flag), fontSize: '0.68rem', fontWeight: 700 }}>{l.flag}</span>}</td>
                                                                </tr>
                                                            ))}</tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Clinical notes */}
                                            {scanResult.clinical_notes && (
                                                <div className="card card-amber" style={{ padding: '0.875rem 1.25rem', marginBottom: '1rem' }}>
                                                    <p style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--amber-600)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.4rem' }}>Clinical Notes</p>
                                                    <p style={{ fontSize: '0.85rem', lineHeight: 1.7 }}>{scanResult.clinical_notes}</p>
                                                </div>
                                            )}

                                            {/* Raw JSON toggle */}
                                            <div className="card" style={{ overflow: 'hidden' }}>
                                                <button onClick={() => setShowRawJson(v => !v)} style={{ width: '100%', padding: '0.75rem 1.25rem', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Raw JSON Response</span>
                                                    {showRawJson ? <ChevronUp size={14} color="var(--text-muted)" /> : <ChevronDown size={14} color="var(--text-muted)" />}
                                                </button>
                                                {showRawJson && (
                                                    <pre style={{ padding: '0 1.25rem 1rem', margin: 0, fontSize: '0.73rem', lineHeight: 1.6, color: 'var(--text-secondary)', overflowX: 'auto', borderTop: '1px solid var(--border)', background: '#fafcff' }}>
                                                        {JSON.stringify(scanResult, null, 2)}
                                                    </pre>
                                                )}
                                            </div>
                                        </motion.div>
                                    ) : (
                                        <motion.div key="sc-empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                            className="card" style={{ padding: '4rem 2rem', textAlign: 'center' }}>
                                            <div style={{ width: 64, height: 64, borderRadius: 18, background: 'linear-gradient(135deg, #d4e8ff, #b3ecff)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem', border: '1px solid #89d8f0' }}>
                                                <ScanLine size={28} color="var(--teal-600)" strokeWidth={1.5} />
                                            </div>
                                            <p style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem', fontSize: '0.95rem' }}>No document scanned yet</p>
                                            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: 280, margin: '0 auto' }}>Upload a medical image on the left and click <strong>Scan Document</strong> to extract all clinical data.</p>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
            <style>{`@keyframes spin{to{transform:rotate(360deg)}} @keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}`}</style>
        </AppLayout>
    );
}
