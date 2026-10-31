import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { notifications } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
const TRIGGER_LABELS = {
    download_complete: 'Download finished',
    download_failed: 'Download failed',
    telegram: 'Telegram connection lost / restored',
    unmatched: 'Video needs review',
    disk_low: 'Disk space low',
};
const toInput = (t) => ({
    id: t.id,
    name: t.name,
    triggers: t.triggers,
});
function TriggerBoxes({ idPrefix, all, value, onChange }) {
    return (_jsx("div", { className: "flex flex-wrap gap-x-4 gap-y-2", children: all.map((t) => (_jsxs("div", { className: "flex items-center gap-2", children: [_jsx(Checkbox, { id: `${idPrefix}-${t}`, checked: value.includes(t), onCheckedChange: (c) => onChange(c === true ? [...value, t] : value.filter((x) => x !== t)) }), _jsx(Label, { htmlFor: `${idPrefix}-${t}`, className: "text-[13px] font-normal", children: TRIGGER_LABELS[t] ?? t })] }, t))) }));
}
export function NotificationTargets({ triggers, targets }) {
    const qc = useQueryClient();
    const [name, setName] = useState('');
    const [url, setUrl] = useState('');
    const [newTriggers, setNewTriggers] = useState(triggers);
    const [replace, setReplace] = useState({});
    const onError = (e) => toast.error(e.message);
    const save = useMutation({
        mutationFn: (list) => notifications.saveTargets(list),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['notifications'] });
            toast.success('Target saved');
        },
        onError,
    });
    const test = useMutation({
        mutationFn: (body) => notifications.test(body),
        onSuccess: () => toast.success('Test sent'),
        onError,
    });
    const existing = targets.map(toInput);
    const update = (id, patch) => save.mutate(existing.map((t) => (t.id === id ? { ...t, ...patch } : t)));
    const add = () => {
        save.mutate([...existing, { name, url, triggers: newTriggers }], {
            onSuccess: () => {
                setName('');
                setUrl('');
                setNewTriggers(triggers);
            },
        });
    };
    return (_jsxs("div", { className: "space-y-4", children: [_jsx("h3", { className: "text-[13px] font-semibold", children: "Targets" }), targets.length === 0 && (_jsx("p", { className: "text-[13px] text-muted-foreground", children: "No targets yet. Add one below to get alerts." })), targets.map((t) => (_jsxs("div", { className: "space-y-3 rounded-lg border border-border p-3", children: [_jsxs("div", { className: "flex flex-wrap items-center justify-between gap-2", children: [_jsxs("div", { children: [_jsx("p", { className: "text-[13px] font-medium", children: t.name }), _jsx("p", { className: "font-mono text-[12px] text-muted-foreground", children: t.url_masked })] }), _jsxs("div", { className: "flex gap-2", children: [_jsx(Button, { size: "sm", variant: "outline", onClick: () => test.mutate({ id: t.id }), children: "Send test" }), _jsx(Button, { size: "sm", variant: "outline", onClick: () => save.mutate(existing.filter((x) => x.id !== t.id)), children: "Remove" })] })] }), _jsx(TriggerBoxes, { idPrefix: `t-${t.id}`, all: triggers, value: t.triggers, onChange: (v) => update(t.id, { triggers: v }) }), _jsxs("div", { className: "flex items-end gap-2", children: [_jsxs("div", { className: "flex-1 space-y-1", children: [_jsx(Label, { htmlFor: `replace-${t.id}`, children: "Replace URL" }), _jsx(Input, { className: "h-9 text-[13px]", id: `replace-${t.id}`, value: replace[t.id] ?? '', placeholder: "Optional new Apprise URL", onChange: (e) => setReplace({ ...replace, [t.id]: e.target.value }) })] }), _jsx(Button, { size: "sm", disabled: !replace[t.id], onClick: () => {
                                    update(t.id, { url: replace[t.id] });
                                    setReplace({ ...replace, [t.id]: '' });
                                }, children: "Save URL" })] })] }, t.id))), _jsxs("div", { className: "space-y-3 rounded-lg border border-dashed border-border p-3", children: [_jsx("h4", { className: "text-[13px] font-medium", children: "Add target" }), _jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: "new-target-name", children: "Name" }), _jsx(Input, { id: "new-target-name", className: "h-9 max-w-md text-[13px]", value: name, onChange: (e) => setName(e.target.value) })] }), _jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: "new-target-url", children: "Apprise URL" }), _jsx(Input, { className: "h-9 max-w-md text-[13px]", id: "new-target-url", value: url, placeholder: "discord://webhook_id/webhook_token", onChange: (e) => setUrl(e.target.value) }), _jsx("a", { href: "https://github.com/caronc/apprise/wiki", target: "_blank", rel: "noreferrer", className: "text-[12px] font-medium text-brand hover:underline", children: "Apprise URL formats" })] }), _jsx(TriggerBoxes, { idPrefix: "new", all: triggers, value: newTriggers, onChange: setNewTriggers }), _jsxs("div", { className: "flex gap-2", children: [_jsx(Button, { size: "sm", variant: "outline", disabled: !url, onClick: () => test.mutate({ url }), children: "Send test" }), _jsx(Button, { size: "sm", disabled: !name || !url || save.isPending, onClick: add, children: "Add target" })] })] })] }));
}
