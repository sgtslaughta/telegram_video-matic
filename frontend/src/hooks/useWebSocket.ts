import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { create } from 'zustand'
import { WebSocketConnection } from '@/lib/ws'
import type * as T from '@/lib/types'
import { downloadKeys } from './useDownloads'
import { tgKeys } from './useTgStatus'
import { mediaKeys } from './useMedia'
import { eventKeys } from './useEvents'
import { toast } from 'sonner'

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws`

interface WSStore {
  connected: boolean
  setConnected: (connected: boolean) => void
}

export const useWSStore = create<WSStore>((set) => ({
  connected: false,
  setConnected: (connected) => set({ connected }),
}))

let globalWS: WebSocketConnection | null = null
let wsConnectPromise: Promise<void> | null = null

function getOrCreateWS(): WebSocketConnection {
  if (!globalWS) {
    globalWS = new WebSocketConnection(WS_URL)
  }
  return globalWS
}

export function useWebSocket() {
  const qc = useQueryClient()
  const { setConnected } = useWSStore()
  const wsRef = useRef(getOrCreateWS())

  useEffect(() => {
    const ws = wsRef.current

    // Connect if not already connecting/connected
    if (!wsConnectPromise && !ws.isConnected()) {
      wsConnectPromise = ws.connect().catch((e) => {
        console.error('Initial WS connection failed:', e)
        wsConnectPromise = null
      })
    }

    // Listen for messages
    const unsubscribeMessage = ws.onMessage((msg) => {
      if (msg.kind === 'snapshot') {
        // Hydrate from snapshot on initial connection
        qc.setQueryData(downloadKeys.active(), msg.active_downloads)
        qc.setQueryData(tgKeys.status(), msg.tg_status)
      } else if (msg.kind === 'download_progress') {
        // Update active downloads list
        const current = qc.getQueryData<T.DownloadJob[]>(downloadKeys.active()) || []
        const patch = { progress: msg.progress, status: msg.status, bytes_done: msg.bytes_done, bytes_total: msg.bytes_total, speed_bps: msg.speed_bps, eta_sec: msg.eta_sec }
        const updated = current.map((j) =>
          j.media_id === msg.media_id ? { ...j, ...patch } : j
        )
        if (!updated.some((j) => j.media_id === msg.media_id)) {
          updated.push({ id: msg.job_id, media_id: msg.media_id, attempt: 1, error: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), ...patch } as any)
        }
        qc.setQueryData(downloadKeys.active(), updated)
      } else if (msg.kind === 'media_status') {
        // Update all media lists containing this media_id
        qc.invalidateQueries({ queryKey: mediaKeys.all })
      } else if (msg.kind === 'event') {
        // Prepend event and show toast
        const current = qc.getQueryData<T.PaginatedResponse<T.Event>>(eventKeys.filtered({}))
        if (current) {
          qc.setQueryData(eventKeys.filtered({}), {
            ...current,
            items: [msg.event, ...current.items],
            total: current.total + 1,
          })
        }
        toast[msg.event.level === 'error' ? 'error' : msg.event.level === 'success' ? 'success' : 'info'](msg.event.message)
      } else if (msg.kind === 'tg_status') {
        qc.setQueryData(tgKeys.status(), msg)
      }
    })

    // Listen for connection state
    const unsubscribeConnection = ws.onConnectionChange((connected) => {
      setConnected(connected)
    })

    return () => {
      unsubscribeMessage()
      unsubscribeConnection()
    }
  }, [qc, setConnected])

  return useWSStore((s) => s.connected)
}
