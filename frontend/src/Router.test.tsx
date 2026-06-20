import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { ThemeProvider } from '@/hooks/useTheme'
import { Toaster } from 'sonner'
import Router from './Router'

const queryClient = new QueryClient()

describe('Router', () => {
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

  it('renders login route at /login', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <Router />
            <Toaster />
          </ThemeProvider>
        </QueryClientProvider>
      </MemoryRouter>
    )
    // Login page should NOT have sidebar (nav should not exist)
    expect(screen.getByRole('heading', { name: 'Login' })).toBeTruthy()
    expect(screen.queryByRole('navigation')).toBeFalsy()
  })

  it('renders dashboard route at /', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <Router />
            <Toaster />
          </ThemeProvider>
        </QueryClientProvider>
      </MemoryRouter>
    )
    // Dashboard should have sidebar
    expect(screen.getByRole('navigation')).toBeTruthy()
    // Check for main dashboard content (hero banner or stat cards)
    const mainContent = screen.getByRole('main')
    expect(mainContent.textContent).toContain('Welcome back')
  })
})
