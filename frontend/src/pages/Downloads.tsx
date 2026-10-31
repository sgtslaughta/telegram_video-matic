import { Page, PageHeader } from '@/components/shared/PageHeader'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { RugbyMatchReview } from '@/components/RugbyMatchReview'
import { HistoryTab } from '@/components/downloads/HistoryTab'
import { QueueTab } from '@/components/downloads/QueueTab'
import { WantedTab } from '@/components/downloads/WantedTab'
import { useFailed, useWanted } from '@/components/downloads/data'
import { useActiveDownloads, useQueuedDownloads } from '@/hooks/useDownloads'
import { useDownloadsTabs } from '@/hooks/useDownloadsTabs'
import { useRugbyMatches } from '@/hooks/useRugby'
import { useWebSocket } from '@/hooks/useWebSocket'

const trigger = 'rounded-none border-b-2 border-transparent bg-transparent px-3 py-2 text-[13px] data-[state=active]:border-brand data-[state=active]:bg-transparent data-[state=active]:shadow-none'

export default function Downloads() {
  useWebSocket() // keeps live progress flowing while this page is open
  const { tab, kind, setTab, setKind } = useDownloadsTabs()
  const active = useActiveDownloads()
  const queued = useQueuedDownloads()
  const wanted = useWanted()
  const failed = useFailed()
  const review = useRugbyMatches('needs_review')

  const count = (n: number | undefined, label: string) => (n ? `${n} ${label}` : null)
  const parts = [
    count(active.data?.length, 'downloading'), count(queued.data?.length, 'queued'),
    count(wanted.data?.length, 'missing games'), count(failed.data?.length, 'failed'),
  ].filter(Boolean)
  const loading = active.isLoading || queued.isLoading
  const badge = (n?: number) => (n ? <span className="ml-1.5 text-[11px] tabular-nums text-muted-foreground">{n}</span> : null)

  return (
    <Page wide>
      <PageHeader title="Downloads" description={loading ? <Skeleton className="h-4 w-48" /> : parts.length ? parts.join(', ') : 'Nothing in progress.'} />
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="mb-4 h-auto w-full justify-start gap-1 rounded-none border-b border-border bg-transparent p-0">
          <TabsTrigger value="queue" className={trigger}>Queue{badge((active.data?.length ?? 0) + (queued.data?.length ?? 0))}</TabsTrigger>
          <TabsTrigger value="wanted" className={trigger}>Wanted{badge((wanted.data?.length ?? 0) + (failed.data?.length ?? 0))}</TabsTrigger>
          <TabsTrigger value="history" className={trigger}>History</TabsTrigger>
          <TabsTrigger value="review" className={trigger}>Review{badge(review.data?.length)}</TabsTrigger>
        </TabsList>
        <TabsContent value="queue" className="mt-0"><QueueTab /></TabsContent>
        <TabsContent value="wanted" className="mt-0"><WantedTab /></TabsContent>
        <TabsContent value="history" className="mt-0"><HistoryTab kind={kind} setKind={setKind} /></TabsContent>
        <TabsContent value="review" className="mt-0"><RugbyMatchReview /></TabsContent>
      </Tabs>
    </Page>
  )
}
