import { forwardRef } from 'react'
import { MoreHorizontal } from 'lucide-react'
import { Sparkline } from '@/components/shared/Sparkline'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Switch } from '@/components/ui/switch'
import { useUpdateSubscription } from '@/hooks/useSubscriptions'
import type { OverviewSub } from '@/hooks/useOverview'
import { absTime, formatBytes, relTime } from '@/lib/format'
import { withToast } from '@/lib/toast'
import type { SubscriptionRead } from '@/lib/types'
import { filterSummary } from './summary'

/** Optional fields the API may add; absent on older backends. */
export type ListSub = SubscriptionRead & { downloaded_count?: number; downloaded_bytes?: number }

const FREQ: Record<string, string> = {
  realtime: 'Real-time', '1m': 'Every minute', '5m': 'Every 5 min', '15m': 'Every 15 min',
  '30m': 'Every 30 min', hourly: 'Hourly', daily: 'Daily', scheduled: 'Weekdays',
}

interface Props {
  sub: ListSub
  title: string
  detail: string
  pulse?: OverviewSub
  focused: boolean
  onOpen: () => void
  onFocus: () => void
  onDelete: () => void
  onScan: () => void
}

export const SubscriptionRow = forwardRef<HTMLTableRowElement, Props>(function SubscriptionRow(
  { sub, title, detail, pulse, focused, onOpen, onFocus, onDelete, onScan }, ref,
) {
  const update = useUpdateSubscription(sub.id)
  const toggle = (enabled: boolean) =>
    withToast(() => update.mutateAsync({ enabled }), {
      success: `${enabled ? 'Enabled' : 'Paused'} ${title}`,
      undo: () => update.mutateAsync({ enabled: !enabled }),
    })
  const stop = (e: React.SyntheticEvent) => e.stopPropagation()
  const checked = pulse?.last_checked_at ?? null

  return (
    <tr ref={ref} tabIndex={focused ? 0 : -1} data-sub-id={sub.id} onClick={onOpen} onFocus={onFocus}
      onKeyDown={(e) => { if (e.key === 'Enter' && e.target === e.currentTarget) onOpen() }}
      className="h-12 cursor-pointer border-b border-border outline-none transition-colors last:border-0 hover:bg-accent/60 focus-visible:bg-accent/60 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-brand">
      <td className="max-w-[260px] pl-4 pr-3">
        <div className="flex items-center gap-2.5">
          <span role="img" aria-label={sub.enabled ? 'Enabled' : 'Paused'}
            className={`h-2 w-2 shrink-0 rounded-full ${sub.enabled ? 'bg-ok' : 'bg-muted-foreground/40'}`} />
          <div className="min-w-0">
            <p className="truncate font-medium">{title}</p>
            {detail && <p className="truncate text-[12px] text-muted-foreground">{detail}</p>}
          </div>
        </div>
      </td>
      <td className="hidden whitespace-nowrap px-3 text-muted-foreground md:table-cell">{FREQ[sub.check_frequency ?? ''] ?? sub.check_frequency ?? ''}</td>
      <td className="hidden max-w-[200px] truncate px-3 text-muted-foreground lg:table-cell" title={sub.filter_regex ?? undefined}>{filterSummary(sub)}</td>
      <td className="hidden whitespace-nowrap px-3 text-right tabular-nums text-muted-foreground lg:table-cell">
        {sub.downloaded_count != null ? `${sub.downloaded_count} video${sub.downloaded_count === 1 ? '' : 's'}, ${formatBytes(sub.downloaded_bytes)}` : ''}
      </td>
      <td className="hidden whitespace-nowrap px-3 text-right text-[12px] text-muted-foreground md:table-cell" title={absTime(checked)}>
        {sub.enabled ? relTime(checked) : ''}
      </td>
      <td className="hidden w-32 px-3 xl:table-cell">
        {pulse && <Sparkline data={pulse.pulse} dataKey="queued" label="New videos" className="h-7" />}
      </td>
      <td className="px-3" onClick={stop}>
        <Switch checked={sub.enabled} onCheckedChange={toggle} aria-label={`${sub.enabled ? 'Pause' : 'Enable'} ${title}`} />
      </td>
      <td className="w-10 pr-3" onClick={stop} onKeyDown={stop}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8" aria-label={`Actions for ${title}`}><MoreHorizontal className="h-4 w-4" /></Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={onOpen}>Edit</DropdownMenuItem>
            <DropdownMenuItem onSelect={onScan}>Scan now</DropdownMenuItem>
            <DropdownMenuItem onSelect={onDelete} className="text-err">Delete</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </td>
    </tr>
  )
})
