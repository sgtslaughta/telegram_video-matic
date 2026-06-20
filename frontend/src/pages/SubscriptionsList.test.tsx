import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import SubscriptionsList from './SubscriptionsList'
import * as subsHook from '@/hooks/useSubscriptions'
import type { SubscriptionRead } from '@/lib/types'

const createWrapper = () => {
  const queryClient = new QueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          {children}
        </TooltipProvider>
      </QueryClientProvider>
    </BrowserRouter>
  )
}

const mockSub: SubscriptionRead = {
  id: 1,
  channel_id: 100,
  enabled: true,
  mode: 'auto',
  filter_mode: 'include',
  storage_path: '/tmp',
  rename_template: '{title}',
  season_detection: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('SubscriptionsList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders subscriptions list', () => {
    vi.spyOn(subsHook, 'useSubscriptions').mockReturnValue({
      data: [mockSub],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<SubscriptionsList />, { wrapper: createWrapper() })

    expect(screen.getByText('Subscriptions')).toBeTruthy()
    expect(screen.getByText('Channel 100')).toBeTruthy()
  })

  it('toggle calls useUpdateSubscription with enabled: false', () => {
    const mockMutate = vi.fn()
    vi.spyOn(subsHook, 'useSubscriptions').mockReturnValue({
      data: [mockSub],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useUpdateSubscription').mockReturnValue({
      mutate: mockMutate,
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
      status: 'idle',
      reset: vi.fn(),
    } as any)
    vi.spyOn(subsHook, 'useDeleteSubscription').mockReturnValue({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
      status: 'idle',
      reset: vi.fn(),
    } as any)
    vi.spyOn(subsHook, 'useScanSubscription').mockReturnValue({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
      status: 'idle',
      reset: vi.fn(),
    } as any)

    render(<SubscriptionsList />, { wrapper: createWrapper() })

    const buttons = screen.getAllByRole('button')
    const disableBtn = buttons.find(btn => btn.getAttribute('aria-label')?.includes('Disable') || btn.textContent?.includes('Disable'))
    if (disableBtn) fireEvent.click(disableBtn)

    expect(mockMutate).toHaveBeenCalledWith({ enabled: false })
  })
})
