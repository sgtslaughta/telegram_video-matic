import { useState, useMemo } from 'react'

const DEFAULTS: SubscriptionEditorState = {
  channelId: null,
  topicId: null,
  name: '',
  filterMode: 'include',
  filterRegex: '',
  regexError: null,
  checkFrequency: '5m',
  scheduleDays: [],
  minSizeMb: null,
  maxSizeMb: null,
  maxTotalGb: null,
  dateFrom: '',
  dateTo: '',
  ongoing: true,
  storagePath: '',
  renameTemplate: '{channel}/{title}.{ext}',
  retentionDays: null,
  seasonDetection: false,
  jellyfinMetadata: false,
  keep: false,
}

export interface SubscriptionEditorState {
  channelId: number | null
  topicId: number | null
  name: string
  filterMode: 'include' | 'exclude'
  filterRegex: string
  regexError: string | null
  checkFrequency: string  // realtime | 1m | 5m | 15m | 30m | hourly | daily | scheduled
  scheduleDays: string[]
  minSizeMb: number | null
  maxSizeMb: number | null
  maxTotalGb: number | null   // disk quota; null = unlimited
  dateFrom: string  // yyyy-mm-dd; empty = no lower bound
  dateTo: string    // yyyy-mm-dd; empty = ongoing (no upper bound)
  ongoing: boolean  // UI: capture future indefinitely (no end date)
  storagePath: string
  renameTemplate: string
  retentionDays: number | null
  seasonDetection: boolean
  jellyfinMetadata: boolean
  keep: boolean  // never auto-delete (overrides retention)
}

export function useSubscriptionEditor(
  initialState?: Partial<SubscriptionEditorState>,
  resetKey?: string | number,
) {
  const [state, setState] = useState<SubscriptionEditorState>({ ...DEFAULTS, ...initialState })
  const [base, setBase] = useState<SubscriptionEditorState>(state)

  // The edit form mounts before the query resolves, so the first init uses
  // defaults. Re-seed from initialState once the loaded sub (resetKey) changes.
  const [seenKey, setSeenKey] = useState(resetKey)
  if (seenKey !== resetKey) {
    setSeenKey(resetKey)
    if (initialState) {
      const seeded = { ...DEFAULTS, ...initialState }
      setState(seeded)
      setBase(seeded)
    }
  }

  // Live regex validation
  const regexStatus = useMemo(() => {
    if (!state.filterRegex) return null
    try {
      new RegExp(state.filterRegex)
      return { valid: true, error: null }
    } catch (e) {
      return { valid: false, error: (e as Error).message }
    }
  }, [state.filterRegex])

  const update = <K extends keyof SubscriptionEditorState>(key: K, value: SubscriptionEditorState[K]) => {
    setState((prev) => ({ ...prev, [key]: value }))
  }

  const toggleScheduleDay = (day: string) => {
    setState((prev) => ({
      ...prev,
      scheduleDays: prev.scheduleDays.includes(day)
        ? prev.scheduleDays.filter((d) => d !== day)
        : [...prev.scheduleDays, day],
    }))
  }

  const dirty = useMemo(() => JSON.stringify(state) !== JSON.stringify(base), [state, base])

  return {
    state,
    dirty,
    discard: () => setState(base),
    markSaved: () => setBase(state),
    update,
    toggleScheduleDay,
    regexValid: regexStatus?.valid ?? true,
    regexError: regexStatus?.error,
  }
}
