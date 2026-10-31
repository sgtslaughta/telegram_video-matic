import type { PulseCell } from '@/hooks/useOverview'

export type Span = { from: number; to: number; kind: 'down' | 'error' }

/** Merge consecutive hours that had outages or failed polls into shaded spans. */
export function outageSpans(cells: PulseCell[]): Span[] {
  const spans: Span[] = []
  cells.forEach((c, i) => {
    const kind = c.down ? 'down' : c.error ? 'error' : null
    if (!kind) return
    const last = spans[spans.length - 1]
    if (last && last.to === i - 1 && last.kind === kind) last.to = i
    else spans.push({ from: i, to: i, kind })
  })
  return spans
}
