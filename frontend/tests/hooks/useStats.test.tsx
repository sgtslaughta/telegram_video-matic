import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useStats } from '@/hooks/useStats'
import * as api from '@/lib/api'

vi.mock('@/lib/api')

const wrap = (qc: QueryClient) => ({ children }: any) => (
  <QueryClientProvider client={qc}>{children}</QueryClientProvider>
)

describe('useStats', () => {
  let qc: QueryClient
  beforeEach(() => {
    qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    vi.clearAllMocks()
  })

  it('derives counts and storage from subscriptions + media', async () => {
    vi.mocked(api.subscriptions.list).mockResolvedValue([
      { id: 1, enabled: true }, { id: 2, enabled: false }, { id: 3, enabled: true },
    ] as any)
    vi.mocked(api.media.list).mockImplementation((f: any) =>
      Promise.resolve(
        f?.status === 'downloaded'
          ? ([{ id: 1, size_bytes: 100 }, { id: 2, size_bytes: 50 }] as any)
          : ([{ id: 9 }] as any) // failed
      )
    )

    const { result } = renderHook(() => useStats(), { wrapper: wrap(qc) })

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.activeSubs).toBe(2)
    expect(result.current.downloaded).toBe(2)
    expect(result.current.failed).toBe(1)
    expect(result.current.storageBytes).toBe(150)
  })
})
