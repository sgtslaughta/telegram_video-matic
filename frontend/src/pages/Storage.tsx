import { Page, PageHeader } from '@/components/shared/PageHeader'
import { Skeleton } from '@/components/ui/skeleton'
import { useStorage } from '@/hooks/useStorage'
import { DiskUsage } from '@/components/storage/DiskUsage'
import { PausedPanel } from '@/components/storage/PausedPanel'
import { PreviewTable } from '@/components/storage/PreviewTable'
import { FoldersTable } from '@/components/storage/FoldersTable'
import { UntrackedTable } from '@/components/storage/UntrackedTable'

export default function Storage() {
  const { data, isLoading, error } = useStorage()
  const head = <PageHeader title="Storage" description="Disk usage, cleanup preview and files the app doesn’t track." />

  if (error) {
    return <Page>{head}<p className="text-[13px] text-muted-foreground">Storage couldn’t load ({(error as Error).message}). It retries every minute.</p></Page>
  }
  if (isLoading || !data) {
    return <Page>{head}<div className="space-y-4">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-32 w-full" />)}</div></Page>
  }
  return (
    <Page>
      {head}
      <div className="space-y-4">
        <DiskUsage s={data} />
        {data.paused && (
          <PausedPanel count={data.paused.count} gb={data.paused.gb}
            onReview={() => document.getElementById('cleanup-preview')?.scrollIntoView({ behavior: 'smooth' })} />
        )}
        <PreviewTable preview={data.preview} />
        <FoldersTable folders={data.folders} />
        <UntrackedTable untracked={data.untracked} />
      </div>
    </Page>
  )
}
