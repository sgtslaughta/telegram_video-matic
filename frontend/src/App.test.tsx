import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
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

  it('renders the app title', () => {
    render(<App />)
    expect(screen.getByText('Video-Matic')).toBeTruthy()
  })

  it('renders router', () => {
    render(<App />)
    // The router should render the dashboard by default
    expect(screen.getByRole('navigation')).toBeTruthy()
  })
})
