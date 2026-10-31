import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { TooltipProvider } from '@/components/ui/tooltip';
import Downloads from './Downloads';
vi.mock('@/hooks/useWebSocket', () => ({ useWebSocket: () => undefined }));
const game = { fixture_id: 7, league: 'Premiership', season: '2026', round: '3', home: 'Bath', away: 'Leicester', date: '2026-10-01T12:00:00Z', days_missing: 3, last_searched_at: null, attempts: 0, state: 'missing', subscription_id: 2 };
const cand = { channel_id: 1, tg_msg_id: 99, file_name: 'bath-leicester.mp4', caption: null, size_bytes: 1000, date: '2026-10-02T12:00:00Z', confidence: 0.9, auto: true, already_tracked: false, media_id: null, media_status: null };
const calls = [];
const json = (b, status = 200) => Promise.resolve(new Response(JSON.stringify(b), { status }));
beforeEach(() => {
    calls.length = 0;
    vi.stubGlobal('fetch', vi.fn((url, init) => {
        const path = String(url).replace('/api', '');
        calls.push(`${init?.method ?? 'GET'} ${path}`);
        if (path.startsWith('/plugins/rugby/wanted/7/search'))
            return json([cand]);
        if (path === '/plugins/rugby/wanted/7/grab')
            return json({ media_id: 5, status: 'pending' });
        if (path === '/plugins/rugby/wanted')
            return json([game]);
        if (path.startsWith('/rugby/matches') || path.includes('matches'))
            return json([]);
        return json([]);
    }));
});
afterEach(() => vi.unstubAllGlobals());
function Loc() { return _jsx("span", { "data-testid": "loc", children: useLocation().search }); }
function setup(url) {
    render(_jsx(QueryClientProvider, { client: new QueryClient({ defaultOptions: { queries: { retry: false } } }), children: _jsx(TooltipProvider, { children: _jsxs(MemoryRouter, { initialEntries: [url], children: [_jsx(Downloads, {}), _jsx(Loc, {})] }) }) }));
}
describe('Downloads', () => {
    it('shows queue empty state by default and switches tab via URL', async () => {
        setup('/downloads');
        expect(await screen.findByText(/Nothing downloading/)).toBeTruthy();
        await userEvent.click(screen.getByRole('tab', { name: /History/ }));
        expect(screen.getByTestId('loc').textContent).toBe('?tab=history');
        await userEvent.click(screen.getByRole('tab', { name: /Queue/ }));
        expect(screen.getByTestId('loc').textContent).toBe('');
    });
    it('opens the tab named in the URL', async () => {
        setup('/downloads?tab=wanted');
        expect(await screen.findByText('Bath vs Leicester')).toBeTruthy();
    });
    it('searches a missing game and grabs a candidate', async () => {
        setup('/downloads?tab=wanted');
        await screen.findByText('Bath vs Leicester');
        fireEvent.click(screen.getByRole('button', { name: 'Search' }));
        expect(await screen.findByText('bath-leicester.mp4')).toBeTruthy();
        expect(calls).toContain('POST /plugins/rugby/wanted/7/search?subscription_id=2');
        fireEvent.click(screen.getByRole('button', { name: 'Grab' }));
        await waitFor(() => expect(calls).toContain('POST /plugins/rugby/wanted/7/grab'));
        expect(await screen.findByRole('button', { name: 'Queued' })).toBeTruthy();
    });
});
