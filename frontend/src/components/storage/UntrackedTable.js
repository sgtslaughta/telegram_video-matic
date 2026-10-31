import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useDeleteUntracked } from '@/hooks/useStorage';
import { absTime, formatBytes, relTime } from '@/lib/format';
import { withToast } from '@/lib/toast';
import { DestructiveConfirm } from './DestructiveConfirm';
import { Panel, TD, TH } from './Panel';
export function UntrackedTable({ untracked }) {
    const [target, setTarget] = useState(null);
    const del = useDeleteUntracked();
    const run = async () => {
        const f = target;
        setTarget(null);
        if (f)
            await withToast(() => del.mutateAsync(f.path), { success: 'Deleted file' });
    };
    return (_jsxs(Panel, { title: "Files the app doesn\u2019t track", aside: untracked.count ? `${untracked.count} file${untracked.count === 1 ? '' : 's'}, ${formatBytes(untracked.bytes)}` : undefined, children: [_jsx("p", { className: "border-b border-border px-4 py-2.5 text-[12px] text-muted-foreground", children: "These files aren\u2019t in the library, so cleanup never touches them." }), untracked.items.length ? (_jsx("div", { className: "overflow-x-auto", children: _jsxs("table", { className: "w-full text-[13px]", children: [_jsx("thead", { children: _jsxs("tr", { className: "border-b border-border", children: [_jsx("th", { className: TH, children: "Path" }), _jsx("th", { className: `${TH} text-right`, children: "Size" }), _jsx("th", { className: TH, children: "Modified" }), _jsx("th", { className: `${TH} w-12`, children: _jsx("span", { className: "sr-only", children: "Actions" }) })] }) }), _jsx("tbody", { className: "divide-y divide-border", children: untracked.items.map((f) => (_jsxs("tr", { className: "transition-colors hover:bg-accent/60", children: [_jsx("td", { className: `${TD} max-w-[360px]`, children: _jsx("span", { className: "block truncate font-mono text-[12px]", title: f.path, children: f.path }) }), _jsx("td", { className: `${TD} text-right tabular-nums`, children: formatBytes(f.size_bytes) }), _jsx("td", { className: `${TD} whitespace-nowrap text-muted-foreground`, title: absTime(f.modified), children: relTime(f.modified) }), _jsx("td", { className: `${TD} text-right`, children: _jsx(Button, { variant: "ghost", size: "icon", className: "h-8 w-8 text-muted-foreground hover:text-err", "aria-label": `Delete ${f.path}`, onClick: () => setTarget(f), children: _jsx(Trash2, { className: "h-4 w-4" }) }) })] }, f.path))) })] }) })) : (_jsx("p", { className: "px-4 py-6 text-[13px] text-muted-foreground", children: "Every file in the media folder is in the library." })), _jsx(DestructiveConfirm, { open: !!target, title: "Delete this file?", description: `${target?.path ?? ''} will be permanently deleted from disk. It can’t be undone.`, confirmText: "Delete file", onConfirm: run, onCancel: () => setTarget(null) })] }));
}
