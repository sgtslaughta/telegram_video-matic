import { jsx as _jsx } from "react/jsx-runtime";
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WelcomeSplash from './WelcomeSplash';
const summary = (show) => ({
    since: '2026-10-30T10:00:00Z', show,
    incidents: [{ kind: 'telegram_down', started: '2026-10-30T12:00:00Z', ended: '2026-10-30T17:00:00Z', hours: 5 }],
    arrivals: [{ group: 'English Prem Rugby, round 4', items: [{ id: 1, title: 'Bath vs Gloucester', subtitle: null, size_bytes: 1, duration_sec: 1, at: null, has_thumb: false }] }],
    attention: { failed: 2, needs_review: 0, wanted: 0, cleanup_paused: null },
    stats: { downloaded: 1, bytes: 3700000000 },
});
function mount(show) {
    const calls = [];
    vi.stubGlobal('fetch', vi.fn(async (url) => {
        calls.push(url);
        return new Response(JSON.stringify(url.endsWith('/seen') ? {} : summary(show)), { status: 200 });
    }));
    render(_jsx(MemoryRouter, { children: _jsx(QueryClientProvider, { client: new QueryClient(), children: _jsx(WelcomeSplash, {}) }) }));
    return calls;
}
describe('WelcomeSplash', () => {
    beforeEach(() => vi.unstubAllGlobals());
    it('shows problems first, arrivals and attention when there is news', async () => {
        mount(true);
        expect(await screen.findByText('Since your last visit')).toBeTruthy();
        expect(screen.getByText(/offline for about 5 hours/)).toBeTruthy();
        expect(screen.getByText('Bath vs Gloucester')).toBeTruthy();
        expect(screen.getByText('2 failed downloads')).toBeTruthy();
    });
    it('stays hidden and records the visit when nothing to show', async () => {
        const calls = mount(false);
        await waitFor(() => expect(calls.some((c) => c.endsWith('/summary/seen'))).toBe(true));
        expect(screen.queryByText('Since your last visit')).toBeNull();
    });
});
