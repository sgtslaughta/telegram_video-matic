import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { useSettings, useUpdateSettings } from '@/hooks/useSettings';
import { withToast } from '@/lib/toast';
import { Field, SettingsSection, inputCls } from './SettingsSection';
/** Draft of a group of numeric settings; dirty when it differs from the server. */
function useGroup(keys, saved) {
    const { data } = useSettings();
    const update = useUpdateSettings();
    const base = Object.fromEntries(keys.map((k) => [k, data?.find((s) => s.key === k)?.value ?? '']));
    const [draft, setDraft] = useState(base);
    const dirty = keys.some((k) => draft[k] !== base[k]);
    const save = async () => {
        const patch = {};
        // Only send what changed; an untouched empty field must not overwrite the server value.
        keys.filter((k) => draft[k] !== base[k] && draft[k] !== '').forEach((k) => { patch[k] = Number(draft[k]); });
        await withToast(() => update.mutateAsync(patch), { success: saved });
    };
    return { draft, set: (k, v) => setDraft((d) => ({ ...d, [k]: v })), dirty, save, saving: update.isPending };
}
export function GeneralSection() {
    const g = useGroup(['poll_interval_sec', 'max_concurrent_downloads', 'download_connections'], 'General settings saved');
    return (_jsxs(SettingsSection, { id: "general", title: "General", description: "How often the app checks for new videos and how many it downloads at once.", dirty: g.dirty, saving: g.saving, onSave: g.save, children: [_jsx(Field, { id: "poll", label: "Poll interval (seconds)", help: "How often subscriptions are scanned for new videos.", children: _jsx(Input, { id: "poll", type: "number", min: 1, className: inputCls, value: g.draft.poll_interval_sec, onChange: (e) => g.set('poll_interval_sec', e.target.value) }) }), _jsx(Field, { id: "max-dl", label: "Concurrent downloads", help: "How many videos download at the same time (1\u201310). Takes effect on the next download.", children: _jsx(Input, { id: "max-dl", type: "number", min: 1, max: 10, className: inputCls, value: g.draft.max_concurrent_downloads, onChange: (e) => g.set('max_concurrent_downloads', e.target.value) }) }), _jsx(Field, { id: "dl-conns", label: "Connections per download", help: "Parallel Telegram connections used for each video (1\u201332, default 20). More can be faster; too many can trigger Telegram rate limits.", children: _jsx(Input, { id: "dl-conns", type: "number", min: 1, max: 32, placeholder: "20", className: inputCls, value: g.draft.download_connections, onChange: (e) => g.set('download_connections', e.target.value) }) })] }));
}
export function CleanupSection() {
    const g = useGroup(['retention_days', 'retention_disk_pct'], 'Cleanup settings saved');
    return (_jsxs(SettingsSection, { id: "cleanup", title: "Cleanup", description: "Automatic deletion keeps the disk from filling up.", dirty: g.dirty, saving: g.saving, onSave: g.save, children: [_jsx(Field, { id: "retention", label: "Retention (days)", help: "Videos are deleted this many days after the match date. Pinned videos and subscriptions are kept.", children: _jsx(Input, { id: "retention", type: "number", min: 0, className: inputCls, value: g.draft.retention_days, onChange: (e) => g.set('retention_days', e.target.value) }) }), _jsx(Field, { id: "retention-pct", label: "Disk usage limit (%)", help: "When the disk is this full, the oldest videos are deleted until it is back under.", children: _jsx(Input, { id: "retention-pct", type: "number", min: 1, max: 100, className: inputCls, value: g.draft.retention_disk_pct, onChange: (e) => g.set('retention_disk_pct', e.target.value) }) })] }));
}
