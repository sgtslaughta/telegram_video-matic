import { useState, useMemo } from 'react'

export interface SubscriptionEditorState {
  channelId: number | null
  topicId: number | null
  name: string
  filterMode: 'include' | 'exclude'
  filterRegex: string
  regexError: string | null
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
}

export function useSubscriptionEditor(initialState?: Partial<SubscriptionEditorState>) {
  const [state, setState] = useState<SubscriptionEditorState>({
    channelId: null,
    topicId: null,
    name: '',
    filterMode: 'include',
    filterRegex: '',
    regexError: null,
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
    ...initialState,
  })

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

  const update = (key: keyof SubscriptionEditorState, value: any) => {
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

  return {
    state,
    update,
    toggleScheduleDay,
    regexValid: regexStatus?.valid ?? true,
    regexError: regexStatus?.error,
  }
}
