import { clsx } from 'clsx'

type Tone = 'ok' | 'warn' | 'err' | 'muted'

// Status → tone + human label. Colour is reserved for status (see DESIGN.md).
const STATUS: Record<string, [Tone, string]> = {
  ready: ['ok', 'Ready'], downloaded: ['ok', 'Downloaded'], completed: ['ok', 'Completed'], done: ['ok', 'Done'],
  connected: ['ok', 'Connected'],
  pending: ['warn', 'Pending'], queued: ['warn', 'Queued'], downloading: ['warn', 'Downloading'],
  running: ['warn', 'Downloading'], processing: ['warn', 'Processing'], paused: ['muted', 'Paused'],
  waiting_phone: ['warn', 'Waiting for phone'], waiting_code: ['warn', 'Waiting for code'],
  waiting_password: ['warn', 'Waiting for password'], awaiting_code: ['warn', 'Waiting for code'],
  awaiting_password: ['warn', 'Waiting for password'],
  failed: ['err', 'Failed'], error: ['err', 'Failed'],
  skipped: ['muted', 'Skipped'], pruned: ['muted', 'Deleted'], disconnected: ['muted', 'Disconnected'],
  canceled: ['muted', 'Canceled'],
}

const TONE: Record<Tone, string> = {
  ok: 'bg-ok/12 text-ok', warn: 'bg-warn/12 text-warn', err: 'bg-err/12 text-err', muted: 'bg-muted text-muted-foreground',
}
const DOT: Record<Tone, string> = { ok: 'bg-ok', warn: 'bg-warn', err: 'bg-err', muted: 'bg-muted-foreground/60' }

export function StatusBadge({ status }: { status: string }) {
  const [tone, label] = STATUS[status] ?? ['muted', status]
  return (
    <span data-tone={tone} className={clsx('inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[12px] font-medium', TONE[tone])}>
      <span className={clsx('h-1.5 w-1.5 rounded-full', DOT[tone])} />
      {label}
    </span>
  )
}
