import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TelegramLoginDialog from '@/components/telegram/TelegramLoginDialog'
import * as api from '@/lib/api'

vi.mock('@/lib/api')
const wrap = (qc: QueryClient, ui: React.ReactNode) => (
  <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
)

describe('TelegramLoginDialog', () => {
  let qc: QueryClient
  beforeEach(() => {
    qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    vi.clearAllMocks()
    vi.mocked(api.tg.status).mockResolvedValue({ status: 'disconnected', configured: true } as any)
  })

  it('renders the login flow when open', async () => {
    render(wrap(qc, <TelegramLoginDialog open={true} onOpenChange={() => {}} />))
    expect(await screen.findByText(/Connect Telegram/i)).toBeInTheDocument()
    expect(await screen.findByText(/Enter phone number/i)).toBeInTheDocument()
  })

  it('renders nothing visible when closed', () => {
    render(wrap(qc, <TelegramLoginDialog open={false} onOpenChange={() => {}} />))
    expect(screen.queryByText(/Enter phone number/i)).not.toBeInTheDocument()
  })
})
