'use client';
import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ScanLine, Upload, X, AlertCircle, CheckCircle, Download,
    Pill, FlaskConical, Stethoscope, User, Building2, Calendar,
    ClipboardList, ChevronDown, ChevronUp, Copy
} from 'lucide-react';
import AppLayout from '../../components/AppLayout';
import api from '../../lib/api';

/* ─── Types ──────────────────────────────────────────────── */
interface Medication {
    name: string;
    dose?: string;
    frequency?: string;
    duration?: string;
    route?: string;
}
interface LabValue {
    test: string;
    value: string;
    unit?: string;
    reference_range?: string;
    flag?: 'HIGH' | 'LOW' | 'NORMAL' | null;
}
interface ScanResult {
    document_type: string;
    patient_name?: string;
    patient_age?: string;
    patient_id?: string;
    date?: string;
    doctor_name?: string;
    hospital?: string;
    diagnoses?: string[];
    medications?: Medication[];
    lab_values?: LabValue[];
    clinical_notes?: string;
    full_summary?: string;
    model?: string;
    filename?: string;
}

/* ─── Helpers ─────────────────────────────────────────────── */
const DOC_COLORS: Record<string, { bg: string; color: string; border: string }> = {
    Prescription: { bg: '#eef6ff', color: '#1d4ed8', border: '#bfdbfe' },
    'Lab Report': { bg: '#f0fdf4', color: '#15803d', border: '#86efac' },
    'Discharge Summary': { bg: '#fdf4ff', color: '#7c3aed', border: '#d8b4fe' },
    'Radiology Report': { bg: '#fffbeb', color: '#92400e', border: '#fcd34d' },
    Other: { bg: '#f8fafc', color: '#475569', border: '#cbd5e1' },
};

const flagColor = (flag: string | null | undefined) => {
    if (flag === 'HIGH') return '#b91c1c';
    if (flag === 'LOW') return '#1d4ed8';
    return '#15803d';
};
const flagBg = (flag: string | null | undefined) => {
    if (flag === 'HIGH') return '#fee2e2';
    if (flag === 'LOW') return '#dbeafe';
    return '#dcfce7';
};

/* ─── Page ────────────────────────────────────────────────── */
export default function ScanReportPage() {
    const [dragOver, setDragOver] = useState(false);
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [scanning, setScanning] = useState(false);
    const [result, setResult] = useState<ScanResult | null>(null);
    const [error, setError] = useState('');
    const [showRaw, setShowRaw] = useState(false);
    const [copied, setCopied] = useState(false);
    const fileRef = useRef<HTMLInputElement>(null);

    const handleFile = useCallback((file: File) => {
        if (!file.type.startsWith('image/')) {
            setError('Please upload an image file (JPG, PNG, WebP).');
            return;
        }
        setImageFile(file);
        setError('');
        setResult(null);
        const reader = new FileReader();
        reader.onload = e => setImagePreview(e.target?.result as string);
        reader.readAsDataURL(file);
    }, []);

    const onDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    }, [handleFile]);

    const scanImage = async () => {
        if (!imageFile) return;
        setScanning(true); setError(''); setResult(null);
        const form = new FormData();
        form.append('file', imageFile);
        try {
            const res = await api.post('/api/scan-report', form, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setResult(res.data);
        } catch (err: unknown) {
            const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
                || 'Scan failed. Ensure Ollama is running with qwen2.5vl:3b.';
            setError(msg);
        } finally {
            setScanning(false);
        }
    };

    const clearAll = () => {
        setImageFile(null); setImagePreview(null);
        setResult(null); setError('');
    };

    const copyResult = () => {
        if (!result) return;
        navigator.clipboard.writeText(JSON.stringify(result, null, 2));
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const downloadResult = () => {
        if (!result) return;
        const lines = [
            `ScribeAI — Medical Document Analysis`,
            `Scanned: ${new Date().toLocaleString('en-IN')}`,
            `File: ${result.filename || 'unknown'}`,
            `═══════════════════════════════════════`,
            `Type: ${result.document_type}`,
            `Patient: ${result.patient_name || 'N/A'} | Age: ${result.patient_age || 'N/A'}`,
            `Date: ${result.date || 'N/A'}`,
            `Doctor: ${result.doctor_name || 'N/A'}`,
            `Hospital: ${result.hospital || 'N/A'}`,
            `───────────────────────────────────────`,
            `DIAGNOSES:`,
            ...(result.diagnoses || []).map(d => `  • ${d}`),
            ``,
            `MEDICATIONS:`,
            ...(result.medications || []).map(m =>
                `  • ${m.name}${m.dose ? ' — ' + m.dose : ''}${m.frequency ? ' | ' + m.frequency : ''}${m.duration ? ' | ' + m.duration : ''}`
            ),
            ``,
            `LAB VALUES:`,
            ...(result.lab_values || []).map(l =>
                `  • ${l.test}: ${l.value}${l.unit ? ' ' + l.unit : ''}${l.reference_range ? ' (ref: ' + l.reference_range + ')' : ''}${l.flag ? ' [' + l.flag + ']' : ''}`
            ),
            ``,
            `NOTES: ${result.clinical_notes || 'None'}`,
            ``,
            `SUMMARY:`,
            result.full_summary || '',
        ].join('\n');
        const blob = new Blob([lines], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'scan_report.txt'; a.click();
        URL.revokeObjectURL(url);
    };

    const docStyle = result ? (DOC_COLORS[result.document_type] || DOC_COLORS.Other) : DOC_COLORS.Other;

    return (
        <AppLayout>
            {/* ── Page Header ── */}
            <div className="page-header">
                <div>
                    <div className="breadcrumb">
                        <span>ScribeAI</span><span>/</span><span>Report Scanner</span>
                    </div>
                    <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <span style={{
                            width: 38, height: 38, borderRadius: 10, flexShrink: 0,
                            background: 'linear-gradient(135deg, #0057b8, #007b91)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            boxShadow: '0 2px 10px rgba(0,87,184,0.3)',
                        }}>
                            <ScanLine size={20} color="#fff" />
                        </span>
                        Medical Report Scanner
                    </h1>
                    <p className="page-subtitle">
                        Upload a prescription, lab report, or discharge summary — <strong>qwen2.5vl:3b</strong> extracts all clinical data instantly.
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className="badge badge-teal">qwen2.5vl:3b</span>
                    <span className="badge badge-navy">Vision AI</span>
                    <span className="badge badge-green">Local · No PHI Leak</span>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: '1.25rem', alignItems: 'start' }}>

                {/* ── LEFT: Upload panel ── */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

                    {/* Drop zone */}
                    <div className="card card-blue" style={{ padding: '1.25rem' }}>
                        <h3 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ width: 22, height: 22, borderRadius: 6, background: '#dbeafe', border: '1px solid #bfdbfe', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', color: 'var(--blue-600)' }}>01</span>
                            Upload Document Image
                        </h3>

                        {!imagePreview ? (
                            <div
                                className={`report-drop-zone${dragOver ? ' active' : ''}`}
                                onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                                onDragLeave={() => setDragOver(false)}
                                onDrop={onDrop}
                                onClick={() => fileRef.current?.click()}
                                style={{
                                    border: `2px dashed ${dragOver ? 'var(--blue-500)' : 'var(--border)'}`,
                                    borderRadius: 14,
                                    padding: '2.5rem 1rem',
                                    textAlign: 'center',
                                    cursor: 'pointer',
                                    background: dragOver ? 'var(--blue-50)' : '#fafcff',
                                    transition: 'all 0.18s ease',
                                    userSelect: 'none',
                                }}
                            >
                                <motion.div animate={dragOver ? { scale: 1.1 } : { scale: 1 }}>
                                    <div style={{
                                        width: 64, height: 64, borderRadius: 16,
                                        background: 'linear-gradient(135deg, #dbeafe, #e0ecff)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        margin: '0 auto 1rem',
                                        border: '1px solid #bfdbfe',
                                    }}>
                                        <Upload size={26} color="var(--blue-500)" />
                                    </div>
                                    <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.3rem', fontSize: '0.9rem' }}>
                                        {dragOver ? 'Drop it here!' : 'Drag & drop or click to upload'}
                                    </p>
                                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                        Supports JPG, PNG, WebP · prescriptions, lab reports, discharge summaries
                                    </p>
                                </motion.div>
                                <input
                                    ref={fileRef}
                                    type="file"
                                    accept="image/*"
                                    style={{ display: 'none' }}
                                    onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }}
                                />
                            </div>
                        ) : (
                            <div style={{ position: 'relative' }}>
                                <img
                                    src={imagePreview}
                                    alt="Uploaded document"
                                    style={{ width: '100%', borderRadius: 10, border: '1.5px solid var(--border)', maxHeight: 340, objectFit: 'contain', background: '#f9fafb' }}
                                />
                                <button
                                    onClick={clearAll}
                                    style={{
                                        position: 'absolute', top: 8, right: 8,
                                        background: 'rgba(0,0,0,0.55)', border: 'none',
                                        borderRadius: '50%', width: 28, height: 28,
                                        cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    }}
                                >
                                    <X size={14} color="#fff" />
                                </button>
                                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', textAlign: 'center' }}>
                                    {imageFile?.name}
                                </p>
                            </div>
                        )}

                        {/* Error */}
                        <AnimatePresence>
                            {error && (
                                <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                                    className="alert alert-error" style={{ marginTop: '0.875rem' }}>
                                    <AlertCircle size={14} style={{ flexShrink: 0 }} />
                                    <span>{error}</span>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Scan button */}
                        <motion.button
                            className="btn btn-primary btn-w100"
                            style={{ marginTop: '1rem', justifyContent: 'center' }}
                            disabled={!imageFile || scanning}
                            onClick={scanImage}
                            whileTap={{ scale: 0.97 }}
                        >
                            {scanning ? (
                                <>
                                    <motion.span
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                        style={{ display: 'inline-block', width: 15, height: 15, border: '2px solid rgba(255,255,255,0.4)', borderTopColor: '#fff', borderRadius: '50%' }}
                                    />
                                    Analysing with qwen2.5vl…
                                </>
                            ) : (
                                <><ScanLine size={15} /> Scan Document</>
                            )}
                        </motion.button>
                    </div>

                    {/* Document type legend */}
                    <div className="card" style={{ padding: '1rem 1.25rem' }}>
                        <p style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>Supported Document Types</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {[
                                { icon: '💊', label: 'Prescription', desc: 'Medications, dosages, instructions' },
                                { icon: '🧪', label: 'Lab Report', desc: 'CBC, LFT, RFT, lipid panels, etc.' },
                                { icon: '🏥', label: 'Discharge Summary', desc: 'Diagnoses, procedures, follow-up' },
                                { icon: '📡', label: 'Radiology Report', desc: 'X-ray, MRI, CT scan findings' },
                            ].map(({ icon, label, desc }) => (
                                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem', borderRadius: 8, background: '#fafcff', border: '1px solid var(--border)' }}>
                                    <span style={{ fontSize: '1.1rem' }}>{icon}</span>
                                    <div>
                                        <p style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{label}</p>
                                        <p style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>{desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* ── RIGHT: Results panel ── */}
                <div>
                    <AnimatePresence mode="wait">
                        {scanning ? (
                            <motion.div key="scanning" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                className="card" style={{ padding: '3.5rem 2rem', textAlign: 'center' }}>
                                <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginBottom: '1.5rem' }}>
                                    {[0, 1, 2, 3, 4, 5, 6, 7].map(i => (
                                        <div key={i} style={{
                                            width: 6, height: 6, borderRadius: '50%', background: 'var(--teal-600)',
                                            animation: `bounce 0.8s ease ${i * 0.1}s infinite`
                                        }} />
                                    ))}
                                </div>
                                <p style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.4rem', fontSize: '1rem' }}>
                                    qwen2.5vl:3b is reading the document…
                                </p>
                                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                                    Extracting medications, diagnoses, lab values and patient details
                                </p>
                            </motion.div>

                        ) : result ? (
                            <motion.div key="result" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>

                                {/* Result header */}
                                <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                        <CheckCircle size={16} color="#15803d" />
                                        <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>Extraction Complete</span>
                                        <span style={{
                                            padding: '0.2rem 0.75rem', borderRadius: 999,
                                            background: docStyle.bg, color: docStyle.color,
                                            border: `1px solid ${docStyle.border}`,
                                            fontSize: '0.75rem', fontWeight: 700,
                                        }}>{result.document_type}</span>
                                        {result.model && <span className="badge badge-teal">{result.model}</span>}
                                    </div>
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <button className="btn btn-ghost btn-sm" onClick={copyResult}>
                                            {copied ? <CheckCircle size={13} /> : <Copy size={13} />}
                                            {copied ? 'Copied!' : 'Copy JSON'}
                                        </button>
                                        <button className="btn btn-outline btn-sm" onClick={downloadResult}>
                                            <Download size={13} /> .txt
                                        </button>
                                    </div>
                                </div>

                                {/* Patient info bar */}
                                {(result.patient_name || result.doctor_name || result.date || result.hospital) && (
                                    <div className="card" style={{ padding: '0.875rem 1.25rem', marginBottom: '1rem', display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                                        {result.patient_name && (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                                <User size={13} color="var(--text-muted)" />
                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Patient</span>
                                                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{result.patient_name}{result.patient_age ? `, ${result.patient_age}` : ''}</span>
                                            </div>
                                        )}
                                        {result.date && (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                                <Calendar size={13} color="var(--text-muted)" />
                                                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{result.date}</span>
                                            </div>
                                        )}
                                        {result.doctor_name && (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                                <Stethoscope size={13} color="var(--text-muted)" />
                                                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{result.doctor_name}</span>
                                            </div>
                                        )}
                                        {result.hospital && (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                                <Building2 size={13} color="var(--text-muted)" />
                                                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{result.hospital}</span>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Summary */}
                                {result.full_summary && (
                                    <div className="alert alert-info" style={{ marginBottom: '1rem', borderRadius: 10 }}>
                                        <ClipboardList size={14} style={{ flexShrink: 0, marginTop: 1 }} />
                                        <span style={{ fontSize: '0.85rem' }}>{result.full_summary}</span>
                                    </div>
                                )}

                                {/* Diagnoses */}
                                {(result.diagnoses || []).length > 0 && (
                                    <div className="card card-purple" style={{ padding: '1rem 1.25rem', marginBottom: '1rem' }}>
                                        <p style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--purple-600)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                            <Stethoscope size={12} /> Diagnoses
                                        </p>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                                            {result.diagnoses!.map((d, i) => (
                                                <span key={i} className="badge badge-purple" style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem' }}>{d}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Medications table */}
                                {(result.medications || []).length > 0 && (
                                    <div className="card card-blue" style={{ marginBottom: '1rem', overflow: 'hidden' }}>
                                        <div className="section-header">
                                            <div className="section-header-icon" style={{ background: 'var(--blue-100)' }}>
                                                <Pill size={13} color="var(--blue-600)" />
                                            </div>
                                            <h2>Medications</h2>
                                            <span className="badge badge-blue" style={{ marginLeft: 'auto' }}>{result.medications!.length}</span>
                                        </div>
                                        <div className="table-wrap">
                                            <table>
                                                <thead>
                                                    <tr>
                                                        <th>Drug Name</th>
                                                        <th>Dose</th>
                                                        <th>Frequency</th>
                                                        <th>Duration</th>
                                                        <th>Route</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {result.medications!.map((m, i) => (
                                                        <tr key={i}>
                                                            <td style={{ fontWeight: 600 }}>{m.name}</td>
                                                            <td>{m.dose || '—'}</td>
                                                            <td>{m.frequency || '—'}</td>
                                                            <td>{m.duration || '—'}</td>
                                                            <td>{m.route || '—'}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}

                                {/* Lab values table */}
                                {(result.lab_values || []).length > 0 && (
                                    <div className="card card-green" style={{ marginBottom: '1rem', overflow: 'hidden' }}>
                                        <div className="section-header">
                                            <div className="section-header-icon" style={{ background: 'var(--green-100)' }}>
                                                <FlaskConical size={13} color="var(--green-600)" />
                                            </div>
                                            <h2>Lab Values</h2>
                                            <span className="badge badge-green" style={{ marginLeft: 'auto' }}>{result.lab_values!.length}</span>
                                        </div>
                                        <div className="table-wrap">
                                            <table>
                                                <thead>
                                                    <tr>
                                                        <th>Test</th>
                                                        <th>Value</th>
                                                        <th>Unit</th>
                                                        <th>Reference</th>
                                                        <th>Flag</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {result.lab_values!.map((l, i) => (
                                                        <tr key={i}>
                                                            <td style={{ fontWeight: 600 }}>{l.test}</td>
                                                            <td style={{ fontWeight: 700, color: l.flag === 'HIGH' ? '#b91c1c' : l.flag === 'LOW' ? '#1d4ed8' : 'inherit' }}>{l.value}</td>
                                                            <td>{l.unit || '—'}</td>
                                                            <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{l.reference_range || '—'}</td>
                                                            <td>
                                                                {l.flag && (
                                                                    <span style={{
                                                                        padding: '0.15rem 0.55rem', borderRadius: 999,
                                                                        background: flagBg(l.flag), color: flagColor(l.flag),
                                                                        fontSize: '0.7rem', fontWeight: 700,
                                                                    }}>{l.flag}</span>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}

                                {/* Clinical notes */}
                                {result.clinical_notes && (
                                    <div className="card card-amber" style={{ padding: '1rem 1.25rem', marginBottom: '1rem' }}>
                                        <p style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--amber-600)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
                                            Clinical Notes
                                        </p>
                                        <p style={{ fontSize: '0.87rem', lineHeight: 1.7, color: 'var(--text-primary)' }}>{result.clinical_notes}</p>
                                    </div>
                                )}

                                {/* Raw JSON toggle */}
                                <div className="card" style={{ overflow: 'hidden' }}>
                                    <button
                                        onClick={() => setShowRaw(v => !v)}
                                        style={{
                                            width: '100%', padding: '0.875rem 1.25rem',
                                            background: 'none', border: 'none', cursor: 'pointer',
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                        }}
                                    >
                                        <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Raw JSON Response</span>
                                        {showRaw ? <ChevronUp size={15} color="var(--text-muted)" /> : <ChevronDown size={15} color="var(--text-muted)" />}
                                    </button>
                                    {showRaw && (
                                        <pre style={{
                                            padding: '0 1.25rem 1.25rem', margin: 0,
                                            fontSize: '0.75rem', lineHeight: 1.6,
                                            color: 'var(--text-secondary)', overflowX: 'auto',
                                            borderTop: '1px solid var(--border)',
                                            background: '#fafcff',
                                        }}>
                                            {JSON.stringify(result, null, 2)}
                                        </pre>
                                    )}
                                </div>

                            </motion.div>

                        ) : (
                            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                className="card" style={{ padding: '4rem 2rem', textAlign: 'center' }}>
                                <div style={{
                                    width: 72, height: 72, borderRadius: 20,
                                    background: 'linear-gradient(135deg, #eef6ff, #e0ecff)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    margin: '0 auto 1.25rem', border: '1px solid #bfdbfe',
                                }}>
                                    <ScanLine size={30} color="var(--blue-500)" strokeWidth={1.5} />
                                </div>
                                <p style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.4rem', fontSize: '1rem' }}>
                                    No document scanned yet
                                </p>
                                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', maxWidth: 300, margin: '0 auto' }}>
                                    Upload a medical image on the left and click <strong>Scan Document</strong> to extract all clinical data.
                                </p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </AppLayout>
    );
}
