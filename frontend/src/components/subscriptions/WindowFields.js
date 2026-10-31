import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Checkbox } from '@/components/ui/checkbox';
import { Combobox } from '@/components/ui/combobox';
import { Input } from '@/components/ui/input';
import { Field } from './Section';
const DAYS = [['mon', 'Mon'], ['tue', 'Tue'], ['wed', 'Wed'], ['thu', 'Thu'], ['fri', 'Fri'], ['sat', 'Sat'], ['sun', 'Sun']];
const FREQUENCIES = [
    { value: 'realtime', label: 'Real-time (instant)' },
    { value: '1m', label: 'Every minute' },
    { value: '5m', label: 'Every 5 minutes' },
    { value: '15m', label: 'Every 15 minutes' },
    { value: '30m', label: 'Every 30 minutes' },
    { value: 'hourly', label: 'Hourly' },
    { value: 'daily', label: 'Daily' },
    { value: 'scheduled', label: 'Specific weekdays' },
];
function windowSummary(s) {
    if (!s.dateFrom && s.ongoing)
        return 'Capturing all history and everything new.';
    if (s.dateFrom && s.ongoing)
        return `From ${s.dateFrom} onward, catching up on missed posts and continuing.`;
    if (s.dateFrom && s.dateTo)
        return `Window ${s.dateFrom} to ${s.dateTo}, then stops.`;
    if (s.dateFrom)
        return `From ${s.dateFrom}. Set an end date or turn on Ongoing.`;
    return s.dateTo ? `Up to ${s.dateTo}.` : '';
}
export function WindowFields({ s, update, toggleDay }) {
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "grid gap-4 sm:grid-cols-2", children: [_jsx(Field, { label: "From", htmlFor: "dateFrom", hint: "Empty means from the very beginning.", children: _jsx(Input, { id: "dateFrom", type: "date", value: s.dateFrom, onChange: (e) => update('dateFrom', e.target.value) }) }), _jsx(Field, { label: "To", htmlFor: "dateTo", hint: "Only used when Ongoing is off.", children: _jsx(Input, { id: "dateTo", type: "date", value: s.dateTo, disabled: s.ongoing, onChange: (e) => update('dateTo', e.target.value) }) })] }), _jsxs("label", { className: "flex cursor-pointer items-center gap-2 text-[13px]", children: [_jsx(Checkbox, { checked: s.ongoing, onCheckedChange: (c) => update('ongoing', c === true) }), "Ongoing: keep capturing new posts"] }), _jsx("p", { className: "text-[12px] text-muted-foreground", children: windowSummary(s) }), _jsx(Field, { label: "Check frequency", hint: s.checkFrequency === 'realtime' ? 'Queued the moment it is posted, via live Telegram events.' : undefined, children: _jsx(Combobox, { value: s.checkFrequency, onChange: (v) => update('checkFrequency', v), options: FREQUENCIES }) }), s.checkFrequency === 'scheduled' && (_jsx(Field, { label: "Weekdays", hint: "Only these days are scanned. Pick at least one.", children: _jsx("div", { className: "flex flex-wrap gap-x-4 gap-y-2", children: DAYS.map(([v, l]) => (_jsxs("label", { className: "flex cursor-pointer items-center gap-2 text-[13px]", children: [_jsx(Checkbox, { checked: s.scheduleDays.includes(v), onCheckedChange: () => toggleDay(v) }), l] }, v))) }) }))] }));
}
