'use client';
import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
    Users, Activity, FileText, Mic, AlertTriangle, TrendingUp,
    Heart, AlertCircle, BookOpen, FlaskConical, RefreshCw
} from 'lucide-react';
import AppLayout from '../../components/AppLayout';
import { Dashboard as DashboardAPI } from '../../lib/api';
import api from '../../lib/api';

interface Stats {
    total_patients: number; total_visits: number;
    total_soap_notes: number; total_audio: number;
    visits_7d: number; high_risk_patients: number; patients_with_chronic: number;
}
interface Recall { product: string; reason: string; class: string; date: string; company: string; }
interface Trial { nct_id: string; title: string; status: string; phase: string; conditions: string[]; }

const METRICS = [
    { key: 'total_patients', label: 'Total Patients', Icon: Users, color: '#0066cc', bg: '#dbeafe' },
    { key: 'total_visits', label: 'Total Visits', Icon: Activity, color: '#059669', bg: '#dcfce7' },
    { key: 'total_soap_notes', label: 'SOAP Notes', Icon: FileText, color: '#7c3aed', bg: '#ede9fe' },
    { key: 'total_audio', label: 'Audio Records', Icon: Mic, color: '#d97706', bg: '#fef3c7' },
];

export default function DashboardPage() {
    const [stats, setStats] = useState<Stats | null>(null);
    const [recalls, setRecalls] = useState<Recall[]>([]);
    const [trials, setTrials] = useState<Trial[]>([]);
    const [diseaseStats, setDiseaseStats] = useState<Record<string, number>>({});
    const [trialCondition, setTrialCondition] = useState('hypertension');
    const [trialLoading, setTrialLoading] = useState(false);
    const [loading, setLoading] = useState(true);
    const [recallDrug, setRecallDrug] = useState('');

    useEffect(() => {
        DashboardAPI.get().then(setStats).finally(() => setLoading(false));
        fetchRecalls();
        fetchDiseaseStats();
        fetchTrials('hypertension');
    }, []);

    const fetchRecalls = async (drug = '') => {
        try {
            const r = await api.get('/api/public/drug-recalls', { params: { drug, limit: 5 } });
            setRecalls(r.data.results || []);
        } catch { setRecalls([]); }
    };

    const fetchDiseaseStats = async () => {
        try {
            const r = await api.get('/api/public/disease-stats');
            setDiseaseStats(r.data.covid || {});
        } catch { }
    };

    const fetchTrials = async (cond: string) => {
        setTrialLoading(true);
        try {
            const r = await api.get('/api/public/clinical-trials', { params: { condition: cond, limit: 4 } });
            setTrials(r.data.results || []);
        } catch { setTrials([]); }
        finally { setTrialLoading(false); }
    };

    return (
        <AppLayout>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Clinical Dashboard</h1>
                    <p className="page-subtitle">Hospital-wide operational overview — real-time data</p>
                </div>
                <span className="badge badge-green">
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#16a34a', display: 'inline-block' }} />
                    Live
                </span>
            </div>

            {/* Metric cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                {loading
                    ? Array.from({ length: 4 }).map((_, i) => (
                        <div key={i} className="card metric-card hospital-cross">
                            <div className="skeleton" style={{ height: 16, width: '60%', marginBottom: '0.75rem' }} />
                            <div className="skeleton" style={{ height: 36, width: '40%' }} />
                        </div>
                    ))
                    : METRICS.map((m, i) => (
                        <motion.div key={m.key} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.07 }} className="card metric-card card-hover hospital-cross">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div>
                                    <p className="metric-label">{m.label}</p>
                                    <p className="metric-value" style={{ color: m.color }}>
                                        {((stats as unknown as Record<string, number>)?.[m.key] ?? 0).toLocaleString()}
                                    </p>
                                </div>
                                <div className="metric-icon" style={{ background: m.bg }}>
                                    <m.Icon size={19} color={m.color} strokeWidth={2} />
                                </div>
                            </div>
                        </motion.div>
                    ))
                }
            </div>

            {/* 3 sub-metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                {[
                    { label: 'Visits This Week', value: stats?.visits_7d ?? 0, Icon: TrendingUp, color: '#0066cc' },
                    { label: 'High-Risk Patients', value: stats?.high_risk_patients ?? 0, Icon: AlertTriangle, color: '#c8102e' },
                    { label: 'Chronic Conditions', value: stats?.patients_with_chronic ?? 0, Icon: Heart, color: '#d97706' },
                ].map((m, i) => (
                    <motion.div key={m.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.35 + i * 0.07 }}
                        className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
                        <div style={{ padding: '0.6rem', borderRadius: 8, background: `${m.color}15`, flexShrink: 0 }}>
                            <m.Icon size={18} color={m.color} strokeWidth={2} />
                        </div>
                        <div>
                            <p style={{ color: 'var(--hospital-muted)', fontSize: '0.75rem', margin: '0 0 0.15rem' }}>{m.label}</p>
                            <p style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, color: m.color }}>{m.value}</p>
                        </div>
                    </motion.div>
                ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                {/* Drug Recalls (OpenFDA) */}
                <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="card">
                    <div className="section-header">
                        <AlertCircle size={16} color="#c8102e" />
                        <h2>FDA Drug Recalls</h2>
                        <span className="badge badge-red" style={{ marginLeft: 'auto' }}>OpenFDA</span>
                    </div>
                    <div style={{ padding: '0.875rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                            <input className="input" style={{ flex: 1 }} placeholder="Filter by drug name..."
                                value={recallDrug} onChange={e => setRecallDrug(e.target.value)} />
                            <button className="btn-outline" onClick={() => fetchRecalls(recallDrug)}>
                                <RefreshCw size={14} /> Search
                            </button>
                        </div>
                        {recalls.length === 0 ? (
                            <p style={{ color: 'var(--hospital-muted)', fontSize: '0.875rem', textAlign: 'center', padding: '1rem' }}>No recalls found</p>
                        ) : recalls.map((r, i) => (
                            <div key={i} style={{ padding: '0.625rem 0', borderBottom: i < recalls.length - 1 ? '1px solid var(--hospital-border)' : 'none' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                                    <p style={{ margin: '0 0 0.2rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--hospital-text)', flex: 1 }}>{r.product}</p>
                                    <span className={`badge ${r.class === 'Class I' ? 'badge-red' : r.class === 'Class II' ? 'badge-amber' : 'badge-gray'}`}>{r.class || 'N/A'}</span>
                                </div>
                                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--hospital-muted)' }}>{r.reason}</p>
                                <p style={{ margin: '0.15rem 0 0', fontSize: '0.7rem', color: 'var(--hospital-light)' }}>{r.company} · {r.date}</p>
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Clinical Trials (ClinicalTrials.gov) */}
                <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55 }} className="card">
                    <div className="section-header">
                        <FlaskConical size={16} color="#0066cc" />
                        <h2>Active Clinical Trials</h2>
                        <span className="badge badge-blue" style={{ marginLeft: 'auto' }}>ClinicalTrials.gov</span>
                    </div>
                    <div style={{ padding: '0.875rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                            <input className="input" style={{ flex: 1 }} placeholder="Condition (e.g. diabetes)"
                                value={trialCondition} onChange={e => setTrialCondition(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && fetchTrials(trialCondition)} />
                            <button className="btn-outline" onClick={() => fetchTrials(trialCondition)} disabled={trialLoading}>
                                <RefreshCw size={14} className={trialLoading ? 'animate-spin' : ''} /> {trialLoading ? '...' : 'Fetch'}
                            </button>
                        </div>
                        {trials.length === 0 ? (
                            <p style={{ color: 'var(--hospital-muted)', fontSize: '0.875rem', textAlign: 'center', padding: '1rem' }}>
                                {trialLoading ? 'Loading...' : 'No trials found'}
                            </p>
                        ) : trials.map((t, i) => (
                            <div key={t.nct_id} style={{ padding: '0.625rem 0', borderBottom: i < trials.length - 1 ? '1px solid var(--hospital-border)' : 'none' }}>
                                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.2rem', alignItems: 'flex-start' }}>
                                    <span className="badge badge-blue">{t.nct_id}</span>
                                    <span className="badge badge-green">{t.phase}</span>
                                </div>
                                <p style={{ margin: '0 0 0.15rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--hospital-text)', lineHeight: 1.4 }}>{t.title}</p>
                                <p style={{ margin: 0, fontSize: '0.7rem', color: 'var(--hospital-muted)' }}>{(t.conditions || []).join(', ')}</p>
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Global Disease Stats (disease.sh) */}
                <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="card">
                    <div className="section-header">
                        <Activity size={16} color="#059669" />
                        <h2>Global Disease Surveillance</h2>
                        <span className="badge badge-teal" style={{ marginLeft: 'auto' }}>WHO / disease.sh</span>
                    </div>
                    <div style={{ padding: '1rem' }}>
                        {Object.keys(diseaseStats).length === 0 ? (
                            <p style={{ color: 'var(--hospital-muted)', fontSize: '0.875rem' }}>Loading surveillance data...</p>
                        ) : (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                {[
                                    { label: 'Total Cases', value: diseaseStats.cases, color: '#d97706' },
                                    { label: 'Active', value: diseaseStats.active, color: '#c8102e' },
                                    { label: 'Recovered', value: diseaseStats.recovered, color: '#059669' },
                                    { label: 'Deaths', value: diseaseStats.deaths, color: '#64748b' },
                                ].map(s => (
                                    <div key={s.label} style={{ background: 'var(--hospital-subtle)', borderRadius: 8, padding: '0.75rem' }}>
                                        <p style={{ margin: '0 0 0.2rem', fontSize: '0.72rem', color: 'var(--hospital-muted)', fontWeight: 500 }}>{s.label}</p>
                                        <p style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: s.color }}>{(s.value || 0).toLocaleString()}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </motion.div>

                {/* ICD-10 Quick Lookup */}
                <ICD10Widget />
            </div>
        </AppLayout>
    );
}

function ICD10Widget() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<{ code: string; name: string }[]>([]);
    const [loading, setLoading] = useState(false);

    const search = useCallback(async (q: string) => {
        if (!q.trim()) { setResults([]); return; }
        setLoading(true);
        try {
            const r = await api.get('/api/public/icd10-search', { params: { q } });
            setResults(r.data.results || []);
        } catch { setResults([]); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => {
        const id = setTimeout(() => search(query), 400);
        return () => clearTimeout(id);
    }, [query, search]);

    return (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.65 }} className="card">
            <div className="section-header">
                <BookOpen size={16} color="#7c3aed" />
                <h2>ICD-10 Code Lookup</h2>
                <span className="badge badge-purple" style={{ marginLeft: 'auto' }}>NLM</span>
            </div>
            <div style={{ padding: '0.875rem' }}>
                <input className="input" placeholder="Type a condition (e.g. hypertension)..."
                    value={query} onChange={e => setQuery(e.target.value)} />
                <div style={{ marginTop: '0.75rem' }}>
                    {loading ? (
                        Array.from({ length: 3 }).map((_, i) => (
                            <div key={i} className="skeleton" style={{ height: 32, marginBottom: '0.4rem', borderRadius: 6 }} />
                        ))
                    ) : results.length === 0 && query ? (
                        <p style={{ fontSize: '0.8rem', color: 'var(--hospital-muted)', textAlign: 'center' }}>No results</p>
                    ) : (
                        results.map(r => (
                            <div key={r.code} style={{ display: 'flex', gap: '0.75rem', padding: '0.5rem 0', borderBottom: '1px solid var(--hospital-border)', alignItems: 'center' }}>
                                <span className="badge badge-purple" style={{ fontFamily: 'monospace', minWidth: 64, justifyContent: 'center' }}>{r.code}</span>
                                <span style={{ fontSize: '0.8rem', color: 'var(--hospital-text)' }}>{r.name}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </motion.div>
    );
}
