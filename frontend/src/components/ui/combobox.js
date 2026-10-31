import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from 'react';
import { Check, ChevronsUpDown, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
// Searchable select built on Popover (no cmdk dependency). The filter input is
// hidden for short lists where searching adds nothing.
// ponytail: mouse + type-to-filter only; no arrow-key nav (add cmdk if needed).
export function Combobox({ value, onChange, options, placeholder = 'Select…', searchPlaceholder = 'Search…', emptyText = 'No results', disabled, className, }) {
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState('');
    const selected = options.find((o) => o.value === value);
    const showSearch = options.length >= 8;
    const filtered = useMemo(() => {
        const q = query.toLowerCase();
        return q ? options.filter((o) => o.label.toLowerCase().includes(q)) : options;
    }, [options, query]);
    return (_jsxs(Popover, { open: open, onOpenChange: (o) => { setOpen(o); if (!o)
            setQuery(''); }, children: [_jsx(PopoverTrigger, { asChild: true, children: _jsxs(Button, { variant: "outline", role: "combobox", "aria-expanded": open, disabled: disabled, className: cn('w-full justify-between font-normal', !selected && 'text-muted-foreground', className), children: [_jsx("span", { className: "truncate", children: selected ? selected.label : placeholder }), _jsx(ChevronsUpDown, { className: "ml-2 h-4 w-4 shrink-0 opacity-50" })] }) }), _jsxs(PopoverContent, { className: "w-[--radix-popover-trigger-width] p-0", align: "start", children: [showSearch && (_jsxs("div", { className: "relative border-b", children: [_jsx(Search, { className: "absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" }), _jsx(Input, { autoFocus: true, value: query, onChange: (e) => setQuery(e.target.value), placeholder: searchPlaceholder, className: "border-0 pl-8 focus-visible:ring-0" })] })), _jsx("div", { className: "max-h-64 overflow-y-auto p-1", children: filtered.length === 0 ? (_jsx("p", { className: "py-6 text-center text-sm text-muted-foreground", children: emptyText })) : (filtered.map((o) => (_jsxs("button", { type: "button", onClick: () => { onChange(o.value); setOpen(false); setQuery(''); }, className: cn('flex w-full items-center rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent hover:text-accent-foreground', o.value === value && 'bg-accent/50'), children: [_jsx(Check, { className: cn('mr-2 h-4 w-4 shrink-0', o.value === value ? 'opacity-100' : 'opacity-0') }), _jsx("span", { className: "truncate", children: o.label })] }, o.value)))) })] })] }));
}
