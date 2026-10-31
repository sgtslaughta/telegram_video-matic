import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useTheme } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';
import AccentPicker from '@/components/AccentPicker';
import { Field, SettingsSection } from './SettingsSection';
const THEMES = [['light', 'Light'], ['dark', 'Dark'], ['system', 'System']];
export function AppearanceSection() {
    const { theme, setTheme } = useTheme();
    return (_jsxs(SettingsSection, { id: "appearance", title: "Appearance", description: "Applies immediately and is remembered on this device.", children: [_jsx(Field, { id: "theme", label: "Theme", children: _jsx("div", { role: "radiogroup", "aria-label": "Theme", id: "theme", className: "inline-flex rounded-md border border-border p-0.5 text-[13px]", children: THEMES.map(([v, l]) => (_jsx("button", { role: "radio", "aria-checked": theme === v, onClick: () => setTheme(v), className: cn('rounded px-3 py-1 transition-colors', theme === v ? 'bg-brand/10 font-medium text-brand' : 'text-muted-foreground hover:text-foreground'), children: l }, v))) }) }), _jsx(Field, { id: "accent", label: "Accent color", children: _jsx(AccentPicker, {}) })] }));
}
