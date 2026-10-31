import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useFilterPreview } from '@/hooks/useSubscriptionTools';
import { FilterFields } from './FilterFields';
import { FilterPreview } from './FilterPreview';
import { Section } from './Section';
import { WindowFields } from './WindowFields';
import { previewParams } from './previewParams';
export function WhatToDownload({ regexValid, regexError, toggleDay, ...p }) {
    const preview = useFilterPreview(previewParams(p.s, regexValid));
    const bad = preview.error?.status === 400 ? preview.error.message : null;
    return (_jsxs(Section, { title: "What to download", description: "Filter, size limits, date window and schedule.", children: [_jsx(FilterFields, { ...p, regexValid: regexValid, regexError: regexError, serverError: bad }), _jsx(WindowFields, { ...p, toggleDay: toggleDay }), _jsx(FilterPreview, { items: preview.data, loading: preview.isFetching, idle: !p.s.channelId })] }));
}
