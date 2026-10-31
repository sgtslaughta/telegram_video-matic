import { useState } from 'react'
import { Link } from 'react-router-dom'
import { formatBytes } from '@/lib/format'
import type { Storage, StorageItem } from '@/hooks/useStorage'
import { Panel, TD, TH } from './Panel'

const REASON: Record<StorageItem['reason'], string> = {
  age: 'Older than the retention period',
  quota: 'Over the subscription’s limit',
  disk: 'Disk is nearly full',
}

const FIRST = 20

export function PreviewTable({ preview }: { preview: Storage['preview'] }) {
  const [all, setAll] = useState(false)
  const rows = all ? preview.items : preview.items.slice(0, FIRST)
  return (
    <Panel id="cleanup-preview" title={`Deleting in the next ${preview.days} days`}
      aside={preview.count ? `${preview.count} file${preview.count === 1 ? '' : 's'}, ${formatBytes(preview.bytes)}` : undefined}>
      {preview.items.length ? (
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead><tr className="border-b border-border">
              <th className={TH}>File</th><th className={TH}>Reason</th><th className={TH}>Match date</th>
              <th className={`${TH} text-right`}>Size</th>
            </tr></thead>
            <tbody className="divide-y divide-border">
              {rows.map((i) => (
                <tr key={i.id} className="transition-colors hover:bg-accent/60">
                  <td className={`${TD} max-w-[320px]`}>
                    <Link to={`/media/${i.id}`} className="block truncate font-medium hover:underline" title={i.file_name}>{i.file_name}</Link>
                  </td>
                  <td className={`${TD} text-muted-foreground`}>{REASON[i.reason] ?? i.reason}</td>
                  <td className={`${TD} whitespace-nowrap text-muted-foreground`}>{i.content_date ? new Date(i.content_date).toLocaleDateString(undefined, { dateStyle: 'medium' }) : '-'}</td>
                  <td className={`${TD} text-right tabular-nums`}>{formatBytes(i.size_bytes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {preview.items.length > FIRST && (
            <button onClick={() => setAll((v) => !v)}
              className="w-full border-t border-border py-2.5 text-[13px] font-medium text-brand transition-colors hover:bg-accent/60">
              {all ? 'Show fewer' : `Show all ${preview.items.length} files`}
            </button>
          )}
        </div>
      ) : (
        <p className="px-4 py-6 text-[13px] text-muted-foreground">Nothing is due for cleanup this week.</p>
      )}
    </Panel>
  )
}
