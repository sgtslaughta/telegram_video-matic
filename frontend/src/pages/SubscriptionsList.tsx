import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Search } from 'lucide-react'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { Page, PageHeader } from '@/components/shared/PageHeader'
import { SubscriptionRow, type ListSub } from '@/components/subscriptions/SubscriptionRow'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useChannels } from '@/hooks/useChannels'
import { useOverview } from '@/hooks/useOverview'
import { useDeleteSubscription, useScanSubscription, useSubscriptions } from '@/hooks/useSubscriptions'
import { withToast } from '@/lib/toast'

const isTyping = (t: EventTarget | null) =>
  t instanceof HTMLElement && (t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName) || t.getAttribute('role') === 'switch')

function DeleteConfirm({ id, onDone }: { id: number | null; onDone: () => void }) {
  const del = useDeleteSubscription(id ?? 0)
  return (
    <ConfirmDialog isOpen={id !== null} title="Delete subscription" confirmText="Delete" cancelText="Cancel"
      description="The subscription stops syncing. Files already downloaded are kept."
      onCancel={onDone}
      onConfirm={async () => { await withToast(() => del.mutateAsync(), { success: 'Subscription deleted' }); onDone() }} />
  )
}

function ScanRunner({ id, onDone }: { id: number; onDone: () => void }) {
  const scan = useScanSubscription(id)
  const ran = useRef(false)
  useEffect(() => {
    if (ran.current) return
    ran.current = true
    void withToast(() => scan.mutateAsync(), { success: 'Scan started' }).then(onDone)
  }, [scan, onDone])
  return null
}

export default function SubscriptionsList() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [active, setActive] = useState(0)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [scanId, setScanId] = useState<number | null>(null)
  const rows = useRef<(HTMLTableRowElement | null)[]>([])
  const { data: subs = [], isLoading } = useSubscriptions()
  const { data: channels } = useChannels()
  const { data: overview } = useOverview(24)

  const chanTitle = (id: number) => channels?.find((c) => c.id === id)?.title ?? `Channel ${id}`
  const q = search.toLowerCase()
  const visible = (subs as ListSub[]).filter((s) =>
    !q || [s.name, s.channel_title, s.topic_title, chanTitle(s.channel_id)].some((v) => v?.toLowerCase().includes(q)))

  const move = useCallback((to: number) => {
    const i = Math.max(0, Math.min(to, visible.length - 1))
    setActive(i)
    rows.current[i]?.focus()
  }, [visible.length])

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey || isTyping(e.target) || !visible.length) return
      if (e.key === 'j') move(active + 1)
      else if (e.key === 'k') move(active - 1)
      else if (e.key === 'e') navigate(`/subscriptions/${visible[Math.min(active, visible.length - 1)].id}`)
    }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [active, move, navigate, visible])

  return (
    <Page wide>
      <PageHeader title="Subscriptions"
        description={subs.length ? `${subs.filter((s) => s.enabled).length} of ${subs.length} active` : undefined}
        actions={<Button onClick={() => navigate('/subscriptions/new')}><Plus className="mr-1.5 h-4 w-4" />New subscription</Button>} />

      {subs.length > 3 && (
        <div className="relative mb-3 max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search subscriptions" aria-label="Search subscriptions" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-8" />
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
      ) : visible.length === 0 ? (
        <p className="rounded-lg border border-border bg-card py-10 text-center text-[13px] text-muted-foreground">
          {subs.length ? 'No subscriptions match your search.' : 'No subscriptions yet. Create one to start downloading a channel.'}
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border bg-card">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="h-9 border-b border-border text-left text-[12px] font-normal text-muted-foreground">
                <th className="pl-4 pr-3 font-normal">Subscription</th>
                <th className="hidden px-3 font-normal md:table-cell">Frequency</th>
                <th className="hidden px-3 font-normal lg:table-cell">Filter</th>
                <th className="hidden px-3 text-right font-normal lg:table-cell">Downloaded</th>
                <th className="hidden px-3 text-right font-normal md:table-cell">Last synced</th>
                <th className="hidden px-3 font-normal xl:table-cell">New, 24h</th>
                <th className="px-3 font-normal">Enabled</th>
                <th className="w-10" />
              </tr>
            </thead>
            <tbody>
              {visible.map((s, i) => {
                const name = s.name || s.channel_title || chanTitle(s.channel_id)
                const detail = [s.name ? s.channel_title || chanTitle(s.channel_id) : null, s.topic_title || (s.topic_id ? `Topic ${s.topic_id}` : null)].filter(Boolean).join(' / ')
                return (
                  <SubscriptionRow key={s.id} ref={(el) => { rows.current[i] = el }} sub={s} title={name} detail={detail}
                    pulse={overview?.subscriptions.find((o) => o.id === s.id)} focused={i === active}
                    onFocus={() => setActive(i)} onOpen={() => navigate(`/subscriptions/${s.id}`)}
                    onDelete={() => setDeleteId(s.id)} onScan={() => setScanId(s.id)} />
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <DeleteConfirm id={deleteId} onDone={() => setDeleteId(null)} />
      {scanId !== null && <ScanRunner key={scanId} id={scanId} onDone={() => setScanId(null)} />}
    </Page>
  )
}
