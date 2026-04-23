'use client';
import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';

function Clock() {
    const [time, setTime] = useState('');
    const [date, setDate] = useState('');
    useEffect(() => {
        const tick = () => {
            const now = new Date();
            setTime(now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
            setDate(now.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }));
        };
        tick();
        const id = setInterval(tick, 1000);
        return () => clearInterval(id);
    }, []);
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', fontWeight: 400 }}>{date}</span>
            <span style={{
                fontSize: '0.9rem', fontWeight: 800, letterSpacing: '0.06em',
                color: 'var(--blue-500)', fontVariantNumeric: 'tabular-nums',
                background: 'var(--blue-50)', padding: '0.25rem 0.625rem',
                borderRadius: 8, border: '1px solid #c7ddf7',
            }}>{time}</span>
        </div>
    );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [ready, setReady] = useState(false);
    const [user, setUser] = useState('');

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) { router.replace('/login'); return; }
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            setUser(payload?.user?.name || payload?.sub || 'Clinician');
        } catch { setUser('Clinician'); }
        setReady(true);
    }, [router]);

    const PAGE_NAMES: Record<string, string> = {
        '/dashboard': 'Clinical Dashboard',
        '/patients': 'Patient Registry',
        '/medicines': 'Medicine Directory',
        '/scriber': 'Scriber AI',
        '/scan-report': 'Report Scanner',
        '/analytics': 'Analytics',
        '/database': 'Database',
        '/settings': 'Settings',
    };

    const pageName = PAGE_NAMES[pathname] || pathname.replace('/', '') || 'Home';

    if (!ready) return (
        <div className="page-bg" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
            <div style={{ textAlign: 'center' }}>
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }}
                    style={{ width: 40, height: 40, border: '3px solid #d8e2f0', borderTopColor: 'var(--blue-500)', borderRadius: '50%', margin: '0 auto 1rem' }}
                />
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Initialising Clinical OS…</p>
            </div>
        </div>
    );

    return (
        <div style={{ display: 'flex', minHeight: '100vh' }}>
            <Sidebar />

            <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
                {/* ── Top bar ── */}
                <header style={{
                    background: '#fff',
                    borderBottom: '1px solid var(--border)',
                    height: 58, padding: '0 1.75rem',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    boxShadow: '0 1px 6px rgba(6,23,46,0.05)',
                    position: 'sticky', top: 0, zIndex: 100, flexShrink: 0,
                }}>
                    {/* Breadcrumb */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{ width: 28, height: 28, borderRadius: 7, background: 'var(--blue-50)', border: '1px solid #c7ddf7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            {/* Medical cross mini */}
                            <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                                <rect x="5" y="1" width="4" height="12" rx="1.5" fill="var(--blue-500)" />
                                <rect x="1" y="5" width="12" height="4" rx="1.5" fill="var(--blue-500)" />
                            </svg>
                        </div>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 400 }}>ScribeAI</span>
                        <span style={{ color: 'var(--border)', fontSize: '0.9rem' }}>/</span>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 600 }}>{pageName}</span>
                    </div>

                    {/* Right side */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                        <Clock />

                        {/* System status */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: '0.3rem 0.75rem' }}>
                            <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e', display: 'inline-block', boxShadow: '0 0 0 2px rgba(34,197,94,0.3)' }} />
                            <span style={{ fontSize: '0.74rem', color: '#15803d', fontWeight: 600 }}>All Systems Operational</span>
                        </div>

                        {/* User chip */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-subtle)', border: '1px solid var(--border)', borderRadius: 99, padding: '0.25rem 0.75rem 0.25rem 0.3rem' }}>
                            <div style={{ width: 26, height: 26, borderRadius: '50%', background: 'var(--grad-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', color: '#fff', fontWeight: 700 }}>
                                {user.charAt(0).toUpperCase()}
                            </div>
                            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)' }}>{user}</span>
                        </div>
                    </div>
                </header>

                {/* ── Main content ── */}
                <main className="page-bg" style={{ flex: 1, overflowY: 'auto' }}>
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={pathname}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -6 }}
                            transition={{ duration: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
                            style={{ padding: '1.75rem 2rem', maxWidth: 1440, width: '100%', margin: '0 auto' }}
                        >
                            {children}
                        </motion.div>
                    </AnimatePresence>
                </main>

                {/* ── Footer ── */}
                <footer style={{
                    background: '#fff', borderTop: '1px solid var(--border)',
                    padding: '0.5rem 1.75rem',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        ScribeAI Clinical OS v2.1 &nbsp;·&nbsp; BioMistral + qwen2.5vl &nbsp;·&nbsp; ABDM Compliant &nbsp;·&nbsp; SQLite
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        No PHI transmitted — all AI runs locally
                    </span>
                </footer>
            </div>
        </div>
    );
}
