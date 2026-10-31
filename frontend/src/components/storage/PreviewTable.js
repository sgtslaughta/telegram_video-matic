import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { formatBytes } from '@/lib/format';
import { Panel, TD, TH } from './Panel';
const REASON = {
    age: 'Older than the retention period',
    quota: 'Over the subscription’s limit',
    disk: 'Disk is nearly full',
};
const FIRST = 20;
export function PreviewTable({ preview }) {
    const [all, setAll] = useState(false);
    const rows = all ? preview.items : preview.items.slice(0, FIRST);
    return (_jsx(Panel, { id: "cleanup-preview", title: `Deleting in the next ${preview.days} days`, aside: preview.count ? `${preview.count} file${preview.count === 1 ? '' : 's'}, ${formatBytes(preview.bytes)}` : undefined, children: preview.items.length ? (_jsxs("div", { className: "overflow-x-auto", children: [_jsxs("table", { className: "w-full text-[13px]", children: [_jsx("thead", { children: _jsxs("tr", { className: "border-b border-border", children: [_jsx("th", { className: TH, children: "File" }), _jsx("th", { className: TH, children: "Reason" }), _jsx("th", { className: TH, children: "Match date" }), _jsx("th", { className: `${TH} text-right`, children: "Size" })] }) }), _jsx("tbody", { className: "divide-y divide-border", children: rows.map((i) => (_jsxs("tr", { className: "transition-colors hover:bg-accent/60", children: [_jsx("td", { className: `${TD} max-w-[320px]`, children: _jsx(Link, { to: `/media/${i.id}`, className: "block truncate font-medium hover:underline", title: i.file_name, children: i.file_name }) }), _jsx("td", { className: `${TD} text-muted-foreground`, children: REASON[i.reason] ?? i.reason }), _jsx("td", { className: `${TD} whitespace-nowrap text-muted-foreground`, children: i.content_date ? new Date(i.content_date).toLocaleDateString(undefined, { dateStyle: 'medium' }) : '-' }), _jsx("td", { className: `${TD} text-right tabular-nums`, children: formatBytes(i.size_bytes) })] }, i.id))) })] }), preview.items.length > FIRST && (_jsx("button", { onClick: () => setAll((v) => !v), className: "w-full border-t border-border py-2.5 text-[13px] font-medium text-brand transition-colors hover:bg-accent/60", children: all ? 'Show fewer' : `Show all ${preview.items.length} files` }))] })) : (_jsx("p", { className: "px-4 py-6 text-[13px] text-muted-foreground", children: "Nothing is due for cleanup this week." })) }));
}
