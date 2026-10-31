export const ACCENTS = [
    { name: 'telegram', label: 'Telegram blue', swatch: '#229ed9', primary: '' },
    { name: 'violet', label: 'Violet', swatch: '#7c5cff', primary: '252 89% 62.7%' },
    { name: 'graphite', label: 'Graphite', swatch: '#18181b', primary: 'var(--foreground)' },
];
export const DEFAULT_ACCENT = 'telegram';
export function applyAccent(name) {
    const a = ACCENTS.find((x) => x.name === name) ?? ACCENTS[0];
    const root = document.documentElement;
    if (!a.primary) {
        // Default Telegram blue: the theme tokens already define light/dark variants.
        for (const v of ['--primary', '--primary-foreground', '--ring', '--brand'])
            root.style.removeProperty(v);
        return;
    }
    root.style.setProperty('--primary', a.primary);
    root.style.setProperty('--brand', a.primary);
    root.style.setProperty('--ring', a.primary);
    root.style.setProperty('--primary-foreground', a.name === 'graphite' ? 'var(--background)' : '0 0% 100%');
}
