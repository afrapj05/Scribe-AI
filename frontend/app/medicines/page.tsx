'use client';
import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Search, ChevronLeft, ChevronRight, Package } from 'lucide-react';
import AppLayout from '../../components/AppLayout';
import api, { Medicines } from '../../lib/api';

const MedIcon = () => (
    <div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--blue-50)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--blue-500)' }}>
        <Package size={20} />
    </div>
);

interface MedItem {
    id: string; name: string; category: string; form: string;
    manufacturer: string; price?: number; discontinued: boolean;
}

export default function MedicinesPage() {
    const [data, setData] = useState<{ items: MedItem[]; total: number; total_pages: number; source?: string } | null>(null);
    const [search, setSearch] = useState('');
    const [page, setPage] = useState(1);
    const [category, setCategory] = useState('All');
    const [categories, setCategories] = useState<string[]>(['All']);
    const [loading, setLoading] = useState(true);

    // Interaction Checker state
    const [interactionQuery, setInteractionQuery] = useState('');
    const [interactions, setInteractions] = useState<{ drugs: string[]; severity: string; warning: string }[]>([]);
    const [checking, setChecking] = useState(false);

    useEffect(() => {
        Medicines.categories().then((r: { categories: string[] }) => setCategories(['All', ...r.categories.slice(0, 60)]));
    }, []);

    const load = useCallback(() => {
        setLoading(true);
        Medicines.list({ search, page, page_size: 50, category })
            .then(setData)
            .finally(() => setLoading(false));
    }, [search, page, category]);

    useEffect(() => { const id = setTimeout(load, 300); return () => clearTimeout(id); }, [load]);
    useEffect(() => { setPage(1); }, [search, category]);

    const checkInteractions = async () => {
        if (!interactionQuery.trim()) return;
        setChecking(true);
        try {
            const r = await api.get('/api/medicines/interactions', { params: { drugs: interactionQuery } });
            setInteractions(r.data.interactions);
        } catch { } finally { setChecking(false); }
    };

    return (
        <AppLayout>
            <div className="page-header">
                <div>
                    <p className="breadcrumb">Pharmacy &rsaquo; Formulary</p>
                    <h1 className="page-title">Medicines & Pharmacy</h1>
                    <p className="page-subtitle">Standardized drug database and interaction safety checks</p>
                </div>
                <div style={{ display: 'flex', gap: '0.875rem' }}>
                    <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12, padding: '0.4rem 0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem', boxShadow: 'var(--shadow-sm)' }}>
                        <Search size={14} color="var(--blue-500)" />
                        <input style={{ border: 'none', background: 'none', fontSize: '0.85rem', fontWeight: 500, outline: 'none', color: 'var(--text-primary)', width: 140 }}
                            placeholder="Find drug..." value={search} onChange={e => setSearch(e.target.value)} />
                    </div>
                    <select className="input" style={{ width: 'auto', minWidth: 140 }} value={category} onChange={e => setCategory(e.target.value)}>
                        {categories.map(c => <option key={c}>{c}</option>)}
                    </select>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem', alignItems: 'start' }}>
                <div className="card" style={{ padding: 0 }}>
                    <div className="table-wrap">
                        <table style={{ border: 'none' }}>
                            <thead>
                                <tr>{['Drug Name', 'Category', 'Form', 'Price', 'Status'].map(h => <th key={h}>{h}</th>)}</tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    Array.from({ length: 12 }).map((_, i) => (
                                        <tr key={i}>
                                            {Array.from({ length: 5 }).map((_, j) => (
                                                <td key={j}><div className="skeleton" style={{ height: 16, width: '80%' }} /></td>
                                            ))}
                                        </tr>
                                    ))
                                ) : (data?.items ?? []).length === 0 ? (
                                    <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '4rem' }}>No medicines found matching your criteria.</td></tr>
                                ) : (
                                    (data?.items ?? []).map((m, i) => (
                                        <motion.tr key={m.id || i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: Math.min(i, 20) * 0.015 }}>
                                            <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{m.name}</td>
                                            <td><span className="badge badge-blue">{m.category || 'General'}</span></td>
                                            <td style={{ color: 'var(--text-secondary)' }}>{m.form || '—'}</td>
                                            <td style={{ fontWeight: 600 }}>{m.price != null ? `₹${m.price}` : '—'}</td>
                                            <td>{m.discontinued ? <span className="badge badge-red">Inactive</span> : <span className="badge badge-green">Available</span>}</td>
                                        </motion.tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>

                    {data && data.total_pages > 1 && (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem 1.25rem', borderTop: '1px solid var(--border)', background: 'var(--bg-subtle)' }}>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Page {page} of {data.total_pages}</span>
                            <div style={{ display: 'flex', gap: '0.4rem' }}>
                                <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}><ChevronLeft size={14} /></button>
                                <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => Math.min(data.total_pages, p + 1))} disabled={page >= data.total_pages}><ChevronRight size={14} /></button>
                            </div>
                        </div>
                    )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    <div className="card card-red" style={{ padding: '1.25rem' }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--red-600)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--red-600)', animation: 'pulse 1.5s infinite' }} />
                            Interaction Checker
                        </h3>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>Enter comma-separated drugs to check for high-risk combinations.</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            <textarea className="input" rows={3} placeholder="e.g. Aspirin, Warfarin"
                                value={interactionQuery} onChange={e => setInteractionQuery(e.target.value)} />
                            <motion.button className="btn btn-danger btn-sm" onClick={checkInteractions} disabled={checking} whileTap={{ scale: 0.98 }}>
                                {checking ? 'Checking Safety...' : 'Run Safety Check'}
                            </motion.button>
                        </div>

                        {interactions.length > 0 && (
                            <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                {interactions.map((it, i) => (
                                    <div key={i} style={{ padding: '0.875rem', background: '#fff', border: '1px solid #fecaca', borderRadius: 10 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                                            <span style={{ fontSize: '0.7rem', fontWeight: 900, color: 'var(--red-600)', textTransform: 'uppercase' }}>High Risk</span>
                                        </div>
                                        <p style={{ fontSize: '0.8rem', fontWeight: 700, margin: '0 0 0.25rem', color: 'var(--text-primary)' }}>{it.drugs.join(' + ')}</p>
                                        <p style={{ fontSize: '0.75rem', lineHeight: 1.4, color: 'var(--text-secondary)' }}>{it.warning}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                        {interactions.length === 0 && !checking && interactionQuery && (
                            <div style={{ marginTop: '1rem', textAlign: 'center', padding: '1rem', background: 'var(--green-50)', borderRadius: 10, border: '1px solid var(--green-100)' }}>
                                <p style={{ fontSize: '0.75rem', color: 'var(--green-600)', fontWeight: 600 }}>No known major interactions found for these specific drugs.</p>
                            </div>
                        )}
                    </div>

                    <div className="card" style={{ padding: '1.25rem' }}>
                        <h4 style={{ fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.75rem' }}>Database Info</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border)' }}>
                                <span style={{ color: 'var(--text-muted)' }}>Source</span>
                                <span style={{ fontWeight: 600 }}>{data?.source || 'Registry'}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                                <span style={{ color: 'var(--text-muted)' }}>Latest Update</span>
                                <span style={{ fontWeight: 600 }}>{new Date().toLocaleDateString()}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}
