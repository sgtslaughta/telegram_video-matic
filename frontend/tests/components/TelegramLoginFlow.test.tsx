import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TelegramLoginFlow from '@/components/telegram/TelegramLoginFlow'
import * as api from '@/lib/api'

vi.mock('@/lib/api')
const wrap = (qc: QueryClient, ui: React.ReactNode) => (
  <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
)

describe('TelegramLoginFlow', () => {
  let qc: QueryClient
  beforeEach(() => {
    qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    vi.clearAllMocks()
  })

  it('shows the credentials step when not configured', async () => {
    vi.mocked(api.tg.status).mockResolvedValue({ status: 'disconnected', configured: false } as any)
    render(wrap(qc, <TelegramLoginFlow />))
    expect(await screen.findByText(/Telegram API credentials/i)).toBeTruthy()
  })

  it('shows the phone step when configured but disconnected', async () => {
    vi.mocked(api.tg.status).mockResolvedValue({ status: 'disconnected', configured: true } as any)
    render(wrap(qc, <TelegramLoginFlow />))
    expect(await screen.findByText(/Enter phone number/i)).toBeTruthy()
  })

  it('calls onConnected when status is connected', async () => {
    vi.mocked(api.tg.status).mockResolvedValue({ status: 'connected', configured: true, username: 'bob' } as any)
    const onConnected = vi.fn()
    render(wrap(qc, <TelegramLoginFlow onConnected={onConnected} />))
    await screen.findByText(/Connected/i)
    expect(onConnected).toHaveBeenCalled()
  })
})
