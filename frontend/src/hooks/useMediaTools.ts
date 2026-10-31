import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchAPI } from '@/lib/api'
import { mediaKeys } from '@/hooks/useMedia'
import type { MediaItemRead } from '@/lib/types'

/** Media row as the API returns it today (types.ts lags behind). */
export type MediaFull = MediaItemRead & {
  content_date?: string | null
  keep?: boolean
  skip_reason?: string | null
  error?: string | null
}

export interface HistoryEntry { at: string; kind: string; message: string; level: string }

export function useMediaFull(id: number) {
  return useQuery({
    queryKey: mediaKeys.detail(id),
    queryFn: () => fetchAPI<MediaFull>(`/media/${id}`),
    enabled: id > 0,
  })
}

export function useMediaHistory(id: number) {
  return useQuery({
    queryKey: ['media', 'history', id],
    queryFn: () => fetchAPI<HistoryEntry[]>('/history', { params: { media_id: id } }),
    enabled: id > 0,
  })
}

export function useSetKeep(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (keep: boolean) =>
      fetchAPI<MediaFull>(`/media/${id}/keep`, { method: 'PATCH', body: JSON.stringify({ keep }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: mediaKeys.detail(id) }),
  })
}

const typing = (t: EventTarget | null) => {
  const el = t as HTMLElement | null
  return !!el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable)
}

/** j/k move, Enter opens, `/` focuses the search input. Rows carry data-nav="<index>". */
export function useListNav(count: number, onOpen: (index: number) => void) {
  const [active, setActive] = useState(-1)
  const searchRef = useRef<HTMLInputElement>(null)
  const openRef = useRef(onOpen)
  useEffect(() => { openRef.current = onOpen })

  const move = useCallback((d: number) => {
    setActive((i) => Math.max(0, Math.min(count - 1, i + d)))
  }, [count])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey || typing(e.target)) return
      if (e.key === '/') { e.preventDefault(); searchRef.current?.focus() }
      else if (e.key === 'j') move(1)
      else if (e.key === 'k') move(-1)
      else if (e.key === 'Enter' && active >= 0 && active < count && !(e.target as HTMLElement).closest?.('button,a,[role=button]')) {
        openRef.current(active)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [move, active, count])

  useEffect(() => {
    if (active >= 0) document.querySelector(`[data-nav="${active}"]`)?.scrollIntoView?.({ block: 'nearest' })
  }, [active])

  return { active, setActive, searchRef }
}
