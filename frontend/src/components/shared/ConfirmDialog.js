import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogTitle, } from '@/components/ui/alert-dialog';
export function ConfirmDialog({ title, description, onConfirm, onCancel, isOpen, confirmText = 'Confirm', cancelText = 'Cancel', }) {
    return (_jsx(AlertDialog, { open: isOpen, children: _jsxs(AlertDialogContent, { children: [_jsx(AlertDialogTitle, { children: title }), _jsx(AlertDialogDescription, { children: description }), _jsxs("div", { className: "flex justify-end gap-2 pt-4", children: [_jsx(AlertDialogCancel, { onClick: onCancel, children: cancelText }), _jsx(AlertDialogAction, { onClick: onConfirm, children: confirmText })] })] }) }));
}
