import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import Login from './Login'

const createWrapper = () => {
  const queryClient = new QueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders password input and submit button', () => {
    render(<Login />, { wrapper: createWrapper() })

    expect(screen.getByLabelText('Password')).toBeTruthy()
    expect(screen.getByRole('button', { name: /login/i })).toBeTruthy()
  })

  it('displays error message on failed login', async () => {
    const originalFetch = global.fetch
    global.fetch = vi.fn().mockRejectedValueOnce(new Error('Invalid password'))

    render(<Login />, { wrapper: createWrapper() })

    const input = screen.getByLabelText('Password')
    const button = screen.getByRole('button', { name: /login/i })

    fireEvent.change(input, { target: { value: 'wrongpassword' } })
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/invalid password/i)).toBeTruthy()
    })

    global.fetch = originalFetch
  })

  it('disables button when password is empty', () => {
    render(<Login />, { wrapper: createWrapper() })

    const button = screen.getByRole('button', { name: /login/i }) as HTMLButtonElement
    expect(button.disabled).toBe(true)
  })

  it('enables button when password has value', () => {
    render(<Login />, { wrapper: createWrapper() })

    const input = screen.getByLabelText('Password')
    const button = screen.getByRole('button', { name: /login/i }) as HTMLButtonElement

    fireEvent.change(input, { target: { value: 'password123' } })
    expect(button.disabled).toBe(false)
  })
})
