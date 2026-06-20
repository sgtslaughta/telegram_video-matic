import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useSubscriptions, useCreateSubscription, subscriptionKeys } from '@/hooks/useSubscriptions'
import * as api from '@/lib/api'

vi.mock('@/lib/api')

describe('useSubscriptions', () => {
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

  it('calls api.subscriptions.list', async () => {
    const mockData = [{ id: 1, name: 'Test' }]
    vi.mocked(api.subscriptions.list).mockResolvedValue(mockData)

    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useSubscriptions(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(mockData)
  })

  it('invalidates cache on useCreateSubscription success', async () => {
    const spy = vi.spyOn(queryClient, 'invalidateQueries')
    vi.mocked(api.subscriptions.create).mockResolvedValue({ id: 1 })

    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useCreateSubscription(), { wrapper })

    await result.current.mutateAsync({ name: 'Test' } as any)

    expect(spy).toHaveBeenCalledWith({ queryKey: subscriptionKeys.list() })
  })
})
