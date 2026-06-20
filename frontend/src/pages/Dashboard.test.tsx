import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './Dashboard'
import * as hooks from '@/hooks/useDownloads'
import * as eventsHook from '@/hooks/useEvents'
import * as subsHook from '@/hooks/useSubscriptions'
import * as tgHook from '@/hooks/useTgStatus'

const createWrapper = () => {
  const queryClient = new QueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard hero banner', () => {
    vi.spyOn(hooks, 'useActiveDownloads').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useSubscriptions').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(tgHook, 'useTgStatus').mockReturnValue({
      data: { status: 'connected', username: 'testuser' },
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Dashboard />, { wrapper: createWrapper() })

    expect(screen.getByText('Welcome back')).toBeTruthy()
    expect(screen.getByText('Subscriptions')).toBeTruthy()
    expect(screen.getByText('Active Downloads')).toBeTruthy()
  })

  it('renders stat cards with correct labels', () => {
    vi.spyOn(hooks, 'useActiveDownloads').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useSubscriptions').mockReturnValue({
      data: [
        { id: 1, enabled: true, channel_id: 1, storage_path: '/tmp', rename_template: '', filter_mode: '', season_detection: false, created_at: '', updated_at: '', mode: '' },
      ],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(tgHook, 'useTgStatus').mockReturnValue({
      data: { status: 'connected', username: 'testuser' },
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Dashboard />, { wrapper: createWrapper() })

    expect(screen.getByText('Pending')).toBeTruthy()
    expect(screen.getByText('Downloaded')).toBeTruthy()
  })

  it('renders active download with progress bar', () => {
    const mockDownload = {
      id: 1,
      media_id: 100,
      status: 'downloading',
      progress: 45,
      speed_bps: 1024 * 1024 * 2.4, // 2.4 MB/s
      eta_sec: 120,
      bytes_done: 100000000,
      bytes_total: 220000000,
      attempt: 1,
    }

    vi.spyOn(hooks, 'useActiveDownloads').mockReturnValue({
      data: [mockDownload],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(eventsHook, 'useEvents').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(subsHook, 'useSubscriptions').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)
    vi.spyOn(tgHook, 'useTgStatus').mockReturnValue({
      data: { status: 'connected' },
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Dashboard />, { wrapper: createWrapper() })

    expect(screen.getByText('1 active download')).toBeTruthy()
    expect(screen.getByText(/45%/)).toBeTruthy()
  })

  it('updates progress bar width when download progress changes', () => {
    const mockDownload1 = {
      id: 1,
      media_id: 100,
      status: 'downloading',
      progress: 30,
      speed_bps: 1024 * 1024 * 2.4,
      eta_sec: 120,
      bytes_done: 50000000,
      bytes_total: 220000000,
      attempt: 1,
    }

    const { rerender } = render(<Dashboard />, { wrapper: createWrapper() })

    vi.spyOn(hooks, 'useActiveDownloads').mockReturnValue({
      data: [mockDownload1],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    rerender(<Dashboard />)
    expect(screen.getByText(/30%/)).toBeTruthy()

    const mockDownload2 = { ...mockDownload1, progress: 75 }
    vi.spyOn(hooks, 'useActiveDownloads').mockReturnValue({
      data: [mockDownload2],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    rerender(<Dashboard />)
    expect(screen.getByText(/75%/)).toBeTruthy()
  })
})
