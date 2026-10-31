import { jsx as _jsx } from "react/jsx-runtime";
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { TooltipProvider } from '@/components/ui/tooltip';
import Settings from './Settings';
import * as settingsHooks from '@/hooks/useSettings';
import * as themeHook from '@/hooks/useTheme';
import * as pluginsHook from '@/hooks/usePlugins';
const createWrapper = () => {
    const queryClient = new QueryClient();
    return ({ children }) => (_jsx(QueryClientProvider, { client: queryClient, children: _jsx(MemoryRouter, { children: _jsx(TooltipProvider, { children: children }) }) }));
};
const mockSettings = [
    { key: 'poll_interval_sec', value: '300' },
    { key: 'max_concurrent_downloads', value: '4' },
    { key: 'retention_days', value: '90' },
    { key: 'retention_disk_pct', value: '80' },
];
const mockPlugins = [
    {
        id: 1,
        name: 'test-plugin',
        version: '1.0.0',
        enabled: true,
        config: null,
        installed_at: '2026-01-01T00:00:00Z',
    },
];
describe('Settings', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
    });
    it('renders settings form with all fields', async () => {
        vi.spyOn(settingsHooks, 'useSettings').mockReturnValue({
            data: mockSettings,
            isLoading: false,
            isError: false,
            error: null,
            status: 'success',
            refetch: vi.fn(),
            isPending: false,
        });
        vi.spyOn(themeHook, 'useTheme').mockReturnValue({
            theme: 'system',
            toggleTheme: vi.fn(),
            setTheme: vi.fn(),
            effectiveTheme: 'light',
        });
        vi.spyOn(pluginsHook, 'usePlugins').mockReturnValue({
            data: [],
            isLoading: false,
            isError: false,
            error: null,
            status: 'success',
            refetch: vi.fn(),
            isPending: false,
        });
        render(_jsx(Settings, {}), { wrapper: createWrapper() });
        expect(screen.getByDisplayValue('300')).toBeTruthy();
        expect(screen.getByDisplayValue('4')).toBeTruthy();
        expect(screen.getByDisplayValue('90')).toBeTruthy();
        expect(screen.getByDisplayValue('80')).toBeTruthy();
    });
    it('renders theme selector with radio buttons', async () => {
        vi.spyOn(settingsHooks, 'useSettings').mockReturnValue({
            data: mockSettings,
            isLoading: false,
            isError: false,
            error: null,
            status: 'success',
            refetch: vi.fn(),
            isPending: false,
        });
        vi.spyOn(themeHook, 'useTheme').mockReturnValue({
            theme: 'light',
            toggleTheme: vi.fn(),
            effectiveTheme: 'light',
        });
        vi.spyOn(pluginsHook, 'usePlugins').mockReturnValue({
            data: [],
            isLoading: false,
            isError: false,
            error: null,
            status: 'success',
            refetch: vi.fn(),
            isPending: false,
        });
        render(_jsx(Settings, {}), { wrapper: createWrapper() });
        expect(screen.getByRole('radiogroup', { name: 'Theme' })).toBeTruthy();
        expect(screen.getByRole('radiogroup', { name: 'Accent color' })).toBeTruthy();
    });
    it('renders plugins section with toggle', async () => {
        vi.spyOn(settingsHooks, 'useSettings').mockReturnValue({
            data: mockSettings,
            isLoading: false,
            isError: false,
            error: null,
            status: 'success',
            refetch: vi.fn(),
            isPending: false,
        });
        vi.spyOn(themeHook, 'useTheme').mockReturnValue({
            theme: 'system',
            toggleTheme: vi.fn(),
            setTheme: vi.fn(),
            effectiveTheme: 'light',
        });
        vi.spyOn(pluginsHook, 'usePlugins').mockReturnValue({
            data: mockPlugins,
            isLoading: false,
            isError: false,
            error: null,
            status: 'success',
            refetch: vi.fn(),
            isPending: false,
        });
        render(_jsx(Settings, {}), { wrapper: createWrapper() });
        expect(screen.getByText('test-plugin')).toBeTruthy();
    });
    it('calls updateSettings when save button is clicked', async () => {
        const updateMutate = vi.fn().mockResolvedValue([]);
        vi.spyOn(settingsHooks, 'useSettings').mockReturnValue({
            data: mockSettings,
            isLoading: false,
            isError: false,
            error: null,
            status: 'success',
            refetch: vi.fn(),
            isPending: false,
        });
        vi.spyOn(settingsHooks, 'useUpdateSettings').mockReturnValue({
            mutateAsync: updateMutate,
            isPending: false,
            isError: false,
            error: null,
            status: 'idle',
        });
        vi.spyOn(themeHook, 'useTheme').mockReturnValue({
            theme: 'system',
            toggleTheme: vi.fn(),
            setTheme: vi.fn(),
            effectiveTheme: 'light',
        });
        vi.spyOn(pluginsHook, 'usePlugins').mockReturnValue({
            data: [],
            isLoading: false,
            isError: false,
            error: null,
            status: 'success',
            refetch: vi.fn(),
            isPending: false,
        });
        const user = userEvent.setup();
        render(_jsx(Settings, {}), { wrapper: createWrapper() });
        // Save buttons only appear once a section is dirty.
        expect(screen.queryByRole('button', { name: /save changes/i })).toBeNull();
        const poll = screen.getByLabelText(/poll interval/i);
        await user.clear(poll);
        await user.type(poll, '120');
        await user.click(screen.getByRole('button', { name: /save changes/i }));
        await waitFor(() => {
            expect(updateMutate).toHaveBeenCalledWith({ poll_interval_sec: 120 }); // only what changed
        });
    });
});
