import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useTgStatus, useTgLoginPhone, tgKeys } from '@/hooks/useTgStatus'
import * as api from '@/lib/api'

vi.mock('@/lib/api')

describe('useTgStatus', () => {
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

  it('calls api.tg.status', async () => {
    const mockData = { authenticated: false }
    vi.mocked(api.tg.status).mockResolvedValue(mockData)

    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useTgStatus(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockData)
  })

  it('invalidates cache on useTgLoginPhone success', async () => {
    const spy = vi.spyOn(queryClient, 'invalidateQueries')
    vi.mocked(api.tg.loginPhone).mockResolvedValue({})

    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useTgLoginPhone(), { wrapper })

    await result.current.mutateAsync('+1234567890')

    expect(spy).toHaveBeenCalledWith({ queryKey: tgKeys.status() })
  })
})
