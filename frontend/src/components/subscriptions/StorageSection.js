import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import FolderPicker from '@/components/FolderPicker';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Field, Section, ToggleRow } from './Section';
import { DEFAULT_TEMPLATE, sampleName } from './template';
export function StorageSection({ s, update }) {
    return (_jsxs(Section, { title: "Storage and naming", description: "Where files go and what they are called.", children: [_jsx(Field, { label: "Storage path", htmlFor: "path", hint: "Base folder on the server. Must be writable.", children: _jsx(FolderPicker, { id: "path", value: s.storagePath, onChange: (p) => update('storagePath', p), placeholder: "/media/downloads" }) }), _jsxs(Field, { label: "Naming template", htmlFor: "template", hint: "Tokens: {channel} {topic} {title} {season} {episode} {date} {original} {ext}. Slashes create folders.", children: [_jsx(Input, { id: "template", value: s.renameTemplate, onChange: (e) => update('renameTemplate', e.target.value), placeholder: DEFAULT_TEMPLATE }), _jsxs("div", { className: "text-[12px] text-muted-foreground", children: ["Preview ", _jsx(Badge, { variant: "outline", className: "ml-1 font-mono", children: sampleName(s.renameTemplate) })] })] }), _jsx(ToggleRow, { id: "seasonDet", label: "Season detection", hint: "Detect SxxExx in file names to fill {season} and {episode}.", checked: s.seasonDetection, onChange: (c) => update('seasonDetection', c) }), _jsx(ToggleRow, { id: "jellyfin", label: "Jellyfin metadata", hint: "Write .nfo sidecars, plus season folders when episodes are detected.", checked: s.jellyfinMetadata, onChange: (c) => update('jellyfinMetadata', c) })] }));
}
