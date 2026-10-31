import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogTitle, } from '@/components/ui/alert-dialog';
/** Irreversible-action confirm; the action button uses the destructive colour. */
export function DestructiveConfirm({ open, title, description, confirmText, onConfirm, onCancel }) {
    return (_jsx(AlertDialog, { open: open, onOpenChange: (o) => !o && onCancel(), children: _jsxs(AlertDialogContent, { children: [_jsx(AlertDialogTitle, { children: title }), _jsx(AlertDialogDescription, { children: description }), _jsxs("div", { className: "flex justify-end gap-2 pt-4", children: [_jsx(AlertDialogCancel, { onClick: onCancel, children: "Cancel" }), _jsx(AlertDialogAction, { onClick: onConfirm, className: "bg-destructive text-destructive-foreground hover:bg-destructive/90", children: confirmText })] })] }) }));
}
