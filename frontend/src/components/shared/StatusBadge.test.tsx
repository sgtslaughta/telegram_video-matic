import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from './StatusBadge'
import { MediaStatus, AccountStatus, JobStatus } from '@/lib/types'

describe('StatusBadge', () => {
  it('renders green badge for ready status', () => {
    render(<StatusBadge status={MediaStatus.READY} />)
    const badge = screen.getByText('Ready')
    expect(badge.className).toContain('bg-green-100')
    expect(badge.className).toContain('text-green-800')
  })

  it('renders amber badge for downloading status', () => {
    render(<StatusBadge status={MediaStatus.DOWNLOADING} />)
    const badge = screen.getByText('Downloading')
    expect(badge.className).toContain('bg-amber-100')
    expect(badge.className).toContain('text-amber-800')
  })

  it('renders red badge for failed status', () => {
    render(<StatusBadge status={MediaStatus.FAILED} />)
    const badge = screen.getByText('Failed')
    expect(badge.className).toContain('bg-red-100')
    expect(badge.className).toContain('text-red-800')
  })

  it('renders gray badge for disconnected account status', () => {
    render(<StatusBadge status={AccountStatus.DISCONNECTED} />)
    const badge = screen.getByText('Disconnected')
    expect(badge.className).toContain('bg-gray-100')
    expect(badge.className).toContain('text-gray-800')
  })

  it('renders green badge for connected account status', () => {
    render(<StatusBadge status={AccountStatus.CONNECTED} />)
    const badge = screen.getByText('Connected')
    expect(badge.className).toContain('bg-green-100')
    expect(badge.className).toContain('text-green-800')
  })

  it('renders amber badge for job pending status', () => {
    render(<StatusBadge status={JobStatus.PENDING} />)
    const badge = screen.getByText('Pending')
    expect(badge.className).toContain('bg-amber-100')
    expect(badge.className).toContain('text-amber-800')
  })
})
