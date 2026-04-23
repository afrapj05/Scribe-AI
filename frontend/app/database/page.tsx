'use client';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import AppLayout from '../../components/AppLayout';
import { Database } from '../../lib/api';

type Tab = 'stats' | 'visits' | 'prescriptions';

export default function DatabasePage() {
    const [tab, setTab] = useState<Tab>('stats');
    const [stats, setStats] = useState<Record<string, number> | null>(null);
    const [visits, setVisits] = useState<Record<string, string>[]>([]);
    const [presc, setPresc] = useState<Record<string, string>[]>([]);

    useEffect(() => { Database.stats().then(setStats); }, []);
    useEffect(() => {
        if (tab === 'visits') Database.visits().then(setVisits);
        if (tab === 'prescriptions') Database.prescriptions().then(setPresc);
    }, [tab]);

    return (
        <AppLayout>
            <div style={{ marginBottom: '2rem' }}>
                <h1 className="page-title gradient-text">Database</h1>
                <p className="page-subtitle">Manage and inspect clinical records</p>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                {(['stats', 'visits', 'prescriptions'] as Tab[]).map(t => (
                    <motion.button key={t} onClick={() => setTab(t)}
                        whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                        style={{
                            padding: '0.55rem 1.1rem', borderRadius: 8, border: `1px solid ${tab === t ? '#00d4aa' : 'rgba(255,255,255,0.08)'}`,
                            background: tab === t ? 'rgba(0,212,170,0.1)' : 'transparent',
                            color: tab === t ? '#00d4aa' : '#64748b', cursor: 'pointer',
                            fontSize: '0.875rem', fontWeight: tab === t ? 600 : 400,
                            textTransform: 'capitalize',
                        }}>
                        {t}
                    </motion.button>
                ))}
            </div>

            <motion.div key={tab} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
                {tab === 'stats' && stats && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '1rem' }}>
                        {Object.entries(stats).map(([k, v], i) => (
                            <motion.div key={k} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.06 }}
                                className="glass" style={{ padding: '1.25rem' }}>
                                <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 0.4rem', textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</p>
                                <p style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0, color: '#e2e8f0' }}>{v}</p>
                            </motion.div>
                        ))}
                    </div>
                )}

                {tab === 'visits' && (
                    <div className="glass">
                        <div className="table-wrap">
                            <table>
                                <thead><tr>{['Visit ID', 'Patient ID', 'Chief Complaint', 'Department', 'Date', 'Clinician'].map(h => <th key={h}>{h}</th>)}</tr></thead>
                                <tbody>
                                    {visits.length === 0
                                        ? <tr><td colSpan={6} style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>No visits yet</td></tr>
                                        : visits.map((v, i) => (
                                            <motion.tr key={v.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.02 }}>
                                                <td style={{ color: '#00d4aa', fontFamily: 'monospace', fontSize: '0.8rem' }}>{v.id}</td>
                                                <td style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{v.patient_id}</td>
                                                <td>{v.chief_complaint}</td>
                                                <td><span className="badge badge-blue">{v.dept || 'General'}</span></td>
                                                <td style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{v.date ? new Date(v.date).toLocaleDateString() : '—'}</td>
                                                <td style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{v.clinician_id}</td>
                                            </motion.tr>
                                        ))
                                    }
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {tab === 'prescriptions' && (
                    <div className="glass">
                        <div className="table-wrap">
                            <table>
                                <thead><tr>{['Medicine', 'Patient ID', 'Dosage', 'Frequency', 'Duration', 'Route', 'Date'].map(h => <th key={h}>{h}</th>)}</tr></thead>
                                <tbody>
                                    {presc.length === 0
                                        ? <tr><td colSpan={7} style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>No prescriptions yet</td></tr>
                                        : presc.map((p, i) => (
                                            <motion.tr key={p.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.02 }}>
                                                <td style={{ fontWeight: 500, color: '#e2e8f0' }}>{p.medicine}</td>
                                                <td style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{p.patient_id}</td>
                                                <td>{p.dosage}</td>
                                                <td>{p.frequency}</td>
                                                <td>{p.duration}</td>
                                                <td><span className="badge badge-teal">{p.route}</span></td>
                                                <td style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{p.date}</td>
                                            </motion.tr>
                                        ))
                                    }
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </motion.div>
        </AppLayout>
    );
}
