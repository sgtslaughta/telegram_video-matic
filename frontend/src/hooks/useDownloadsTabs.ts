import { useSearchParams } from 'react-router-dom'

export const TABS = ['queue', 'wanted', 'history', 'review'] as const
export type DownloadsTab = (typeof TABS)[number]

/** Active tab + history kind filter, both kept in the URL. */
export function useDownloadsTabs() {
  const [params, setParams] = useSearchParams()
  const raw = params.get('tab')
  const tab: DownloadsTab = (TABS as readonly string[]).includes(raw ?? '') ? (raw as DownloadsTab) : 'queue'
  const kind = params.get('kind') ?? ''
  const update = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(params)
    for (const [k, v] of Object.entries(patch)) {
      if (v) next.set(k, v)
      else next.delete(k)
    }
    setParams(next, { replace: true })
  }
  return {
    tab,
    kind,
    setTab: (t: string) => update({ tab: t === 'queue' ? null : t }),
    setKind: (k: string) => update({ kind: k || null }),
  }
}
