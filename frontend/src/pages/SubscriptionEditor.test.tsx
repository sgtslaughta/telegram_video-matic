import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useSubscriptionEditor } from '@/hooks/useSubscriptionEditor'
import * as channelsHook from '@/hooks/useChannels'
import * as subsHook from '@/hooks/useSubscriptions'
import SubscriptionEditor from './SubscriptionEditor'

describe('SubscriptionEditor - Regex Validation', () => {
  it('shows valid ✅ for valid regex pattern', () => {
    const { result } = renderHook(() => useSubscriptionEditor())

    act(() => {
      result.current.update('filterRegex', '.*\\.mkv$')
    })

    expect(result.current.regexValid).toBe(true)
    expect(result.current.regexError).toBeNull()
  })

  it('shows error ❌ for invalid regex pattern', () => {
    const { result } = renderHook(() => useSubscriptionEditor())

    act(() => {
      result.current.update('filterRegex', '(?P<invalid')
    })

    expect(result.current.regexValid).toBe(false)
    expect(result.current.regexError).toBeTruthy()
  })

  it('clears error when regex becomes valid', () => {
    const { result } = renderHook(() => useSubscriptionEditor())

    // Start with invalid
    act(() => {
      result.current.update('filterRegex', '(unclosed')
    })
    expect(result.current.regexValid).toBe(false)

    // Fix it
    act(() => {
      result.current.update('filterRegex', '(closed)')
    })
    expect(result.current.regexValid).toBe(true)
    expect(result.current.regexError).toBeNull()
  })

  it('handles empty regex as valid', () => {
    const { result } = renderHook(() => useSubscriptionEditor())

    act(() => {
      result.current.update('filterRegex', '')
    })

    expect(result.current.regexValid).toBe(true)
  })
})

describe('SubscriptionEditor - UI Badge Color', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays green ✅ badge when regex is valid', async () => {
    const qc = new QueryClient()
    vi.spyOn(channelsHook, 'useChannels').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(channelsHook, 'useTopics').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useSubscription').mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useCreateSubscription').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useUpdateSubscription').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as any)

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <MemoryRouter>
        <QueryClientProvider client={qc}>
          <TooltipProvider>
            {children}
          </TooltipProvider>
        </QueryClientProvider>
      </MemoryRouter>
    )

    const user = userEvent.setup()
    const { container } = render(<SubscriptionEditor />, { wrapper })

    const regexInput = screen.getByRole('textbox', { name: /filter regex/i }) as HTMLTextAreaElement
    await user.type(regexInput, '.*\\.mkv$')

    await waitFor(
      () => {
        expect(screen.getByText(/Valid/)).toBeTruthy()
      },
      { timeout: 2000 }
    )
  })

  it('displays red ❌ badge when regex is invalid', async () => {
    const qc = new QueryClient()
    vi.spyOn(channelsHook, 'useChannels').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(channelsHook, 'useTopics').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useSubscription').mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useCreateSubscription').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useUpdateSubscription').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as any)

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <MemoryRouter>
        <QueryClientProvider client={qc}>
          <TooltipProvider>
            {children}
          </TooltipProvider>
        </QueryClientProvider>
      </MemoryRouter>
    )

    const user = userEvent.setup()
    const { container } = render(<SubscriptionEditor />, { wrapper })

    const regexInput = screen.getByRole('textbox', { name: /filter regex/i }) as HTMLTextAreaElement
    await user.type(regexInput, '(?P<invalid')

    await waitFor(
      () => {
        expect(screen.getByText(/Invalid/)).toBeTruthy()
      },
      { timeout: 2000 }
    )
  })
})
