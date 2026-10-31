import { jsx as _jsx } from "react/jsx-runtime";
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MediaPlayer } from './MediaPlayer';
const base = { id: 7, channel_id: 1, tg_msg_id: 1, date_posted: '2026-01-01T00:00:00Z', created_at: '', updated_at: '' };
const mk = (o) => ({ ...base, status: 'pending', ...o });
const noop = () => { };
describe('MediaPlayer', () => {
    it('streams downloaded media with range-capable native video', () => {
        const { container } = render(_jsx(MediaPlayer, { item: mk({ status: 'downloaded' }), busy: false, onDownload: noop, onRetry: noop }));
        const v = container.querySelector('video');
        expect(v.getAttribute('src')).toBe('/api/media/7/stream');
        expect(v.getAttribute('poster')).toBe('/api/media/7/thumb');
        expect(v.getAttribute('preload')).toBe('metadata');
    });
    it('shows the skip reason instead of a player', () => {
        const { container } = render(_jsx(MediaPlayer, { item: mk({ skip_reason: 'Larger than 2 GB limit' }), busy: false, onDownload: noop, onRetry: noop }));
        expect(container.querySelector('video')).toBeNull();
        expect(screen.getByText('Larger than 2 GB limit')).toBeTruthy();
    });
    it('offers Retry download when failed', () => {
        const onRetry = vi.fn();
        render(_jsx(MediaPlayer, { item: mk({ status: 'failed', error: 'Timeout' }), busy: false, onDownload: noop, onRetry: onRetry }));
        expect(screen.getByText('Timeout')).toBeTruthy();
        fireEvent.click(screen.getByText('Retry download'));
        expect(onRetry).toHaveBeenCalled();
    });
});
