import { jsx as _jsx } from "react/jsx-runtime";
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from './StatusBadge';
import { MediaStatus, AccountStatus, JobStatus } from '@/lib/types';
const tone = (label) => screen.getByText(label).closest('[data-tone]')?.getAttribute('data-tone');
describe('StatusBadge', () => {
    it.each([
        [MediaStatus.READY, 'Ready', 'ok'],
        [MediaStatus.DOWNLOADING, 'Downloading', 'warn'],
        [MediaStatus.FAILED, 'Failed', 'err'],
        [AccountStatus.DISCONNECTED, 'Disconnected', 'muted'],
        [AccountStatus.CONNECTED, 'Connected', 'ok'],
        [JobStatus.PENDING, 'Pending', 'warn'],
        [AccountStatus.WAITING_CODE, 'Waiting for code', 'warn'],
        ['pruned', 'Deleted', 'muted'],
    ])('%s → %s (%s)', (status, label, t) => {
        render(_jsx(StatusBadge, { status: status }));
        expect(tone(label)).toBe(t);
    });
    it('falls back to the raw status, muted', () => {
        render(_jsx(StatusBadge, { status: "mystery" }));
        expect(tone('mystery')).toBe('muted');
    });
});
