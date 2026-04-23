'use client';
import { useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    LayoutDashboard, Users, Pill, Mic, BarChart3,
    Database, Settings, ChevronLeft, ChevronRight, LogOut, Cross
} from 'lucide-react';

const NAV = [
    { href: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
    { href: '/patients', label: 'Patients', Icon: Users },
    { href: '/medicines', label: 'Medicines', Icon: Pill },
    { href: '/scriber', label: 'Scriber AI', Icon: Mic },
    { href: '/analytics', label: 'Analytics', Icon: BarChart3 },
    { href: '/database', label: 'Database', Icon: Database },
    { href: '/settings', label: 'Settings', Icon: Settings },
];

export default function Sidebar() {
    const [collapsed, setCollapsed] = useState(false);
    const pathname = usePathname();
    const router = useRouter();

    const logout = () => { localStorage.removeItem('token'); router.push('/login'); };

    return (
        <motion.aside
            animate={{ width: collapsed ? 68 : 232 }}
            transition={{ type: 'spring', stiffness: 280, damping: 30 }}
            style={{
                background: 'linear-gradient(180deg, #0a2342 0%, #0d2d52 100%)',
                display: 'flex', flexDirection: 'column', height: '100vh',
                position: 'sticky', top: 0, flexShrink: 0, overflow: 'hidden',
                boxShadow: '2px 0 12px rgba(10,35,66,0.18)',
            }}
        >
            {/* Logo */}
            <div style={{
                padding: '1.25rem 1rem 1rem',
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                borderBottom: '1px solid rgba(255,255,255,0.08)', minHeight: 70,
            }}>
                <div style={{
                    width: 38, height: 38, borderRadius: 10, flexShrink: 0,
                    background: 'linear-gradient(135deg, #0066cc, #007b91)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    boxShadow: '0 2px 8px rgba(0,102,204,0.4)',
                }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <rect x="9" y="2" width="6" height="20" rx="2" fill="white" />
                        <rect x="2" y="9" width="20" height="6" rx="2" fill="white" />
                    </svg>
                </div>
                <AnimatePresence>
                    {!collapsed && (
                        <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -10 }}
                            transition={{ duration: 0.15 }}
                        >
                            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#fff', whiteSpace: 'nowrap' }}>ScribeAI</div>
                            <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.45)', whiteSpace: 'nowrap', letterSpacing: '0.05em' }}>CLINICAL OS</div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Nav */}
            <nav style={{ flex: 1, padding: '0.875rem 0.625rem', display: 'flex', flexDirection: 'column', gap: '0.2rem', overflowY: 'auto' }}>
                {NAV.map(({ href, label, Icon }) => {
                    const active = pathname === href || pathname.startsWith(href + '/');
                    return (
                        <motion.button
                            key={href}
                            onClick={() => router.push(href)}
                            whileHover={{ x: 1 }}
                            whileTap={{ scale: 0.97 }}
                            style={{
                                display: 'flex', alignItems: 'center',
                                gap: '0.75rem', padding: collapsed ? '0.7rem' : '0.65rem 0.875rem',
                                borderRadius: 9, border: 'none', cursor: 'pointer',
                                width: '100%', justifyContent: collapsed ? 'center' : 'flex-start',
                                background: active ? 'rgba(255,255,255,0.12)' : 'transparent',
                                color: active ? '#fff' : 'rgba(255,255,255,0.5)',
                                position: 'relative', transition: 'background 0.15s, color 0.15s',
                            }}
                            title={collapsed ? label : undefined}
                        >
                            {active && (
                                <motion.div
                                    layoutId="activeBar"
                                    style={{
                                        position: 'absolute', left: 0, top: '15%', bottom: '15%',
                                        width: 3, borderRadius: 2, background: '#4facfe',
                                    }}
                                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                                />
                            )}
                            <Icon size={17} strokeWidth={active ? 2.2 : 1.8} />
                            <AnimatePresence>
                                {!collapsed && (
                                    <motion.span
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.12 }}
                                        style={{ fontSize: '0.85rem', fontWeight: active ? 600 : 400, whiteSpace: 'nowrap' }}
                                    >
                                        {label}
                                    </motion.span>
                                )}
                            </AnimatePresence>
                        </motion.button>
                    );
                })}
            </nav>

            {/* Bottom */}
            <div style={{ padding: '0.625rem', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                <motion.button
                    onClick={() => setCollapsed(!collapsed)}
                    whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                    style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        padding: '0.55rem', borderRadius: 8, border: 'none', cursor: 'pointer',
                        background: 'rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.4)',
                    }}
                    title={collapsed ? 'Expand' : 'Collapse'}
                >
                    {collapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
                </motion.button>
                <motion.button
                    onClick={logout}
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
                    style={{
                        display: 'flex', alignItems: 'center', gap: '0.75rem',
                        padding: collapsed ? '0.55rem' : '0.55rem 0.875rem',
                        justifyContent: collapsed ? 'center' : 'flex-start',
                        borderRadius: 8, border: 'none', cursor: 'pointer',
                        background: 'transparent', color: 'rgba(255,255,255,0.4)', width: '100%',
                    }}
                    title="Logout"
                >
                    <LogOut size={15} />
                    <AnimatePresence>
                        {!collapsed && (
                            <motion.span
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                style={{ fontSize: '0.85rem', whiteSpace: 'nowrap' }}
                            >
                                Logout
                            </motion.span>
                        )}
                    </AnimatePresence>
                </motion.button>
            </div>
        </motion.aside>
    );
}
