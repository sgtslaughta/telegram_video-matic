import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMedia, useDownloadMedia, mediaKeys } from '@/hooks/useMedia'
import * as api from '@/lib/api'

vi.mock('@/lib/api')

describe('useMedia', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  it('calls api.media.list', async () => {
    const mockData = { items: [], total: 0 }
    vi.mocked(api.media.list).mockResolvedValue(mockData)

    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useMedia(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockData)
  })

  it('invalidates cache on useDownloadMedia success', async () => {
    const spy = vi.spyOn(queryClient, 'invalidateQueries')
    vi.mocked(api.media.download).mockResolvedValue({})

    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useDownloadMedia(1), { wrapper })

    await result.current.mutateAsync()

    expect(spy).toHaveBeenCalledWith({ queryKey: mediaKeys.detail(1) })
  })
})
