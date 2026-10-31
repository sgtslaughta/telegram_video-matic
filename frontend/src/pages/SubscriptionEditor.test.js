import { jsx as _jsx } from "react/jsx-runtime";
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { TooltipProvider } from '@/components/ui/tooltip';
import { useSubscriptionEditor } from '@/hooks/useSubscriptionEditor';
import * as channelsHook from '@/hooks/useChannels';
import * as subsHook from '@/hooks/useSubscriptions';
import * as toolsHook from '@/hooks/useSubscriptionTools';
import SubscriptionEditor from './SubscriptionEditor';
describe('SubscriptionEditor - Regex Validation', () => {
    it('shows valid ✅ for valid regex pattern', () => {
        const { result } = renderHook(() => useSubscriptionEditor());
        act(() => {
            result.current.update('filterRegex', '.*\\.mkv$');
        });
        expect(result.current.regexValid).toBe(true);
        expect(result.current.regexError).toBeNull();
    });
    it('shows error ❌ for invalid regex pattern', () => {
        const { result } = renderHook(() => useSubscriptionEditor());
        act(() => {
            result.current.update('filterRegex', '(?P<invalid');
        });
        expect(result.current.regexValid).toBe(false);
        expect(result.current.regexError).toBeTruthy();
    });
    it('clears error when regex becomes valid', () => {
        const { result } = renderHook(() => useSubscriptionEditor());
        // Start with invalid
        act(() => {
            result.current.update('filterRegex', '(unclosed');
        });
        expect(result.current.regexValid).toBe(false);
        // Fix it
        act(() => {
            result.current.update('filterRegex', '(closed)');
        });
        expect(result.current.regexValid).toBe(true);
        expect(result.current.regexError).toBeNull();
    });
    it('handles empty regex as valid', () => {
        const { result } = renderHook(() => useSubscriptionEditor());
        act(() => {
            result.current.update('filterRegex', '');
        });
        expect(result.current.regexValid).toBe(true);
    });
});
describe('useSubscriptionEditor - dirty tracking', () => {
    it('is clean until changed, and discard restores', () => {
        const { result } = renderHook(() => useSubscriptionEditor());
        expect(result.current.dirty).toBe(false);
        act(() => result.current.update('keep', true));
        expect(result.current.dirty).toBe(true);
        act(() => result.current.discard());
        expect(result.current.dirty).toBe(false);
        expect(result.current.state.keep).toBe(false);
    });
});
const q = (data) => ({ data, isLoading: false, isError: false, error: null, status: 'success', refetch: vi.fn(), isPending: false });
const IDLE = { data: undefined, isFetching: false, error: null };
const existing = {
    id: 3, channel_id: 5, topic_id: 9, name: 'Matches', enabled: true, mode: 'immediate', filter_mode: 'include',
    storage_path: '/media', rename_template: '{title}', season_detection: false,
    created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z',
};
function mountEditor(path = '/subscriptions/new', opts = {}) {
    vi.spyOn(channelsHook, 'useChannels').mockReturnValue(q([{ id: 5, title: 'Chan' }]));
    vi.spyOn(channelsHook, 'useTopics').mockReturnValue(q([]));
    vi.spyOn(subsHook, 'useSubscription').mockReturnValue(q(opts.sub ?? null));
    vi.spyOn(subsHook, 'useCreateSubscription').mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    vi.spyOn(subsHook, 'useUpdateSubscription').mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    vi.spyOn(toolsHook, 'useFilterPreview').mockReturnValue((opts.preview ?? IDLE));
    return render(_jsx(MemoryRouter, { initialEntries: [path], children: _jsx(QueryClientProvider, { client: new QueryClient(), children: _jsx(TooltipProvider, { children: _jsx(Routes, { children: _jsx(Route, { path: "/subscriptions/:id", element: _jsx(SubscriptionEditor, {}) }) }) }) }) }));
}
describe('SubscriptionEditor page', () => {
    beforeEach(() => vi.restoreAllMocks());
    it('shows a valid marker for a valid regex', async () => {
        mountEditor();
        await userEvent.setup().type(screen.getByRole('textbox', { name: /filter regex/i }), '.*\\.mkv$');
        await waitFor(() => expect(screen.getByText(/Valid pattern/)).toBeTruthy());
    });
    it('shows an inline error for an invalid regex', async () => {
        mountEditor();
        await userEvent.setup().type(screen.getByRole('textbox', { name: /filter regex/i }), '(?P<invalid');
        await waitFor(() => expect(screen.getByRole('alert').textContent).toMatch(/✗/));
    });
    it('shows preview counts and skip reasons', () => {
        const row = { file_name: 'a.mp4', caption: null, size_bytes: 1000, date_posted: '2026-01-01T00:00:00Z', reason: '' };
        mountEditor('/subscriptions/3', { sub: existing, preview: { isFetching: false, error: null, data: [
                    { ...row, tg_msg_id: 1, would: 'download' },
                    { ...row, tg_msg_id: 2, file_name: 'b.mp4', would: 'skip', reason: 'no regex match' },
                ] } });
        expect(screen.getByTestId('preview-counts').textContent).toBe('1 would download, 1 skipped');
        expect(screen.getByText('no regex match')).toBeTruthy();
    });
    it('surfaces a 400 from the preview under the regex field', async () => {
        mountEditor('/subscriptions/new', { preview: { data: undefined, isFetching: false, error: Object.assign(new Error('bad escape'), { status: 400 }) } });
        await userEvent.setup().type(screen.getByRole('textbox', { name: /filter regex/i }), 'x');
        expect(screen.getByRole('alert').textContent).toContain('bad escape');
    });
    it('save bar appears only once dirty and Discard hides it', async () => {
        mountEditor('/subscriptions/3', { sub: existing });
        expect(screen.queryByRole('region', { name: /unsaved/i })).toBeNull();
        await userEvent.setup().type(screen.getByLabelText('Name'), 'x');
        expect(screen.getByRole('button', { name: 'Save changes' })).toBeTruthy();
        fireEvent.click(screen.getByRole('button', { name: 'Discard' }));
        await waitFor(() => expect(screen.queryByRole('region', { name: /unsaved/i })).toBeNull());
    });
    it('has retention helper text, keep switch and rescan tool when editing', () => {
        mountEditor('/subscriptions/3', { sub: existing });
        expect(screen.getByText('Leave empty to use the global setting')).toBeTruthy();
        expect(screen.getByRole('switch', { name: 'Keep forever' })).toBeTruthy();
        fireEvent.click(screen.getByRole('button', { name: 'Rescan' }));
        expect(screen.getByLabelText('Days to look back')).toBeTruthy();
    });
    it('Cmd+S does not throw with an incomplete form', () => {
        mountEditor();
        fireEvent.keyDown(window, { key: 's', metaKey: true });
    });
});
