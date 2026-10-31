import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Activity from './Activity'
import * as feed from '@/components/activity/useEventsFeed'
import type { FeedEvent } from '@/components/activity/useEventsFeed'

const ev = (o: Partial<FeedEvent>): FeedEvent => ({
  id: 1, level: 'info', kind: 'download', message: 'Event', created_at: '2026-06-20T10:00:00Z', ...o,
})

function mockFeed(events: FeedEvent[], extra: Record<string, unknown> = {}) {
  const spy = vi.spyOn(feed, 'useEventsFeed').mockReturnValue({
    data: { pages: [events] }, isLoading: false, hasNextPage: false, isFetchingNextPage: false,
    fetchNextPage: vi.fn(), ...extra,
  } as unknown as ReturnType<typeof feed.useEventsFeed>)
  return spy
}
const renderPage = (url = '/activity') => render(<MemoryRouter initialEntries={[url]}><Activity /></MemoryRouter>)

describe('Activity', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('renders events with a repeat pill only when count > 1', () => {
    mockFeed([ev({ id: 1, message: 'Download completed', level: 'success' }), ev({ id: 2, message: 'Poll failed', level: 'error', count: 42 })])
    renderPage()
    expect(screen.getByText('Download completed')).toBeTruthy()
    expect(screen.getByText('×42').getAttribute('title')).toMatch(/^Repeated 42 times, last /)
    expect(screen.queryByText('×1')).toBeNull()
  })

  it('shows a skeleton while loading and an empty state when nothing matches', () => {
    mockFeed([], { data: undefined, isLoading: true })
    const { container, unmount } = renderPage()
    expect(container.querySelector('[aria-busy="true"]')).toBeTruthy()
    unmount()
    mockFeed([])
    renderPage()
    expect(screen.getByText('No events')).toBeTruthy()
  })

  it('reads level from the URL and passes it to the feed', () => {
    const spy = mockFeed([])
    renderPage('/activity?level=error&kind=job')
    expect(spy).toHaveBeenCalledWith({ level: 'error', kind: 'job' })
    expect(screen.getByRole('button', { name: 'Errors' }).getAttribute('aria-pressed')).toBe('true')
  })

  it('filters loaded events by search text and focuses search on "/"', () => {
    mockFeed([ev({ id: 1, message: 'Alpha synced' }), ev({ id: 2, message: 'Beta failed' })])
    renderPage()
    fireEvent.keyDown(window, { key: '/' })
    const input = screen.getByLabelText('Search events')
    expect(document.activeElement).toBe(input)
    fireEvent.change(input, { target: { value: 'beta' } })
    expect(screen.queryByText('Alpha synced')).toBeNull()
    expect(screen.getByText('Beta failed')).toBeTruthy()
  })

  it('offers Load more when another page exists', () => {
    const fetchNextPage = vi.fn()
    mockFeed([ev({})], { hasNextPage: true, fetchNextPage })
    renderPage()
    fireEvent.click(screen.getByText('Load more'))
    expect(fetchNextPage).toHaveBeenCalled()
  })
})
