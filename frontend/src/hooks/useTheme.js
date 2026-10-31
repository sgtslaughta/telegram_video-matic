import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext, useEffect, useState } from 'react';
import { useUpdateSettings } from './useSettings';
const ThemeContext = createContext(undefined);
export function ThemeProvider({ children }) {
    const [theme, setTheme] = useState('system');
    const [effectiveTheme, setEffectiveTheme] = useState('light');
    const updateSettings = useUpdateSettings();
    useEffect(() => {
        const stored = localStorage.getItem('theme');
        if (stored) {
            setTheme(stored);
        }
    }, []);
    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const updateEffective = () => {
            let resolved;
            if (theme === 'system') {
                resolved = mediaQuery.matches ? 'dark' : 'light';
            }
            else {
                resolved = theme;
            }
            setEffectiveTheme(resolved);
            document.documentElement.classList.toggle('dark', resolved === 'dark');
        };
        updateEffective();
        if (theme === 'system') {
            mediaQuery.addEventListener('change', updateEffective);
            return () => mediaQuery.removeEventListener('change', updateEffective);
        }
    }, [theme]);
    const toggleTheme = () => {
        const next = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light';
        setTheme(next);
        localStorage.setItem('theme', next);
        updateSettings.mutate({ theme: next });
    };
    const handleSetTheme = (t) => {
        setTheme(t);
        localStorage.setItem('theme', t);
        updateSettings.mutate({ theme: t });
    };
    return (_jsx(ThemeContext.Provider, { value: { theme, toggleTheme, setTheme: handleSetTheme, effectiveTheme }, children: children }));
}
export function useTheme() {
    const ctx = useContext(ThemeContext);
    if (!ctx) {
        throw new Error('useTheme must be used inside ThemeProvider');
    }
    return ctx;
}
