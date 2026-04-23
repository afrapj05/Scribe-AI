'use client';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import AppLayout from '../../components/AppLayout';
import api, { Analytics } from '../../lib/api';

const TEAL = '#00d4aa'; const BLUE = '#4facfe'; const PURPLE = '#a78bfa';
const PIE_COLORS = ['var(--blue-500)', 'var(--teal-500)', 'var(--purple-500)', 'var(--red-500)', 'var(--orange-500)'];

interface AnalyticsData {
    summary: {
        total_patients: number;
        total_visits: number;
        visits_7d: number;
        avg_age: number;
    };
    top_diagnoses: { name: string; count: number }[];
    demographics: {
        age_distribution: { name: string; count: number }[];
        gender_distribution: { name: string; count: number }[];
    };
    volume: { date: string; count: number }[];
    department: { name: string; count: number }[];
}

function ChartCard({ title, children, delay = 0, cls = "" }: { title: string; children: React.ReactNode; delay?: number; cls?: string }) {
    return (
        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
            className={`card ${cls}`} style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ width: 4, height: 16, borderRadius: 2, background: 'var(--blue-500)' }} />
                {title}
            </h3>
            {children}
        </motion.div>
    );
}

export default function AnalyticsPage() {
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/api/analytics').then((res: any) => setData(res.data)).finally(() => setLoading(false));
    }, []);

    if (loading) return (
        <AppLayout>
            <div className="page-header">
                <div>
                    <p className="breadcrumb">Clinical Insights &rsaquo; Real-time</p>
                    <h1 className="page-title">Analytics</h1>
                </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                {[0, 1, 2, 3].map(i => (
                    <div key={i} className="card" style={{ height: 300 }}>
                        <div className="skeleton" style={{ height: '100%', width: '100%' }} />
                    </div>
                ))}
            </div>
        </AppLayout>
    );

    const empty = !data || data.summary.total_patients === 0;

    return (
        <AppLayout>
            <div className="page-header">
                <div>
                    <p className="breadcrumb">Clinical Insights &rsaquo; Real-time</p>
                    <h1 className="page-title">Analytics Dashboard</h1>
                    <p className="page-subtitle">Population health and clinical volume metrics · Live from EHR</p>
                </div>
            </div>

            {empty ? (
                <div className="card" style={{ padding: '4rem 2rem', textAlign: 'center', border: '2px dashed var(--border)' }}>
                    <p style={{ color: 'var(--text-muted)' }}>No clinical data recorded yet. Start documenting visits to see analytics.</p>
                </div>
            ) : (
                <>
                    {/* Metrics Row */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '1.5rem' }}>
                        {[
                            { label: 'Total Registry', value: data.summary.total_patients, icon: 'PAT' },
                            { label: 'Total Encounters', value: data.summary.total_visits, icon: 'VIS' },
                            { label: 'Last 7 Days', value: data.summary.visits_7d, icon: 'NEW' },
                            { label: 'Avg Patient Age', value: Math.round(data.summary.avg_age), icon: 'AGE' },
                        ].map((m, i) => (
                            <motion.div key={m.label} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}
                                className="card" style={{ padding: '1rem 1.25rem', borderLeft: '4px solid var(--blue-500)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{m.label}</p>
                                    <span className="badge badge-blue mono" style={{ fontSize: '0.65rem' }}>{m.icon}</span>
                                </div>
                                <p style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0.25rem 0 0', color: 'var(--text-primary)' }}>{m.value}</p>
                            </motion.div>
                        ))}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
                        {/* Visit Volume trend */}
                        <ChartCard title="Clinical Volume (Last 30 Days)" delay={0.1} cls="card-blue">
                            <ResponsiveContainer width="100%" height={240}>
                                <BarChart data={data.volume}>
                                    <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <Tooltip contentStyle={{ borderRadius: 10, border: 'none', boxShadow: 'var(--shadow-lg)' }} />
                                    <Bar dataKey="count" fill="var(--blue-500)" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </ChartCard>

                        {/* Top Diagnoses */}
                        <ChartCard title="Top Diagnoses" delay={0.15}>
                            <ResponsiveContainer width="100%" height={240}>
                                <BarChart data={data.top_diagnoses.slice(0, 8)} layout="vertical">
                                    <XAxis type="number" hide />
                                    <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} width={120} axisLine={false} tickLine={false} />
                                    <Tooltip contentStyle={{ borderRadius: 10, border: 'none', boxShadow: 'var(--shadow-lg)' }} />
                                    <Bar dataKey="count" fill="var(--teal-500)" radius={[0, 4, 4, 0]} barSize={20} />
                                </BarChart>
                            </ResponsiveContainer>
                        </ChartCard>

                        {/* Age Distribution */}
                        <ChartCard title="Patient Demographics: Age" delay={0.2}>
                            <ResponsiveContainer width="100%" height={240}>
                                <BarChart data={data.demographics.age_distribution}>
                                    <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                                    <YAxis hide />
                                    <Tooltip contentStyle={{ borderRadius: 10, border: 'none', boxShadow: 'var(--shadow-lg)' }} />
                                    <Bar dataKey="count" fill="var(--purple-500)" radius={[4, 4, 0, 0]} barSize={30} />
                                </BarChart>
                            </ResponsiveContainer>
                        </ChartCard>

                        {/* Department Split */}
                        <ChartCard title="Case Load by Department" delay={0.25}>
                            <ResponsiveContainer width="100%" height={240}>
                                <PieChart>
                                    <Pie data={data.department} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={50} paddingAngle={5}>
                                        {data.department.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                                    </Pie>
                                    <Legend wrapperStyle={{ fontSize: '0.75rem', fontWeight: 600 }} />
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </ChartCard>
                    </div>
                </>
            )}
        </AppLayout>
    );
}
