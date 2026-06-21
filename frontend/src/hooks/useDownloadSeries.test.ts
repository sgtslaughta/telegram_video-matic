import { describe, it, expect } from 'vitest'
import { bucketBySubByDay, bucketByDay } from './useDownloadSeries'

const NOW = new Date('2026-06-20T12:00:00Z')

describe('bucketBySubByDay', () => {
  it('groups downloads by subscription into per-day rows', () => {
    const items = [
      { downloaded_at: '2026-06-20T01:00:00Z', subscription_id: 1 },
      { downloaded_at: '2026-06-20T02:00:00Z', subscription_id: 1 },
      { downloaded_at: '2026-06-20T03:00:00Z', subscription_id: 2 },
      { downloaded_at: '2026-06-20T04:00:00Z', subscription_id: null }, // ad-hoc
    ]
    const { rows, series } = bucketBySubByDay(items, 3, NOW, (id) =>
      id == null ? 'Ad-hoc' : `Sub ${id}`)
    // 3 distinct series: s1, s2, adhoc
    expect(series.map((s) => s.key).sort()).toEqual(['adhoc', 's1', 's2'])
    expect(series.find((s) => s.key === 'adhoc')!.name).toBe('Ad-hoc')
    const today = rows[rows.length - 1]
    expect(today.s1).toBe(2)
    expect(today.s2).toBe(1)
    expect(today.adhoc).toBe(1)
    // each series has a distinct colour
    expect(new Set(series.map((s) => s.color)).size).toBe(3)
  })

  it('bucketByDay total still works (back-compat)', () => {
    const items = [
      { downloaded_at: '2026-06-20T01:00:00Z' },
      { downloaded_at: '2026-06-20T02:00:00Z' },
    ]
    const out = bucketByDay(items, 2, NOW)
    expect(out[out.length - 1].count).toBe(2)
  })
})
