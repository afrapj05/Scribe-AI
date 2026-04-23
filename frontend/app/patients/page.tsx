'use client';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Plus, X, ChevronRight, MessageSquare } from 'lucide-react';
import AppLayout from '../../components/AppLayout';
import { Patients } from '../../lib/api';

interface Patient {
    id: string; name: string; age: number; gender: string;
    blood_group: string; phone: string; chronic_conditions: string[];
}

export default function PatientsPage() {
    const [patients, setPatients] = useState<Patient[]>([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [form, setForm] = useState({ name: '', age: 30, gender: 'Male', blood_group: 'O+', phone: '', email: '' });
    const [saving, setSaving] = useState(false);

    const load = (q = '') => {
        setLoading(true);
        Patients.list(q).then(setPatients).finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, []);

    useEffect(() => {
        const id = setTimeout(() => load(search), 350);
        return () => clearTimeout(id);
    }, [search]);

    const create = async () => {
        setSaving(true);
        try {
            await Patients.create(form);
            setShowAdd(false);
            setForm({ name: '', age: 30, gender: 'Male', blood_group: 'O+', phone: '', email: '' });
            load(search);
        } catch { /* ignore */ } finally { setSaving(false); }
    };

    const sendWhatsApp = async (p: Patient) => {
        if (!p.phone) { alert('Patient has no phone number.'); return; }
        const details = prompt(`Send reminder to ${p.name}?\nEnter Date and Time (e.g. 12/1 at 3pm):`, 'tomorrow at 10am');
        if (!details) return;

        const [date, time] = details.includes(' at ') ? details.split(' at ') : [details, '10:00 AM'];

        try {
            await api.post('/api/notify/whatsapp', {
                to_number: p.phone.startsWith('+') ? p.phone : `+91${p.phone}`,
                patient_name: p.name,
                appointment_date: date,
                appointment_time: time
            });
            alert(`WhatsApp reminder sent to ${p.name}!`);
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to send WhatsApp.');
        }
    };

    return (
        <AppLayout>
            <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1 className="page-title gradient-text">Patients</h1>
                    <p className="page-subtitle">Manage patient records</p>
                </div>
                <motion.button className="btn-primary" onClick={() => setShowAdd(!showAdd)} whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Plus size={16} /> Add Patient
                </motion.button>
            </div>

            <AnimatePresence>
                {showAdd && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        style={{ overflow: 'hidden', marginBottom: '1.5rem' }}
                    >
                        <div className="glass" style={{ padding: '1.5rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                                <p style={{ fontWeight: 600, margin: 0 }}>New Patient</p>
                                <button onClick={() => setShowAdd(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><X size={18} /></button>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.875rem' }}>
                                {[
                                    { key: 'name', label: 'Full Name', type: 'text' },
                                    { key: 'phone', label: 'Phone', type: 'text' },
                                    { key: 'email', label: 'Email', type: 'email' },
                                ].map(({ key, label, type }) => (
                                    <div key={key}>
                                        <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '0.3rem' }}>{label}</label>
                                        <input className="input" type={type} value={(form as Record<string, string | number>)[key] as string}
                                            onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} />
                                    </div>
                                ))}
                                <div>
                                    <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '0.3rem' }}>Age</label>
                                    <input className="input" type="number" value={form.age} onChange={e => setForm(f => ({ ...f, age: +e.target.value }))} />
                                </div>
                                <div>
                                    <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '0.3rem' }}>Gender</label>
                                    <select className="input" value={form.gender} onChange={e => setForm(f => ({ ...f, gender: e.target.value }))}>
                                        {['Male', 'Female', 'Other'].map(g => <option key={g}>{g}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '0.3rem' }}>Blood Group</label>
                                    <select className="input" value={form.blood_group} onChange={e => setForm(f => ({ ...f, blood_group: e.target.value }))}>
                                        {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(b => <option key={b}>{b}</option>)}
                                    </select>
                                </div>
                            </div>
                            <motion.button className="btn-primary" style={{ marginTop: '1rem' }} onClick={create}
                                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} disabled={saving}>
                                {saving ? 'Saving...' : 'Create Patient'}
                            </motion.button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="glass" style={{ padding: '1rem 1.25rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Search size={16} color="#64748b" />
                <input
                    className="input" style={{ border: 'none', background: 'none', padding: 0, flex: 1 }}
                    placeholder="Search by name..."
                    value={search} onChange={e => setSearch(e.target.value)}
                />
            </div>

            <div className="glass">
                <div className="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                {['Name', 'Age', 'Gender', 'Blood', 'Phone', 'Conditions', ''].map(h => <th key={h}>{h}</th>)}
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                Array.from({ length: 6 }).map((_, i) => (
                                    <tr key={i}>
                                        {Array.from({ length: 7 }).map((_, j) => (
                                            <td key={j}>
                                                <motion.div animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.05 }}
                                                    style={{ height: 14, background: 'rgba(255,255,255,0.06)', borderRadius: 4, width: '80%' }} />
                                            </td>
                                        ))}
                                    </tr>
                                ))
                            ) : patients.length === 0 ? (
                                <tr><td colSpan={7} style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>No patients found</td></tr>
                            ) : (
                                patients.map((p, i) => (
                                    <motion.tr key={p.id}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: Math.min(i, 20) * 0.03 }}
                                    >
                                        <td style={{ fontWeight: 500, color: '#e2e8f0' }}>{p.name}</td>
                                        <td>{p.age}</td>
                                        <td>{p.gender}</td>
                                        <td><span className="badge badge-teal">{p.blood_group}</span></td>
                                        <td style={{ color: '#94a3b8' }}>{p.phone || '—'}</td>
                                        <td>
                                            {(p.chronic_conditions || []).slice(0, 2).map(c => (
                                                <span key={c} className="badge badge-blue" style={{ marginRight: 4 }}>{c}</span>
                                            ))}
                                            {(p.chronic_conditions || []).length > 2 && <span className="badge" style={{ background: 'rgba(255,255,255,0.06)', color: '#94a3b8' }}>+{p.chronic_conditions.length - 2}</span>}
                                        </td>
                                        <td style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                            <button className="btn btn-ghost btn-sm" style={{ padding: '0.3rem', color: '#25D366' }} title="Send WhatsApp Reminder"
                                                onClick={(e) => { e.stopPropagation(); sendWhatsApp(p); }}>
                                                <MessageSquare size={16} />
                                            </button>
                                            <ChevronRight size={14} color="#64748b" />
                                        </td>
                                    </motion.tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </AppLayout>
    );
}
