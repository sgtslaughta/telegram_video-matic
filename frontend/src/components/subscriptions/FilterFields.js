import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import { Field } from './Section';
function numOrNull(v) {
    return v === '' ? null : Math.max(0, Number(v));
}
function RegexTester({ s, valid }) {
    const [str, setStr] = useState('');
    let m = null;
    if (s.filterRegex && valid && str) {
        try {
            m = str.match(new RegExp(s.filterRegex, 'i'));
        }
        catch {
            m = null;
        }
    }
    const exclude = s.filterMode === 'exclude';
    return (_jsxs(Field, { label: "Test a string", htmlFor: "regexTest", hint: !s.filterRegex && str ? 'Enter a pattern above to test it.' : undefined, children: [_jsx(Input, { id: "regexTest", value: str, onChange: (e) => setStr(e.target.value), placeholder: "Paste a filename or caption", className: "font-mono text-[12px]" }), str && valid && s.filterRegex && (_jsx("p", { className: cn('text-[12px]', m ? 'text-ok' : 'text-warn'), children: m
                    ? `Matches "${m[0]}" at position ${m.index}, ${exclude ? 'so it would be skipped' : 'so it would download'}.`
                    : `No match, so it would ${exclude ? 'download' : 'be skipped'}.` }))] }));
}
export function FilterFields({ s, update, regexValid, regexError, serverError }) {
    const err = regexError || serverError;
    return (_jsxs(_Fragment, { children: [_jsx("div", { role: "radiogroup", "aria-label": "Filter mode", className: "flex w-fit rounded-md border border-border p-0.5 text-[12px]", children: ['include', 'exclude'].map((mode) => (_jsx("button", { type: "button", role: "radio", "aria-checked": s.filterMode === mode, onClick: () => update('filterMode', mode), className: cn('rounded px-3 py-1 transition-colors', s.filterMode === mode ? 'bg-brand/10 font-medium text-brand' : 'text-muted-foreground hover:text-foreground'), children: mode === 'include' ? 'Only matching' : 'All except matching' }, mode))) }), _jsxs(Field, { label: "Filter regex", htmlFor: "regex", hint: "Case-insensitive pattern matched against file name and caption. Leave empty to match everything.", children: [_jsx(Textarea, { id: "regex", value: s.filterRegex, onChange: (e) => update('filterRegex', e.target.value), placeholder: 'e.g. \\.mkv$  or  (final|semi)', className: cn('font-mono text-[12px]', err && 'border-err'), rows: 2 }), s.filterRegex && (err
                        ? _jsxs("p", { role: "alert", className: "text-[12px] text-err", children: ["\u2717 ", err] })
                        : regexValid && _jsx("p", { className: "text-[12px] text-ok", children: "\u2713 Valid pattern" }))] }), _jsx(RegexTester, { s: s, valid: regexValid }), _jsxs("div", { className: "grid gap-4 sm:grid-cols-2", children: [_jsx(Field, { label: "Minimum size (MB)", htmlFor: "minSize", children: _jsx(Input, { id: "minSize", type: "number", min: 0, value: s.minSizeMb ?? '', placeholder: "No minimum", onChange: (e) => update('minSizeMb', numOrNull(e.target.value)) }) }), _jsx(Field, { label: "Maximum size (MB)", htmlFor: "maxSize", children: _jsx(Input, { id: "maxSize", type: "number", min: 0, value: s.maxSizeMb ?? '', placeholder: "No maximum", onChange: (e) => update('maxSizeMb', numOrNull(e.target.value)) }) })] })] }));
}
