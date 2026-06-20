import { describe, it, expect } from 'vitest'
import { bucketByDay } from '@/hooks/useDownloadSeries'

describe('bucketByDay', () => {
  const now = new Date('2026-06-20T12:00:00Z')

  it('returns `days` buckets oldest->newest, zero-filled', () => {
    const out = bucketByDay([], 3, now)
    expect(out.map((d) => d.day)).toEqual(['2026-06-18', '2026-06-19', '2026-06-20'])
    expect(out.every((d) => d.count === 0)).toBe(true)
  })

  it('counts items on their downloaded_at day and ignores out-of-window/null', () => {
    const out = bucketByDay(
      [
        { downloaded_at: '2026-06-20T01:00:00Z' },
        { downloaded_at: '2026-06-20T23:00:00Z' },
        { downloaded_at: '2026-06-19T05:00:00Z' },
        { downloaded_at: '2026-06-01T05:00:00Z' }, // out of window
        { downloaded_at: null },
      ],
      3,
      now
    )
    expect(out.find((d) => d.day === '2026-06-20')!.count).toBe(2)
    expect(out.find((d) => d.day === '2026-06-19')!.count).toBe(1)
    expect(out.find((d) => d.day === '2026-06-18')!.count).toBe(0)
  })
})
