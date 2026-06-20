import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useSettings, useUpdateSettings, settingKeys } from '@/hooks/useSettings'
import * as api from '@/lib/api'

vi.mock('@/lib/api')

describe('useSettings', () => {
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

  it('calls api.settings.get', async () => {
    const mockData = { theme: 'dark' }
    vi.mocked(api.settings.get).mockResolvedValue(mockData)

    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useSettings(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockData)
  })

  it('updates cache on useUpdateSettings success', async () => {
    const spy = vi.spyOn(queryClient, 'setQueryData')
    const mockData = { theme: 'light' }
    vi.mocked(api.settings.update).mockResolvedValue(mockData)

    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useUpdateSettings(), { wrapper })

    await result.current.mutateAsync({ theme: 'light' } as any)

    expect(spy).toHaveBeenCalledWith(settingKeys.all(), mockData)
  })
})
