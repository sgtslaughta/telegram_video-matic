import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { motion } from 'framer-motion';
import { clsx } from 'clsx';
export function ProgressBar({ progress, className, showLabel = false, animated = true, }) {
    const clampedProgress = Math.min(Math.max(progress, 0), 100);
    return (_jsxs("div", { className: clsx('w-full', className), children: [_jsx("div", { className: "h-2 w-full overflow-hidden rounded-full bg-muted", children: _jsx(motion.div, { className: "h-full bg-primary", initial: animated ? { width: 0 } : { width: `${clampedProgress}%` }, animate: { width: `${clampedProgress}%` }, transition: { duration: animated ? 0.5 : 0, ease: 'easeOut' } }) }), showLabel && (_jsxs("p", { className: "mt-1 text-right text-xs text-muted-foreground", children: [Math.round(clampedProgress), "%"] }))] }));
}
