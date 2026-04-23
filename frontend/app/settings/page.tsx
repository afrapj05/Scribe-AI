'use client';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import AppLayout from '../../components/AppLayout';
import { Translations } from '../../lib/api';

interface Lang { code: string; label: string; }

export default function SettingsPage() {
    const [langs, setLangs] = useState<Lang[]>([]);
    const [selectedLang, setSelectedLang] = useState('en');
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        const stored = localStorage.getItem('ui_lang') || 'en';
        setSelectedLang(stored);
        Translations.languages().then((r: { languages: Record<string, string> }) => {
            setLangs(Object.entries(r.languages).map(([code, label]) => ({ code, label })));
        });
    }, []);

    const save = () => {
        localStorage.setItem('ui_lang', selectedLang);
        setSaved(true);
        setTimeout(() => setSaved(false), 2500);
    };

    return (
        <AppLayout>
            <div style={{ marginBottom: '2rem' }}>
                <h1 className="page-title gradient-text">Settings</h1>
                <p className="page-subtitle">Application preferences</p>
            </div>

            <div style={{ maxWidth: 600 }}>
                <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                    className="glass" style={{ padding: '1.75rem', marginBottom: '1rem' }}>
                    <h2 style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '1.25rem', color: '#e2e8f0' }}>Language</h2>
                    <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.75rem' }}>
                        Select the UI language. All 22 official Indian languages are supported via Google Translate.
                    </p>
                    <select className="input" style={{ maxWidth: 320 }} value={selectedLang} onChange={e => setSelectedLang(e.target.value)}>
                        {langs.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
                    </select>
                </motion.div>

                <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}
                    className="glass" style={{ padding: '1.75rem', marginBottom: '1rem' }}>
                    <h2 style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.75rem', color: '#e2e8f0' }}>About</h2>
                    <div style={{ display: 'grid', gap: '0.5rem', fontSize: '0.875rem', color: '#94a3b8' }}>
                        {[
                            ['Application', 'ScribeAI Clinical OS v2.0'],
                            ['Backend', 'FastAPI + Python'],
                            ['Frontend', 'Next.js 14 + Framer Motion'],
                            ['Database', 'SQLite (SQLAlchemy)'],
                            ['AI Model', 'BioMistral via Ollama (local)'],
                            ['Speech', 'OpenAI Whisper (local)'],
                        ].map(([k, v]) => (
                            <div key={k} style={{ display: 'flex', gap: '1rem' }}>
                                <span style={{ color: '#64748b', minWidth: 100 }}>{k}</span>
                                <span style={{ color: '#e2e8f0' }}>{v}</span>
                            </div>
                        ))}
                    </div>
                </motion.div>

                <motion.button className="btn-primary" onClick={save}
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
                    style={{ marginTop: '0.5rem' }}>
                    {saved ? 'Saved!' : 'Save Preferences'}
                </motion.button>
            </div>
        </AppLayout>
    );
}
