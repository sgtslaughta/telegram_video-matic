import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { ThemeProvider } from '@/hooks/useTheme';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Toaster } from 'sonner';
import Router from './Router';
const queryClient = new QueryClient();
describe('Router', () => {
    beforeEach(() => {
        // Mock window.matchMedia for tests
        Object.defineProperty(window, 'matchMedia', {
            writable: true,
            value: vi.fn().mockImplementation((query) => ({
                matches: false,
                media: query,
                onchange: null,
                addListener: vi.fn(),
                removeListener: vi.fn(),
                addEventListener: vi.fn(),
                removeEventListener: vi.fn(),
                dispatchEvent: vi.fn(),
            })),
        });
    });
    it('renders login route at /login', () => {
        render(_jsx(MemoryRouter, { initialEntries: ['/login'], children: _jsx(QueryClientProvider, { client: queryClient, children: _jsx(ThemeProvider, { children: _jsxs(TooltipProvider, { children: [_jsx(Router, {}), _jsx(Toaster, {})] }) }) }) }));
        // Login page should NOT have sidebar (nav should not exist)
        expect(screen.getByRole('heading', { name: 'Login' })).toBeTruthy();
        expect(screen.queryByRole('navigation')).toBeFalsy();
    });
    it('renders overview route at /', () => {
        render(_jsx(MemoryRouter, { initialEntries: ['/'], children: _jsx(QueryClientProvider, { client: queryClient, children: _jsx(ThemeProvider, { children: _jsxs(TooltipProvider, { children: [_jsx(Router, {}), _jsx(Toaster, {})] }) }) }) }));
        // Dashboard should have sidebar
        expect(screen.getAllByRole('navigation')[0]).toBeTruthy();
        // Check for main dashboard content (hero banner or stat cards)
        const mainContent = screen.getByRole('main');
        expect(mainContent.textContent).toContain('Overview');
    });
    it('navigates to /subscriptions and renders SubscriptionsList', () => {
        render(_jsx(MemoryRouter, { initialEntries: ['/subscriptions'], children: _jsx(QueryClientProvider, { client: queryClient, children: _jsx(ThemeProvider, { children: _jsxs(TooltipProvider, { children: [_jsx(Router, {}), _jsx(Toaster, {})] }) }) }) }));
        expect(screen.getAllByRole('navigation')[0]).toBeTruthy();
        expect(screen.getByRole('main')).toBeTruthy();
    });
});
