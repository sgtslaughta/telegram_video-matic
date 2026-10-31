import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { clsx } from 'clsx';
const SIZE_CLASSES = {
    sm: 'w-12 h-12',
    md: 'w-24 h-24',
    lg: 'w-48 h-48',
};
function Skeleton({ size }) {
    return (_jsx("div", { className: clsx(SIZE_CLASSES[size], 'animate-pulse rounded-md bg-muted') }));
}
export function MediaThumb({ src, alt, size = 'md', className, }) {
    const [isLoading, setIsLoading] = useState(!src);
    const [hasError, setHasError] = useState(false);
    if (!src || hasError) {
        return (_jsx("div", { className: clsx(SIZE_CLASSES[size], 'flex items-center justify-center rounded-md bg-muted', className), children: _jsx("svg", { className: "h-6 w-6 text-muted-foreground", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "m4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" }) }) }));
    }
    return (_jsxs("div", { className: clsx('relative overflow-hidden rounded-md', SIZE_CLASSES[size], className), children: [isLoading && _jsx(Skeleton, { size: size }), _jsx("img", { src: src, alt: alt, onLoad: () => setIsLoading(false), onError: () => {
                    setIsLoading(false);
                    setHasError(true);
                }, className: clsx('h-full w-full object-cover', isLoading && 'hidden') })] }));
}
