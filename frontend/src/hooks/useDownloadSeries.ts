import { useQuery } from '@tanstack/react-query'
import * as api from '@/lib/api'
import { MediaStatus } from '@/lib/types'
import { useSubscriptions } from '@/hooks/useSubscriptions'

const toDay = (d: Date) => d.toISOString().slice(0, 10) // YYYY-MM-DD (UTC)

// Distinct colors for per-subscription series (cycled if more subs than colors).
const COLORS = [
  '#229ed9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
]

export interface SeriesMeta { key: string; name: string; color: string }

type MediaRow = { downloaded_at?: string | null; subscription_id?: number | null }

// Build per-day rows keyed by subscription series, plus a total, for stacking.
export function bucketBySubByDay(
  items: MediaRow[],
  days: number,
  now: Date,
  nameFor: (id: number | null | undefined) => string,
): { rows: Record<string, number | string>[]; series: SeriesMeta[] } {
  const keyFor = (id: number | null | undefined) => (id == null ? 'adhoc' : `s${id}`)

  // Discover which series actually have downloads (stable order by first seen).
  const seenKeys: string[] = []
  const keyName = new Map<string, string>()
  for (const it of items) {
    if (!it.downloaded_at) continue
    const k = keyFor(it.subscription_id)
    if (!keyName.has(k)) { keyName.set(k, nameFor(it.subscription_id)); seenKeys.push(k) }
  }
  const series: SeriesMeta[] = seenKeys.map((k, i) => ({
    key: k, name: keyName.get(k) || k, color: COLORS[i % COLORS.length],
  }))

  const rows: Record<string, number | string>[] = []
  const index = new Map<string, number>()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setUTCDate(d.getUTCDate() - i)
    const key = toDay(d)
    index.set(key, rows.length)
    const row: Record<string, number | string> = { day: key }
    for (const s of series) row[s.key] = 0
    rows.push(row)
  }
  for (const it of items) {
    if (!it.downloaded_at) continue
    const pos = index.get(toDay(new Date(it.downloaded_at)))
    if (pos === undefined) continue
    const k = keyFor(it.subscription_id)
    rows[pos][k] = ((rows[pos][k] as number) || 0) + 1
  }
  return { rows, series }
}

// Back-compat: flat per-day total (used by any caller wanting just counts).
export function bucketByDay(
  items: { downloaded_at?: string | null }[],
  days: number,
  now: Date,
): { day: string; count: number }[] {
  const { rows } = bucketBySubByDay(items as MediaRow[], days, now, () => 'x')
  return rows.map((r) => ({
    day: r.day as string,
    count: Object.entries(r).reduce((t, [k, v]) => (k === 'day' ? t : t + (v as number)), 0),
  }))
}

export function useDownloadSeries(days = 14) {
  const q = useQuery({
    queryKey: ['media', 'list', { status: MediaStatus.DOWNLOADED }],
    queryFn: () => api.media.list({ status: MediaStatus.DOWNLOADED }),
  })
  const subs = useSubscriptions()
  const nameFor = (id: number | null | undefined) => {
    if (id == null) return 'Ad-hoc'
    const s = subs.data?.find((x) => x.id === id)
    return s?.name || s?.channel_title || `Subscription ${id}`
  }
  const { rows, series } = bucketBySubByDay(q.data ?? [], days, new Date(), nameFor)
  return { data: rows, series, isLoading: q.isLoading }
}
