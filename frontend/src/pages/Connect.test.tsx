import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Connect from './Connect'
import * as tgHook from '@/hooks/useTgStatus'
import { AccountStatus } from '@/lib/types'

const createWrapper = () => {
  const queryClient = new QueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('Connect', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows phone step when status is disconnected', () => {
    vi.spyOn(tgHook, 'useTgStatus').mockReturnValue({
      data: { status: AccountStatus.DISCONNECTED },
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(tgHook, 'useTgLoginPhone').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)
    vi.spyOn(tgHook, 'useTgLoginCode').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)
    vi.spyOn(tgHook, 'useTgLoginPassword').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)
    vi.spyOn(tgHook, 'useTgLogout').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)

    render(<Connect />, { wrapper: createWrapper() })

    expect(screen.getByText('Enter phone number')).toBeTruthy()
    expect(screen.getByPlaceholderText('+1 234 567 8900')).toBeTruthy()
  })

  it('shows code step when status is awaiting_code', () => {
    vi.spyOn(tgHook, 'useTgStatus').mockReturnValue({
      data: { status: AccountStatus.WAITING_CODE },
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(tgHook, 'useTgLoginPhone').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)
    vi.spyOn(tgHook, 'useTgLoginCode').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)
    vi.spyOn(tgHook, 'useTgLoginPassword').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)
    vi.spyOn(tgHook, 'useTgLogout').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)

    render(<Connect />, { wrapper: createWrapper() })

    expect(screen.getByText('Enter SMS code')).toBeTruthy()
    expect(screen.getByPlaceholderText('123456')).toBeTruthy()
  })

  it('shows confirmation when status is connected', () => {
    vi.spyOn(tgHook, 'useTgStatus').mockReturnValue({
      data: {
        status: AccountStatus.CONNECTED,
        username: 'testuser',
        display_name: 'Test User',
        phone: '+1234567890',
      },
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(tgHook, 'useTgLoginPhone').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)
    vi.spyOn(tgHook, 'useTgLoginCode').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)
    vi.spyOn(tgHook, 'useTgLoginPassword').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)
    vi.spyOn(tgHook, 'useTgLogout').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      mutate: vi.fn(),
      isError: false,
      error: null,
      status: 'idle',
      data: undefined,
      reset: vi.fn(),
      variables: undefined,
    } as any)

    render(<Connect />, { wrapper: createWrapper() })

    expect(screen.getByText('Connected!')).toBeTruthy()
    expect(screen.getByText('@testuser')).toBeTruthy()
    expect(screen.getByText(/account verified/i)).toBeTruthy()
  })
})
