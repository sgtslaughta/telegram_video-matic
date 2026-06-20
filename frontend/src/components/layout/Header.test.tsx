import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { ThemeProvider } from '@/hooks/useTheme'
import Header from './Header'

const queryClient = new QueryClient()

// Mock the API
vi.mock('@/lib/api')

describe('Header', () => {
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

  it('renders search input', () => {
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <Header connected={false} onConnectClick={() => {}} />
          </ThemeProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )
    const searchInput = screen.getByPlaceholderText('Search…')
    expect(searchInput).toBeTruthy()
  })

  it('renders theme toggle button', () => {
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <Header connected={false} onConnectClick={() => {}} />
          </ThemeProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )
    const themeButton = screen.getByLabelText('Toggle theme')
    expect(themeButton).toBeTruthy()
  })

  it('renders user menu button', () => {
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <Header connected={false} onConnectClick={() => {}} />
          </ThemeProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )
    const userMenu = screen.getByLabelText('User menu')
    expect(userMenu).toBeTruthy()
  })

  it('renders status badge', () => {
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <Header connected={true} onConnectClick={() => {}} />
          </ThemeProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )
    const statusBadge = screen.getByText('Telegram')
    expect(statusBadge).toBeTruthy()
  })
})
