import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as api from '@/lib/api'
import { RugbyJobDialog } from './RugbyJobDialog'

describe('RugbyJobDialog', () => {
  it('previews with a dry run, applies only on click', async () => {
    let lastDry = true
    const runJob = vi.spyOn(api.rugby, 'runJob').mockImplementation(async (_j, dryRun) => {
      lastDry = dryRun
      return { scheduled: true }
    })
    vi.spyOn(api.rugby, 'report').mockImplementation(async () => ({
      running: false, dry_run: lastDry, total: 1, moved: 1, conflicts: [],
      plan: [{ media_id: 1, from: '/media/RTL Patreon/a.mp4',
               to: '/media/Gallagher Premiership/Season 2026/a.mp4' }],
    }))
    const qc = new QueryClient()
    render(
      <QueryClientProvider client={qc}>
        <RugbyJobDialog job="reconcile" onClose={() => {}} />
      </QueryClientProvider>,
    )

    expect(await screen.findByText(/Season 2026\/a.mp4/)).toBeInTheDocument()
    expect(runJob).toHaveBeenCalledTimes(1)
    expect(runJob).toHaveBeenLastCalledWith('reconcile', true)

    await userEvent.click(screen.getByRole('button', { name: 'Move files' }))
    await waitFor(() => expect(runJob).toHaveBeenLastCalledWith('reconcile', false))
    expect(await screen.findByRole('button', { name: 'Done' })).toBeInTheDocument()
  })
})
