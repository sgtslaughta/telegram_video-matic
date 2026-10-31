import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { withToast } from '@/lib/toast';
import { notifications } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, } from '@/components/ui/select';
import { NotificationTargets } from './NotificationTargets';
import { SettingsSection } from './SettingsSection';
const HOURS = Array.from({ length: 24 }, (_, h) => h);
const hh = (h) => `${String(h).padStart(2, '0')}:00`;
function HourSelect({ id, label, value, onChange }) {
    return (_jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: id, className: "text-[13px]", children: label }), _jsxs(Select, { value: String(value), onValueChange: (v) => onChange(Number(v)), children: [_jsx(SelectTrigger, { id: id, className: "h-9 w-28 text-[13px]", children: _jsx(SelectValue, {}) }), _jsx(SelectContent, { children: HOURS.map((h) => (_jsx(SelectItem, { value: String(h), children: hh(h) }, h))) })] })] }));
}
const sub = 'text-[13px] font-semibold';
const help = 'text-[12px] text-muted-foreground';
const field = 'h-9 text-[13px]';
function OptionsForm({ initial }) {
    const qc = useQueryClient();
    const [opts, setOpts] = useState(initial);
    const dirty = JSON.stringify(opts) !== JSON.stringify(initial);
    const save = useMutation({
        mutationFn: () => notifications.saveOptions(opts),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
    });
    const setQuiet = (p) => setOpts({ ...opts, quiet: { ...opts.quiet, ...p } });
    return (_jsxs("div", { className: "space-y-4", children: [_jsx("h3", { className: sub, children: "Options" }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx(Switch, { id: "quiet-enabled", checked: opts.quiet.enabled, onCheckedChange: (c) => setQuiet({ enabled: c }) }), _jsx(Label, { htmlFor: "quiet-enabled", className: "text-[13px]", children: "Quiet hours" })] }), _jsxs("div", { className: "flex gap-4", children: [_jsx(HourSelect, { id: "quiet-start", label: "Start", value: opts.quiet.start, onChange: (v) => setQuiet({ start: v }) }), _jsx(HourSelect, { id: "quiet-end", label: "End", value: opts.quiet.end, onChange: (v) => setQuiet({ end: v }) })] }), _jsx("p", { className: help, children: "Arrivals are held and sent as one summary when quiet hours end. Errors still send immediately." }), _jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: "disk-low", className: "text-[13px]", children: "Disk low threshold (%)" }), _jsx(Input, { id: "disk-low", type: "number", min: 50, max: 100, className: `${field} max-w-xs`, value: opts.disk_low_pct, onChange: (e) => setOpts({ ...opts, disk_low_pct: Number(e.target.value) }) })] }), _jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: "public-url", className: "text-[13px]", children: "Public URL" }), _jsx(Input, { id: "public-url", className: `${field} max-w-md`, value: opts.public_url, onChange: (e) => setOpts({ ...opts, public_url: e.target.value }) }), _jsx("p", { className: help, children: "Used for links in notifications, e.g. http://192.168.1.96:8000" })] }), dirty && (_jsx("div", { className: "flex justify-end", children: _jsx(Button, { size: "sm", onClick: () => withToast(() => save.mutateAsync(), { success: 'Notification options saved' }), disabled: save.isPending, children: "Save changes" }) }))] }));
}
function JellyfinForm({ initial }) {
    const qc = useQueryClient();
    const [url, setUrl] = useState(initial.url);
    const [libraryId, setLibraryId] = useState(initial.library_id);
    const [apiKey, setApiKey] = useState('');
    const dirty = url !== initial.url || libraryId !== initial.library_id || apiKey !== '';
    const save = useMutation({
        mutationFn: () => notifications.saveJellyfin({ url, library_id: libraryId, ...(apiKey ? { api_key: apiKey } : {}) }),
        onSuccess: () => { setApiKey(''); qc.invalidateQueries({ queryKey: ['notifications'] }); },
    });
    const test = useMutation({ mutationFn: () => notifications.testJellyfin() });
    return (_jsxs("div", { className: "space-y-4", children: [_jsx("h3", { className: sub, children: "Jellyfin" }), _jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: "jf-url", className: "text-[13px]", children: "URL" }), _jsx(Input, { id: "jf-url", className: `${field} max-w-md`, value: url, onChange: (e) => setUrl(e.target.value) })] }), _jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: "jf-lib", className: "text-[13px]", children: "Library ID" }), _jsx(Input, { id: "jf-lib", className: `${field} max-w-md`, value: libraryId, onChange: (e) => setLibraryId(e.target.value) }), _jsx("p", { className: help, children: "Leave empty to refresh all libraries." })] }), _jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: "jf-key", className: "text-[13px]", children: "API key" }), _jsx(Input, { id: "jf-key", type: "password", className: `${field} max-w-md`, value: apiKey, placeholder: initial.api_key_set ? 'Saved, leave empty to keep' : '', onChange: (e) => setApiKey(e.target.value) })] }), _jsxs("div", { className: "flex justify-end gap-2", children: [_jsx(Button, { size: "sm", variant: "outline", disabled: test.isPending, onClick: () => withToast(() => test.mutateAsync(), { success: 'Jellyfin refresh started' }), children: "Test refresh" }), dirty && (_jsx(Button, { size: "sm", disabled: save.isPending, onClick: () => withToast(() => save.mutateAsync(), { success: 'Jellyfin settings saved' }), children: "Save changes" }))] })] }));
}
export function NotificationsSettings() {
    const { data } = useQuery({ queryKey: ['notifications'], queryFn: notifications.get });
    return (_jsx(SettingsSection, { id: "notifications", title: "Notifications", description: "Send alerts through Apprise and refresh Jellyfin after new downloads.", children: data ? (_jsxs("div", { className: "divide-y divide-border [&>*]:py-5 [&>:first-child]:pt-0 [&>:last-child]:pb-0", children: [_jsx(NotificationTargets, { triggers: data.triggers, targets: data.targets }), _jsx(OptionsForm, { initial: data.options }, JSON.stringify(data.options)), _jsx(JellyfinForm, { initial: data.jellyfin })] })) : (_jsx("p", { className: "text-[13px] text-muted-foreground", children: "Loading notifications\u2026" })) }));
}
