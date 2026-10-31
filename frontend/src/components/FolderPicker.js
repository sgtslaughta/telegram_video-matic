import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Folder, FolderOpen, CornerLeftUp, Check } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import * as api from '@/lib/api';
// Storage-path input with a browse popover that lists server subfolders
// (sandboxed to MEDIA_ROOT). Click a folder to descend, breadcrumb up, then
// "Use this folder" to write the current path back into the field.
// ponytail: one dir level per fetch; typing the path by hand still works.
export default function FolderPicker({ id, value, onChange, placeholder, }) {
    const [open, setOpen] = useState(false);
    const [view, setView] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const browse = async (path) => {
        setLoading(true);
        setError(null);
        try {
            setView(await api.fs.listDirs(path));
        }
        catch (e) {
            setError(e instanceof Error ? e.message : 'Could not read folder');
        }
        finally {
            setLoading(false);
        }
    };
    const onOpenChange = (next) => {
        setOpen(next);
        // Start at the typed path if there is one, else the media root.
        if (next)
            browse(value || undefined);
    };
    return (_jsxs("div", { className: "flex gap-2", children: [_jsx(Input, { id: id, value: value, onChange: (e) => onChange(e.target.value), placeholder: placeholder }), _jsxs(Popover, { open: open, onOpenChange: onOpenChange, children: [_jsx(PopoverTrigger, { asChild: true, children: _jsx(Button, { type: "button", variant: "outline", size: "icon", "aria-label": "Browse folders", children: _jsx(FolderOpen, { className: "h-4 w-4" }) }) }), _jsxs(PopoverContent, { className: "w-80 p-2", align: "end", children: [_jsxs("div", { className: "mb-2 flex items-center gap-2 text-xs text-muted-foreground", children: [_jsxs("button", { type: "button", className: "inline-flex items-center gap-1 hover:text-foreground disabled:opacity-40", disabled: !view?.parent || loading, onClick: () => view?.parent && browse(view.parent), children: [_jsx(CornerLeftUp, { className: "h-3.5 w-3.5" }), " Up"] }), _jsx("span", { className: "truncate font-mono", title: view?.path, children: view?.path ?? '…' })] }), _jsx(ScrollArea, { className: "h-56 rounded border border-border", children: error ? (_jsx("p", { className: "p-3 text-sm text-destructive", children: error })) : loading ? (_jsx("p", { className: "p-3 text-sm text-muted-foreground", children: "Loading\u2026" })) : view && view.dirs.length === 0 ? (_jsx("p", { className: "p-3 text-sm text-muted-foreground", children: "No subfolders" })) : (view?.dirs.map((name) => (_jsxs("button", { type: "button", className: "flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm hover:bg-accent hover:text-accent-foreground", onClick: () => browse(`${view.path}/${name}`), children: [_jsx(Folder, { className: "h-4 w-4 shrink-0 text-muted-foreground" }), _jsx("span", { className: "truncate", children: name })] }, name)))) }), _jsxs(Button, { type: "button", size: "sm", className: "mt-2 w-full gap-2", disabled: !view, onClick: () => {
                                    if (view)
                                        onChange(view.path);
                                    setOpen(false);
                                }, children: [_jsx(Check, { className: "h-4 w-4" }), " Use this folder"] })] })] })] }));
}
