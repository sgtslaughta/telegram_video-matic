import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { BrowserRouter } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { ThemeProvider } from '@/hooks/useTheme';
import { AccentProvider } from '@/hooks/useAccent';
import { TooltipProvider } from '@/components/ui/tooltip';
import Router from '@/Router';
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 min
            gcTime: 1000 * 60 * 10,
        },
    },
});
export default function App() {
    return (_jsx(QueryClientProvider, { client: queryClient, children: _jsx(ThemeProvider, { children: _jsx(AccentProvider, { children: _jsx(TooltipProvider, { children: _jsxs(BrowserRouter, { children: [_jsx(Router, {}), _jsx(Toaster, { position: "bottom-right" })] }) }) }) }) }));
}
