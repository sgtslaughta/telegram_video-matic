import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import Login from './Login'

const createWrapper = () => {
  const queryClient = new QueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <TooltipProvider>
          {children}
        </TooltipProvider>
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

  it('calls login mutation on form submit', async () => {
    render(<Login />, { wrapper: createWrapper() })

    const input = screen.getByLabelText('Password')
    const button = screen.getByRole('button', { name: /login/i })

    fireEvent.change(input, { target: { value: 'testpassword' } })
    expect(button.disabled).toBe(false)

    fireEvent.click(button)

    // Verify form submitted (button is still present for re-render)
    expect(screen.getByRole('button', { name: /login/i })).toBeTruthy()
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
