import { jsx as _jsx } from "react/jsx-runtime";
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as api from '@/lib/api';
import { usePatchMatch, rugbyKeys } from './useRugby';
describe('usePatchMatch', () => {
    it('refreshes the filtered review list after confirming', async () => {
        vi.spyOn(api.rugby, 'patchMatch').mockResolvedValue({});
        const qc = new QueryClient();
        qc.setQueryData(rugbyKeys.matches('needs_review'), []);
        const wrapper = ({ children }) => (_jsx(QueryClientProvider, { client: qc, children: children }));
        const { result } = renderHook(() => usePatchMatch(), { wrapper });
        result.current.mutate({ mediaId: 1, status: 'confirmed' });
        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(qc.getQueryState(rugbyKeys.matches('needs_review'))?.isInvalidated).toBe(true);
    });
});
