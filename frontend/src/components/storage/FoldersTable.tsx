import { formatBytes } from '@/lib/format'
import type { StorageFolder } from '@/hooks/useStorage'
import { Panel, TD, TH } from './Panel'

export function FoldersTable({ folders }: { folders: StorageFolder[] }) {
  const sorted = [...folders].sort((a, b) => b.bytes - a.bytes)
  const max = sorted[0]?.bytes || 1
  return (
    <Panel title="Folders">
      {sorted.length ? (
        <table className="w-full text-[13px]">
          <thead><tr className="border-b border-border">
            <th className={TH}>Folder</th><th className={`${TH} hidden w-[30%] sm:table-cell`}><span className="sr-only">Share</span></th>
            <th className={`${TH} text-right`}>Files</th><th className={`${TH} text-right`}>Size</th>
          </tr></thead>
          <tbody className="divide-y divide-border">
            {sorted.map((f) => (
              <tr key={f.path} className="transition-colors hover:bg-accent/60">
                <td className={`${TD} max-w-[280px]`}><span className="block truncate font-mono text-[12px]" title={f.path}>{f.path || '/'}</span></td>
                <td className={`${TD} hidden sm:table-cell`}>
                  <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-brand" style={{ width: `${(f.bytes / max) * 100}%` }} />
                  </div>
                </td>
                <td className={`${TD} text-right tabular-nums text-muted-foreground`}>{f.count}</td>
                <td className={`${TD} text-right tabular-nums`}>{formatBytes(f.bytes)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="px-4 py-6 text-[13px] text-muted-foreground">No folders yet. Downloaded videos will be listed here.</p>
      )}
    </Panel>
  )
}
