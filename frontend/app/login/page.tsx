'use client';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Lock, User } from 'lucide-react';
import { Auth } from '../../lib/api';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const router = useRouter();

    useEffect(() => {
        if (typeof window !== 'undefined' && localStorage.getItem('token')) router.replace('/dashboard');
    }, [router]);

    const handleLogin = async () => {
        if (!username || !password) { setError('Please enter username and password'); return; }
        setLoading(true); setError('');
        try {
            const { token } = await Auth.login(username, password);
            localStorage.setItem('token', token);
            router.push('/dashboard');
        } catch {
            setError('Invalid credentials. Use the demo accounts below.');
        } finally { setLoading(false); }
    };

    return (
        <div style={{
            minHeight: '100vh', background: 'linear-gradient(135deg, #0a2342 0%, #0d3060 60%, #0a4a6e 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden',
        }}>
            {/* Medical cross pattern background */}
            <div style={{ position: 'absolute', inset: 0, opacity: 0.04 }}>
                {Array.from({ length: 30 }).map((_, i) => (
                    <span key={i} style={{
                        position: 'absolute',
                        left: `${(i % 6) * 17 + 5}%`,
                        top: `${Math.floor(i / 6) * 22 + 8}%`,
                        fontSize: '2rem', fontWeight: 900, color: '#fff',
                        userSelect: 'none', lineHeight: 1,
                    }}>+</span>
                ))}
            </div>

            <div style={{ display: 'flex', width: '100%', maxWidth: 960, height: '100%', alignItems: 'center', justifyContent: 'center', gap: '3rem', padding: '2rem' }}>
                {/* Branding panel */}
                <motion.div
                    initial={{ opacity: 0, x: -30 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                    style={{ flex: 1, maxWidth: 380, color: '#fff' }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem', marginBottom: '2rem' }}>
                        <div style={{
                            width: 52, height: 52, borderRadius: 14,
                            background: 'linear-gradient(135deg, #0066cc, #007b91)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            boxShadow: '0 4px 20px rgba(0,102,204,0.5)',
                        }}>
                            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                                <rect x="9" y="2" width="6" height="20" rx="2" fill="white" />
                                <rect x="2" y="9" width="20" height="6" rx="2" fill="white" />
                            </svg>
                        </div>
                        <div>
                            <div style={{ fontWeight: 800, fontSize: '1.4rem', letterSpacing: '-0.02em' }}>ScribeAI</div>
                            <div style={{ fontSize: '0.75rem', opacity: 0.6, letterSpacing: '0.12em', textTransform: 'uppercase' }}>Clinical OS</div>
                        </div>
                    </div>

                    <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1rem', lineHeight: 1.2, letterSpacing: '-0.02em' }}>
                        Ambient Clinical<br />Voice Documentation
                    </h1>
                    <p style={{ opacity: 0.65, lineHeight: 1.7, fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                        Powered by phi3:mini — local AI for zero data leakage. Supports Hindi, Tamil, Telugu, Malayalam, and 6 more Indian languages via real-time speech recognition.
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                        {[
                            'Live multilingual speech-to-text',
                            'AI-generated SOAP notes (phi3:mini)',
                            'FDA drug recalls & clinical trials',
                            'ICD-10 & RxNorm real-time lookup',
                            'ABDM compliant — fully local AI',
                        ].map(f => (
                            <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.85rem', opacity: 0.8 }}>
                                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#4facfe', flexShrink: 0 }} />
                                {f}
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Login card */}
                <motion.div
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                    style={{
                        width: '100%', maxWidth: 380,
                        background: '#fff', borderRadius: 18,
                        padding: '2rem 2rem 1.75rem',
                        boxShadow: '0 20px 60px rgba(0,0,0,0.35)',
                    }}
                >
                    <h2 style={{ fontWeight: 700, fontSize: '1.25rem', margin: '0 0 0.3rem', color: 'var(--hospital-text)' }}>Sign In</h2>
                    <p style={{ color: 'var(--hospital-muted)', fontSize: '0.8rem', margin: '0 0 1.5rem' }}>Access the clinical workstation</p>

                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ fontSize: '0.775rem', color: 'var(--hospital-muted)', display: 'block', marginBottom: '0.35rem', fontWeight: 500 }}>Username</label>
                        <div style={{ position: 'relative' }}>
                            <User size={14} style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--hospital-light)' }} />
                            <input className="input" style={{ paddingLeft: '2.4rem' }} placeholder="e.g. dr_sharma"
                                value={username} onChange={e => setUsername(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleLogin()} autoFocus />
                        </div>
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ fontSize: '0.775rem', color: 'var(--hospital-muted)', display: 'block', marginBottom: '0.35rem', fontWeight: 500 }}>Password</label>
                        <div style={{ position: 'relative' }}>
                            <Lock size={14} style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--hospital-light)' }} />
                            <input className="input" type="password" style={{ paddingLeft: '2.4rem' }} placeholder="Enter password"
                                value={password} onChange={e => setPassword(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleLogin()} />
                        </div>
                    </div>

                    {error && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                            className="alert alert-error" style={{ marginBottom: '1rem' }}>
                            {error}
                        </motion.div>
                    )}

                    <button className="btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '0.75rem' }}
                        onClick={handleLogin} disabled={loading}>
                        {loading ? (
                            <span style={{ display: 'inline-block', width: 16, height: 16, border: '2px solid #fff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin360 0.8s linear infinite' }} />
                        ) : 'Sign In'}
                    </button>
                    <style>{`@keyframes spin360{to{transform:rotate(360deg)}}`}</style>

                    <div style={{ marginTop: '1.25rem', padding: '0.875rem', background: '#f4f7fb', borderRadius: 10, border: '1px solid var(--hospital-border)' }}>
                        <p style={{ fontSize: '0.72rem', color: 'var(--hospital-muted)', margin: '0 0 0.5rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Demo Accounts</p>
                        {[
                            ['dr_sharma', 'password123', 'Senior Physician'],
                            ['dr_patel', 'password456', 'Cardiologist'],
                            ['nurse_verma', 'password789', 'Registered Nurse'],
                        ].map(([u, p, role]) => (
                            <motion.div key={u} whileHover={{ x: 2 }} onClick={() => { setUsername(u); setPassword(p); }}
                                style={{ cursor: 'pointer', fontSize: '0.75rem', padding: '0.2rem 0', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <span style={{ color: 'var(--hospital-blue)', fontWeight: 600, minWidth: 90 }}>{u}</span>
                                <span style={{ color: 'var(--hospital-light)' }}>{p}</span>
                                <span className="badge badge-gray" style={{ marginLeft: 'auto' }}>{role}</span>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
