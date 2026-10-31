import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useDeleteUntracked, type Storage, type UntrackedFile } from '@/hooks/useStorage'
import { absTime, formatBytes, relTime } from '@/lib/format'
import { withToast } from '@/lib/toast'
import { DestructiveConfirm } from './DestructiveConfirm'
import { Panel, TD, TH } from './Panel'

export function UntrackedTable({ untracked }: { untracked: Storage['untracked'] }) {
  const [target, setTarget] = useState<UntrackedFile | null>(null)
  const del = useDeleteUntracked()
  const run = async () => {
    const f = target
    setTarget(null)
    if (f) await withToast(() => del.mutateAsync(f.path), { success: 'Deleted file' })
  }
  return (
    <Panel title="Files the app doesn’t track"
      aside={untracked.count ? `${untracked.count} file${untracked.count === 1 ? '' : 's'}, ${formatBytes(untracked.bytes)}` : undefined}>
      <p className="border-b border-border px-4 py-2.5 text-[12px] text-muted-foreground">
        These files aren’t in the library, so cleanup never touches them.
      </p>
      {untracked.items.length ? (
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead><tr className="border-b border-border">
              <th className={TH}>Path</th><th className={`${TH} text-right`}>Size</th>
              <th className={TH}>Modified</th><th className={`${TH} w-12`}><span className="sr-only">Actions</span></th>
            </tr></thead>
            <tbody className="divide-y divide-border">
              {untracked.items.map((f) => (
                <tr key={f.path} className="transition-colors hover:bg-accent/60">
                  <td className={`${TD} max-w-[360px]`}><span className="block truncate font-mono text-[12px]" title={f.path}>{f.path}</span></td>
                  <td className={`${TD} text-right tabular-nums`}>{formatBytes(f.size_bytes)}</td>
                  <td className={`${TD} whitespace-nowrap text-muted-foreground`} title={absTime(f.modified)}>{relTime(f.modified)}</td>
                  <td className={`${TD} text-right`}>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-err"
                      aria-label={`Delete ${f.path}`} onClick={() => setTarget(f)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="px-4 py-6 text-[13px] text-muted-foreground">Every file in the media folder is in the library.</p>
      )}
      <DestructiveConfirm open={!!target} title="Delete this file?"
        description={`${target?.path ?? ''} will be permanently deleted from disk. It can’t be undone.`}
        confirmText="Delete file" onConfirm={run} onCancel={() => setTarget(null)} />
    </Panel>
  )
}
