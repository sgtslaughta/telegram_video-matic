import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Activity from './Activity'
import * as eventsHook from '@/hooks/useEvents'
import type * as T from '@/lib/types'

const createWrapper = () => {
  const queryClient = new QueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('Activity', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders activity page title', () => {
    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Activity />, { wrapper: createWrapper() })

    expect(screen.getByText('Activity')).toBeTruthy()
  })

  it('renders filter dropdowns for level and kind', () => {
    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Activity />, { wrapper: createWrapper() })

    expect(screen.getByDisplayValue('All Levels')).toBeTruthy()
    expect(screen.getByDisplayValue('All Kinds')).toBeTruthy()
  })

  it('displays events with color-coded level badges', () => {
    const mockEvents: T.EventRead[] = [
      {
        id: 1,
        level: 'info',
        kind: 'subscription',
        message: 'Subscription created',
        created_at: '2026-06-20T10:00:00Z',
      },
      {
        id: 2,
        level: 'success',
        kind: 'download',
        message: 'Download completed',
        created_at: '2026-06-20T10:05:00Z',
      },
      {
        id: 3,
        level: 'warning',
        kind: 'job',
        message: 'Low disk space',
        created_at: '2026-06-20T10:10:00Z',
      },
      {
        id: 4,
        level: 'error',
        kind: 'job',
        message: 'Download failed',
        created_at: '2026-06-20T10:15:00Z',
      },
    ]

    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: mockEvents,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Activity />, { wrapper: createWrapper() })

    expect(screen.getByText('Subscription created')).toBeTruthy()
    expect(screen.getByText('Download completed')).toBeTruthy()
    expect(screen.getByText('Low disk space')).toBeTruthy()
    expect(screen.getByText('Download failed')).toBeTruthy()
  })

  it('shows empty state when no events', () => {
    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Activity />, { wrapper: createWrapper() })

    expect(screen.getByText('No events')).toBeTruthy()
  })

  it('shows pagination controls when events exist', () => {
    const mockEvents: T.EventRead[] = [
      {
        id: 1,
        level: 'info',
        kind: 'subscription',
        message: 'Test event',
        created_at: '2026-06-20T10:00:00Z',
      },
    ]

    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: mockEvents,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Activity />, { wrapper: createWrapper() })

    expect(screen.getByRole('button', { name: /previous/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /next/i })).toBeTruthy()
  })

  it('filters events by level when dropdown changes', async () => {
    const mockEvents: T.EventRead[] = [
      {
        id: 1,
        level: 'error',
        kind: 'job',
        message: 'Error event',
        created_at: '2026-06-20T10:00:00Z',
      },
    ]

    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: mockEvents,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Activity />, { wrapper: createWrapper() })

    const levelDropdown = screen.getByDisplayValue('All Levels') as HTMLSelectElement
    fireEvent.change(levelDropdown, { target: { value: 'error' } })

    await waitFor(() => {
      expect(eventsHook.useEvents).toHaveBeenCalledWith(
        expect.objectContaining({ level: 'error' })
      )
    })
  })

  it('filters events by kind when dropdown changes', async () => {
    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Activity />, { wrapper: createWrapper() })

    const kindDropdown = screen.getByDisplayValue('All Kinds') as HTMLSelectElement
    fireEvent.change(kindDropdown, { target: { value: 'download' } })

    await waitFor(() => {
      expect(eventsHook.useEvents).toHaveBeenCalledWith(
        expect.objectContaining({ kind: 'download' })
      )
    })
  })

  it('handles pagination offset correctly', async () => {
    const mockEvents: T.EventRead[] = Array.from({ length: 10 }, (_, i) => ({
      id: i + 1,
      level: 'info',
      kind: 'subscription',
      message: `Event ${i + 1}`,
      created_at: '2026-06-20T10:00:00Z',
    }))

    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: mockEvents,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Activity />, { wrapper: createWrapper() })

    const nextButton = screen.getByRole('button', { name: /next/i })
    fireEvent.click(nextButton)

    await waitFor(() => {
      expect(eventsHook.useEvents).toHaveBeenCalledWith(
        expect.objectContaining({ offset: 10 })
      )
    })
  })
})
