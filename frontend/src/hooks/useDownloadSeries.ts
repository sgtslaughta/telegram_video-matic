import { useQuery } from '@tanstack/react-query'
import * as api from '@/lib/api'
import { MediaStatus } from '@/lib/types'

const toDay = (d: Date) => d.toISOString().slice(0, 10) // YYYY-MM-DD (UTC)

export function bucketByDay(
  items: { downloaded_at?: string | null }[],
  days: number,
  now: Date
): { day: string; count: number }[] {
  const buckets: { day: string; count: number }[] = []
  const index = new Map<string, number>()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setUTCDate(d.getUTCDate() - i)
    const key = toDay(d)
    index.set(key, buckets.length)
    buckets.push({ day: key, count: 0 })
  }
  for (const it of items) {
    if (!it.downloaded_at) continue
    const key = toDay(new Date(it.downloaded_at))
    const pos = index.get(key)
    if (pos !== undefined) buckets[pos].count++
  }
  return buckets
}

export function useDownloadSeries(days = 14) {
  const q = useQuery({
    queryKey: ['media', 'list', { status: MediaStatus.DOWNLOADED }],
    queryFn: () => api.media.list({ status: MediaStatus.DOWNLOADED }),
  })
  return { data: bucketByDay(q.data ?? [], days, new Date()), isLoading: q.isLoading }
}
