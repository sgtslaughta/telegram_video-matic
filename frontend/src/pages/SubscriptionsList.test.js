import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { TooltipProvider } from '@/components/ui/tooltip';
import SubscriptionsList from './SubscriptionsList';
import * as subsHook from '@/hooks/useSubscriptions';
import * as channelsHook from '@/hooks/useChannels';
import * as overviewHook from '@/hooks/useOverview';
const sub = (over) => ({
    id: 1, channel_id: 100, enabled: true, mode: 'auto', filter_mode: 'include', storage_path: '/tmp',
    rename_template: '{title}', season_detection: false, check_frequency: '15m',
    created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z', ...over,
});
const Where = () => _jsx("p", { "data-testid": "loc", children: useLocation().pathname });
const mutation = (mutateAsync = vi.fn().mockResolvedValue({})) => ({ mutate: vi.fn(), mutateAsync, isPending: false });
function setup(subs, update = vi.fn().mockResolvedValue({})) {
    vi.spyOn(subsHook, 'useSubscriptions').mockReturnValue({ data: subs, isLoading: false });
    vi.spyOn(subsHook, 'useUpdateSubscription').mockReturnValue(mutation(update));
    vi.spyOn(subsHook, 'useDeleteSubscription').mockReturnValue(mutation());
    vi.spyOn(subsHook, 'useScanSubscription').mockReturnValue(mutation());
    vi.spyOn(channelsHook, 'useChannels').mockReturnValue({ data: [{ id: 100, title: 'Rugby HQ' }] });
    vi.spyOn(overviewHook, 'useOverview').mockReturnValue({ data: { subscriptions: [] } });
    render(_jsx(MemoryRouter, { children: _jsx(QueryClientProvider, { client: new QueryClient(), children: _jsx(TooltipProvider, { children: _jsx(Routes, { children: _jsx(Route, { path: "*", element: _jsxs(_Fragment, { children: [_jsx(SubscriptionsList, {}), _jsx(Where, {})] }) }) }) }) }) }));
    return update;
}
describe('SubscriptionsList', () => {
    beforeEach(() => vi.restoreAllMocks());
    it('shows name, channel, frequency and filter summary', () => {
        setup([sub({ name: 'Matches', filter_regex: 'final' })]);
        expect(screen.getByText('Matches')).toBeTruthy();
        expect(screen.getByText('Rugby HQ')).toBeTruthy();
        expect(screen.getByText('Every 15 min')).toBeTruthy();
        expect(screen.getByText('Only final')).toBeTruthy();
    });
    it('shows an empty-state sentence with no subscriptions', () => {
        setup([]);
        expect(screen.getByText(/No subscriptions yet/)).toBeTruthy();
    });
    it('switch pauses the subscription', async () => {
        const update = setup([sub({ name: 'Matches' })]);
        fireEvent.click(screen.getByRole('switch', { name: /pause matches/i }));
        await waitFor(() => expect(update).toHaveBeenCalledWith({ enabled: false }));
    });
    it('row click opens the editor', () => {
        setup([sub({ id: 7, name: 'Matches' })]);
        fireEvent.click(screen.getByText('Matches'));
        expect(screen.getByTestId('loc').textContent).toBe('/subscriptions/7');
    });
    it('j moves focus and e edits the focused row', async () => {
        setup([sub({ id: 1, name: 'First' }), sub({ id: 2, name: 'Second' })]);
        const user = userEvent.setup();
        await user.keyboard('j');
        expect(document.activeElement?.getAttribute('data-sub-id')).toBe('2');
        await user.keyboard('e');
        expect(screen.getByTestId('loc').textContent).toBe('/subscriptions/2');
    });
});
