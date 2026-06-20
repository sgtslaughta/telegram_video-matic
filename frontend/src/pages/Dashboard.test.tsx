import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter as Router } from 'react-router-dom'
import Dashboard from './Dashboard'
import * as api from '@/lib/api'

vi.mock('@/lib/api', () => ({
  subscriptions: {
    list: vi.fn(() => Promise.resolve([])),
  },
  media: {
    list: vi.fn(() => Promise.resolve([])),
  },
  events: {
    list: vi.fn(() => Promise.resolve([])),
  },
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <Router>
        {children}
      </Router>
    </QueryClientProvider>
  )
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard heading and stat labels', () => {
    render(<Dashboard />, { wrapper: createWrapper() })

    expect(screen.getByText('Dashboard')).toBeTruthy()
    expect(screen.getByText('Active subscriptions')).toBeTruthy()
    expect(screen.getByText('Downloaded')).toBeTruthy()
    expect(screen.getByText('Storage used')).toBeTruthy()
    expect(screen.getByText('Failed')).toBeTruthy()
  })
})
