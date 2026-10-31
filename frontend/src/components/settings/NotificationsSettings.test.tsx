import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NotificationsSettings } from './NotificationsSettings'

afterEach(() => vi.unstubAllGlobals())

describe('NotificationsSettings', () => {
  it('renders a target name and masked url', async () => {
    const body = {
      triggers: ['download_complete', 'download_failed'],
      targets: [{ id: 'a1', name: 'Family Discord', url_masked: 'discord://****', triggers: ['download_complete'] }],
      options: { quiet: { enabled: false, start: 22, end: 7 }, disk_low_pct: 90, public_url: '' },
      jellyfin: { url: '', library_id: '', api_key_set: false },
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, text: async () => JSON.stringify(body),
    }))
    render(
      <QueryClientProvider client={new QueryClient()}>
        <NotificationsSettings />
      </QueryClientProvider>
    )
    expect(await screen.findByText('Family Discord')).toBeInTheDocument()
    expect(screen.getByText('discord://****')).toBeInTheDocument()
  })
})
