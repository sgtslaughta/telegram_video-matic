import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { ThemeProvider } from '@/hooks/useTheme'
import Shell from './Shell'

const queryClient = new QueryClient()

// Mock the hooks
vi.mock('@/hooks/useTgStatus', () => ({
  useTgStatus: () => ({
    data: { authenticated: true },
    isLoading: false,
  }),
}))

vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => true,
}))

describe('Shell', () => {
  beforeEach(() => {
    // Mock window.matchMedia for tests
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    })
  })

  it('renders sidebar', () => {
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <Shell />
          </ThemeProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )
    expect(screen.getByRole('navigation')).toBeTruthy()
  })

  it('renders header', () => {
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <Shell />
          </ThemeProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )
    // Header should contain either a button for theme toggle or have TG status
    const header = screen.getByRole('banner')
    expect(header).toBeTruthy()
  })
})
