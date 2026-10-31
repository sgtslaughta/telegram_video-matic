import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import { AlertCircle, Clock, FolderSync, HardDriveDownload, RefreshCw, Wand2 } from 'lucide-react';
import { RugbyJobDialog } from '@/components/RugbyJobDialog';
import { RugbyMatchReview } from '@/components/RugbyMatchReview';
import { ProgressBar } from '@/components/shared/ProgressBar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { usePlugins, useUpdatePlugin } from '@/hooks/usePlugins';
import { useRugbyRescan, useRugbyStatus } from '@/hooks/useRugby';
import { withToast } from '@/lib/toast';
import { SettingsSection } from './SettingsSection';
function RugbyTools({ enabled, rateLimited }) {
    const rescan = useRugbyRescan();
    const [job, setJob] = useState(null);
    const status = useRugbyStatus();
    const sync = (status.data?.status ?? {});
    const done = Number(sync.sync_done ?? 0);
    const total = Number(sync.sync_total ?? 0);
    const current = sync.sync_current ?? null;
    if (!enabled)
        return null;
    const btn = 'h-8 text-[13px]';
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "flex flex-wrap items-center gap-2", children: [_jsxs(Button, { size: "sm", variant: "outline", className: btn, disabled: rescan.isPending, onClick: () => withToast(() => rescan.mutateAsync(), { success: 'Scan started, fetching fixtures in the background', error: 'Scan failed' }), children: [_jsx(RefreshCw, { className: `mr-1.5 h-3.5 w-3.5 ${rescan.isPending ? 'animate-spin' : ''}` }), rescan.isPending ? 'Scanning…' : 'Scan now'] }), _jsxs(Button, { size: "sm", variant: "outline", className: btn, onClick: () => setJob('rematch'), title: "Preview re-matching unmatched and auto-matched games, then apply", children: [_jsx(Wand2, { className: "mr-1.5 h-3.5 w-3.5" }), "Re-match"] }), _jsxs(Button, { size: "sm", variant: "outline", className: btn, onClick: () => setJob('reconcile'), title: "Preview moving every rugby video into league/Season folders, then apply", children: [_jsx(FolderSync, { className: "mr-1.5 h-3.5 w-3.5" }), "Reorganize library"] }), _jsxs(Button, { size: "sm", variant: "outline", className: btn, onClick: () => setJob('import'), title: "Preview adopting video files already on disk, then import", children: [_jsx(HardDriveDownload, { className: "mr-1.5 h-3.5 w-3.5" }), "Import files"] }), rateLimited && (_jsxs("span", { className: "inline-flex items-center gap-1 text-[12px] text-warn", children: [_jsx(Clock, { className: "h-3.5 w-3.5" }), "Rate limited, coverage may be incomplete"] }))] }), Boolean(sync.syncing) && (_jsxs("div", { className: "space-y-1", children: [_jsxs("div", { className: "flex justify-between text-[12px] text-muted-foreground", children: [_jsxs("span", { children: ["Syncing metadata", current ? `: ${current}` : '', "\u2026"] }), _jsxs("span", { className: "tabular-nums", children: [done, "/", total || '—'] })] }), _jsx(ProgressBar, { progress: total ? (done / total) * 100 : 5, animated: true })] })), _jsx(RugbyMatchReview, {}), job && _jsx(RugbyJobDialog, { job: job, onClose: () => setJob(null) }, job)] }));
}
export function PluginsSection() {
    const { data: plugins = [] } = usePlugins();
    const update = useUpdatePlugin();
    const server = Object.fromEntries(plugins.map((p) => [p.name, { enabled: p.enabled, config: p.config || {} }]));
    const [draft, setDraft] = useState(server);
    const patch = (name, f) => setDraft((d) => ({ ...d, [name]: f(d[name] ?? server[name]) }));
    const changed = plugins.filter((p) => JSON.stringify(draft[p.name]) !== JSON.stringify(server[p.name]));
    const save = () => withToast(() => Promise.all(changed.map((p) => update.mutateAsync({ name: p.name, config: { enabled: draft[p.name].enabled, ...draft[p.name].config } }))), { success: 'Plugin settings saved' });
    return (_jsxs(SettingsSection, { id: "plugins", title: "Plugins", description: "Extra sources and matchers. Plugins run as application code, so only install ones you trust.", dirty: changed.length > 0, saving: update.isPending, onSave: save, children: [plugins.length === 0 && _jsx("p", { className: "text-[13px] text-muted-foreground", children: "No plugins installed." }), _jsx("div", { className: "divide-y divide-border", children: plugins.map((p) => {
                    const st = draft[p.name] ?? server[p.name];
                    const rateLimited = Boolean(p.status?.rate_limited);
                    return (_jsxs("div", { className: "space-y-4 py-4 first:pt-0 last:pb-0", children: [p.last_error && (_jsxs("div", { className: "flex gap-2 rounded-md bg-err/10 p-3 text-[13px]", children: [_jsx(AlertCircle, { className: "mt-0.5 h-4 w-4 shrink-0 text-err" }), _jsx("p", { children: p.last_error })] })), _jsxs("div", { className: "flex items-center justify-between gap-3", children: [_jsxs("div", { children: [_jsx("p", { className: "text-[13px] font-medium capitalize", children: p.name }), _jsxs("p", { className: "text-[12px] text-muted-foreground", children: ["v", p.version] })] }), _jsx(Switch, { "aria-label": p.name, checked: st.enabled, onCheckedChange: (enabled) => patch(p.name, (s) => ({ ...s, enabled })) })] }), p.config_schema?.fields?.map((f) => (_jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: `${p.name}-${f.key}`, className: "text-[13px] font-medium", children: f.label }), f.type === 'boolean' ? (_jsx("div", { children: _jsx(Switch, { id: `${p.name}-${f.key}`, checked: st.config[f.key] ?? false, onCheckedChange: (v) => patch(p.name, (s) => ({ ...s, config: { ...s.config, [f.key]: v } })) }) })) : (_jsx(Input, { id: `${p.name}-${f.key}`, className: "h-9 max-w-xs text-[13px]", type: f.type === 'number' ? 'number' : 'text', value: st.config[f.key] ?? '', onChange: (e) => patch(p.name, (s) => ({ ...s, config: { ...s.config, [f.key]: f.type === 'number' ? (e.target.value ? Number(e.target.value) : null) : e.target.value } })) })), f.help && _jsx("p", { className: "text-[12px] text-muted-foreground", children: f.help })] }, f.key))), p.name === 'rugby' && _jsx(RugbyTools, { enabled: st.enabled, rateLimited: rateLimited })] }, p.id));
                }) }), _jsxs("p", { className: "border-t border-border pt-4 text-[12px] text-muted-foreground", children: ["To install one, drop a ", _jsx("code", { className: "rounded bg-muted px-1 font-mono", children: "*_plugin.py" }), " file into the", ' ', _jsx("code", { className: "rounded bg-muted px-1 font-mono", children: "plugins/" }), " directory and restart the container."] })] }));
}
