import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import { X } from 'lucide-react';
import { Combobox } from '@/components/ui/combobox';
import { Input } from '@/components/ui/input';
import { MediaThumb } from '@/components/shared/MediaThumb';
import { useRugbyPreview } from '@/hooks/useRugby';
import { Field, Section, ToggleRow } from './Section';
import { DEFAULT_TEMPLATE, renderTemplate } from './template';
export function RugbySection({ allLeagues, on, setOn, leagues, setLeagues, template }) {
    const league = leagues[0] ?? null; // preview tests against the first league
    const name = (id) => allLeagues.find((l) => l.id === id)?.name ?? `League ${id}`;
    const [filename, setFilename] = useState('Sale Sharks v Gloucester.mp4');
    const preview = useRugbyPreview();
    const r = preview.data;
    return (_jsxs(Section, { title: "Rugby league", description: "Match detection and file name enrichment.", children: [_jsx(ToggleRow, { id: "rugbyToggle", label: "Rugby enrichment", hint: "Detect matches and add teams to file names.", checked: on, onChange: setOn }), on && (_jsxs(_Fragment, { children: [_jsxs(Field, { label: "Leagues", hint: "Add every competition this topic posts, e.g. Champions Cup and Challenge Cup.", children: [leagues.length > 0 && (_jsx("ul", { className: "mb-2 flex flex-wrap gap-1.5", children: leagues.map((id) => (_jsxs("li", { className: "flex items-center gap-1 rounded-full bg-brand/10 py-0.5 pl-2.5 pr-1 text-[12px] font-medium text-brand", children: [name(id), _jsx("button", { type: "button", "aria-label": `Remove ${name(id)}`, onClick: () => setLeagues(leagues.filter((x) => x !== id)), className: "rounded-full p-0.5 hover:bg-brand/20", children: _jsx(X, { className: "h-3 w-3" }) })] }, id))) })), _jsx(Combobox, { value: "", onChange: (v) => { if (v)
                                    setLeagues([...leagues, parseInt(v)]); }, placeholder: leagues.length ? 'Add another league' : 'Add a league', options: allLeagues.filter((l) => !leagues.includes(l.id)).map((l) => ({ value: l.id.toString(), label: l.name })) })] }), league && (_jsxs("div", { className: "space-y-3 rounded-md border border-border bg-muted/40 p-3", children: [_jsx(Field, { label: "Test file name", htmlFor: "testFilename", children: _jsx(Input, { id: "testFilename", value: filename, placeholder: "e.g. Sale Sharks v Gloucester.mp4", onChange: (e) => { setFilename(e.target.value); preview.mutate({ leagueId: league, text: e.target.value }); } }) }), r && (_jsxs("div", { className: "space-y-2 text-[12px]", children: [r.matched ? (_jsxs(_Fragment, { children: [_jsxs("p", { className: "font-medium text-ok", children: ["Confident match (", Math.round(r.confidence * 100), "%)"] }), _jsxs("div", { className: "flex items-center gap-2", children: [r.home_badge && _jsx(MediaThumb, { src: r.home_badge, alt: r.home || '', size: "sm" }), r.away_badge && _jsx(MediaThumb, { src: r.away_badge, alt: r.away || '', size: "sm" }), _jsxs("span", { children: [r.home, " vs ", r.away] })] }), r.tokens && _jsx("p", { className: "font-mono", children: renderTemplate(template || DEFAULT_TEMPLATE, r.tokens) })] })) : _jsx("p", { className: "text-warn", children: "No confident match, so the original file name is kept." }), _jsxs("p", { className: "text-muted-foreground", children: [r.fixtures_count, " fixtures, ", r.teams_count, " teams loaded"] })] }))] }))] }))] }));
}
