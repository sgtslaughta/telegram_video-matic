import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, Play } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useSummary, markSeen, type Incident } from '@/hooks/useSummary'
import { absTime, formatBytes, relTime } from '@/lib/format'

function incidentText(i: Incident) {
  const span = i.hours >= 48 ? `${Math.round(i.hours / 24)} days` : `${i.hours} hour${i.hours === 1 ? '' : 's'}`
  return i.ended
    ? `Telegram was offline for about ${span}, from ${absTime(i.started)}. Sync recovered on its own.`
    : `Telegram has been offline for about ${span}. Sync resumes once it reconnects.`
}

/** "Since your last visit" — shown once when you return after 6h+ and something happened. */
export default function WelcomeSplash() {
  const { data } = useSummary()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!data) return
    if (data.show) setOpen(true)
    else void markSeen().catch(() => {})
  }, [data])

  const close = (o: boolean) => {
    setOpen(o)
    if (!o) void markSeen().catch(() => {})
  }
  if (!data?.show) return null
  const a = data.attention
  const needs = [
    a.failed > 0 && { to: '/downloads?tab=wanted', label: `${a.failed} failed download${a.failed === 1 ? '' : 's'}` },
    a.cleanup_paused && { to: '/storage', label: `Cleanup waiting for approval (${a.cleanup_paused.count} files)` },
    a.needs_review > 0 && { to: '/downloads?tab=review', label: `${a.needs_review} video${a.needs_review === 1 ? '' : 's'} to review` },
    a.wanted > 0 && { to: '/downloads?tab=wanted', label: `${a.wanted} played game${a.wanted === 1 ? '' : 's'} with no video yet` },
  ].filter(Boolean) as { to: string; label: string }[]

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="max-h-[85vh] gap-0 overflow-y-auto p-0 sm:max-w-2xl">
        <div className="border-b border-border px-6 py-5">
          <DialogTitle className="text-[20px] font-semibold tracking-tight">Since your last visit</DialogTitle>
          <DialogDescription className="mt-1 text-[13px]" title={absTime(data.since)}>
            {data.stats.downloaded
              ? `${data.stats.downloaded} new video${data.stats.downloaded === 1 ? '' : 's'}, ${formatBytes(data.stats.bytes)} added since ${relTime(data.since)}.`
              : `Here’s what happened since ${relTime(data.since)}.`}
          </DialogDescription>
        </div>

        {data.incidents.length > 0 && (
          <div className="space-y-2 border-b border-border bg-err/5 px-6 py-4">
            {data.incidents.map((i) => (
              <p key={i.started} className="flex gap-2.5 text-[13px]">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-err" />
                {incidentText(i)}
              </p>
            ))}
          </div>
        )}

        {data.arrivals.map((g) => (
          <section key={g.group} className="border-b border-border px-6 py-4">
            <h3 className="mb-3 text-[13px] font-semibold">{g.group}</h3>
            <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {g.items.slice(0, 6).map((it) => (
                <li key={it.id}>
                  <Link to={`/media/${it.id}`} onClick={() => close(false)} className="group block">
                    <div className="relative flex aspect-video items-center justify-center overflow-hidden rounded-md bg-muted">
                      {it.has_thumb && <img src={`/api/media/${it.id}/thumb`} alt="" className="h-full w-full object-cover" />}
                      <span className="absolute flex h-8 w-8 items-center justify-center rounded-full bg-brand text-primary-foreground opacity-90 transition-transform group-hover:scale-105">
                        <Play className="ml-0.5 h-4 w-4" fill="currentColor" />
                      </span>
                    </div>
                    <p className="mt-1.5 truncate text-[12px] font-medium">{it.title}</p>
                  </Link>
                </li>
              ))}
            </ul>
            {g.items.length > 6 && <p className="mt-2 text-[12px] text-muted-foreground">and {g.items.length - 6} more</p>}
          </section>
        ))}

        {needs.length > 0 && (
          <section className="border-b border-border px-6 py-4">
            <h3 className="mb-2 text-[13px] font-semibold">Needs attention</h3>
            <ul className="space-y-1">
              {needs.map((n) => (
                <li key={n.label}>
                  <Link to={n.to} onClick={() => close(false)} className="text-[13px] text-brand hover:underline">{n.label}</Link>
                </li>
              ))}
            </ul>
          </section>
        )}

        <div className="flex justify-end px-6 py-4">
          <Button onClick={() => close(false)}>Done</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
