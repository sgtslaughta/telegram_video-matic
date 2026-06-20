import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useTheme, ThemeProvider } from '@/hooks/useTheme'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
    // Mock matchMedia
    window.matchMedia = vi.fn(() => ({
      matches: false,
      media: '(prefers-color-scheme: dark)',
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })) as any
  })

  it('toggles through light → dark → system', () => {
    const qc = new QueryClient()
    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={qc}>
        <ThemeProvider>{children}</ThemeProvider>
      </QueryClientProvider>
    )
    const { result } = renderHook(() => useTheme(), { wrapper })

    expect(result.current.theme).toBe('system')

    act(() => result.current.toggleTheme())
    expect(result.current.theme).toBe('light')

    act(() => result.current.toggleTheme())
    expect(result.current.theme).toBe('dark')

    act(() => result.current.toggleTheme())
    expect(result.current.theme).toBe('system')
  })

  it('persists theme to localStorage', () => {
    const qc = new QueryClient()
    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={qc}>
        <ThemeProvider>{children}</ThemeProvider>
      </QueryClientProvider>
    )
    const { result } = renderHook(() => useTheme(), { wrapper })

    act(() => result.current.toggleTheme())
    expect(localStorage.getItem('theme')).toBe('light')

    act(() => result.current.toggleTheme())
    expect(localStorage.getItem('theme')).toBe('dark')
  })

  it('applies dark class to document', () => {
    const qc = new QueryClient()
    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={qc}>
        <ThemeProvider>{children}</ThemeProvider>
      </QueryClientProvider>
    )
    const { result } = renderHook(() => useTheme(), { wrapper })

    expect(document.documentElement.classList.contains('dark')).toBe(false)

    act(() => result.current.toggleTheme())
    act(() => result.current.toggleTheme())
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})
