import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchAPI } from '@/lib/api'

export interface StorageItem {
  id: number
  file_name: string
  reason: 'age' | 'quota' | 'disk'
  size_bytes: number
  content_date: string | null
}
export interface StorageFolder { path: string; count: number; bytes: number }
export interface UntrackedFile { path: string; size_bytes: number; modified: string }
export interface Storage {
  media_root: string
  disk: { used: number; total: number; pct: number }
  folders: StorageFolder[]
  preview: { days: number; count: number; bytes: number; items: StorageItem[] }
  paused: { count: number; gb: number } | null
  untracked: { count: number; bytes: number; items: UntrackedFile[] }
}

const KEY = ['storage'] as const

export function useStorage() {
  return useQuery({ queryKey: KEY, queryFn: () => fetchAPI<Storage>('/storage'), refetchInterval: 60000 })
}

export function usePruneConfirm() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => fetchAPI<{ pruned: number; paused: unknown }>('/storage/prune/confirm', { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

export function useDeleteUntracked() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (path: string) =>
      fetchAPI<unknown>('/storage/untracked', { method: 'DELETE', body: JSON.stringify({ path }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}
