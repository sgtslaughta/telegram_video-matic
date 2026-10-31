import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import * as api from '@/lib/api'
import { usePatchMatch, rugbyKeys } from './useRugby'

describe('usePatchMatch', () => {
  it('refreshes the filtered review list after confirming', async () => {
    vi.spyOn(api.rugby, 'patchMatch').mockResolvedValue({} as never)
    const qc = new QueryClient()
    qc.setQueryData(rugbyKeys.matches('needs_review'), [])
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => usePatchMatch(), { wrapper })
    result.current.mutate({ mediaId: 1, status: 'confirmed' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(qc.getQueryState(rugbyKeys.matches('needs_review'))?.isInvalidated).toBe(true)
  })
})
