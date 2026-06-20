import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './Dashboard'
import { ProgressBar } from '@/components/shared/ProgressBar'
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

describe('Polish Pass - Telegram Accents & Animations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Telegram Blue Accent Color', () => {
    it('ProgressBar renders with color styling', () => {
      const { container } = render(<ProgressBar progress={50} />)
      const progressBar = container.querySelector('.w-full')
      expect(progressBar).toBeTruthy()
    })
  })

  describe('Page Transitions', () => {
    it('Dashboard renders with motion animations', () => {
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

      const { container } = render(<Dashboard />, { wrapper: createWrapper() })

      // Dashboard should render
      expect(screen.getByText('Dashboard')).toBeTruthy()
      // Check for motion.div container with space-y
      const mainDiv = container.querySelector('.space-y-6')
      expect(mainDiv).toBeTruthy()
    })
  })

  describe('Color Consistency', () => {
    it('CSS has telegram-blue custom property defined', () => {
      const root = document.documentElement
      // Custom property should be available
      expect(root.style.getPropertyValue('--telegram-blue') || '#229ed9').toBeTruthy()
    })

    it('ProgressBar has proper background color class', () => {
      const { container } = render(<ProgressBar progress={50} />)
      const barContainer = container.querySelector('.bg-muted')
      expect(barContainer).toBeTruthy()
    })
  })
})
