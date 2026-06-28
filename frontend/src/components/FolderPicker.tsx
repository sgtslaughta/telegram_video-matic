import { useState } from 'react'
import { Folder, FolderOpen, CornerLeftUp, Check } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover'
import { ScrollArea } from '@/components/ui/scroll-area'
import * as api from '@/lib/api'
import type { FsDirs } from '@/lib/types'

// Storage-path input with a browse popover that lists server subfolders
// (sandboxed to MEDIA_ROOT). Click a folder to descend, breadcrumb up, then
// "Use this folder" to write the current path back into the field.
// ponytail: one dir level per fetch; typing the path by hand still works.
export default function FolderPicker({
  id,
  value,
  onChange,
  placeholder,
}: {
  id?: string
  value: string
  onChange: (path: string) => void
  placeholder?: string
}) {
  const [open, setOpen] = useState(false)
  const [view, setView] = useState<FsDirs | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const browse = async (path?: string) => {
    setLoading(true)
    setError(null)
    try {
      setView(await api.fs.listDirs(path))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not read folder')
    } finally {
      setLoading(false)
    }
  }

  const onOpenChange = (next: boolean) => {
    setOpen(next)
    // Start at the typed path if there is one, else the media root.
    if (next) browse(value || undefined)
  }

  return (
    <div className="flex gap-2">
      <Input
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      <Popover open={open} onOpenChange={onOpenChange}>
        <PopoverTrigger asChild>
          <Button type="button" variant="outline" size="icon" aria-label="Browse folders">
            <FolderOpen className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-2" align="end">
          <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
            <button
              type="button"
              className="inline-flex items-center gap-1 hover:text-foreground disabled:opacity-40"
              disabled={!view?.parent || loading}
              onClick={() => view?.parent && browse(view.parent)}
            >
              <CornerLeftUp className="h-3.5 w-3.5" /> Up
            </button>
            <span className="truncate font-mono" title={view?.path}>
              {view?.path ?? '…'}
            </span>
          </div>

          <ScrollArea className="h-56 rounded border border-border">
            {error ? (
              <p className="p-3 text-sm text-destructive">{error}</p>
            ) : loading ? (
              <p className="p-3 text-sm text-muted-foreground">Loading…</p>
            ) : view && view.dirs.length === 0 ? (
              <p className="p-3 text-sm text-muted-foreground">No subfolders</p>
            ) : (
              view?.dirs.map((name) => (
                <button
                  key={name}
                  type="button"
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm hover:bg-accent hover:text-accent-foreground"
                  onClick={() => browse(`${view.path}/${name}`)}
                >
                  <Folder className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="truncate">{name}</span>
                </button>
              ))
            )}
          </ScrollArea>

          <Button
            type="button"
            size="sm"
            className="mt-2 w-full gap-2"
            disabled={!view}
            onClick={() => {
              if (view) onChange(view.path)
              setOpen(false)
            }}
          >
            <Check className="h-4 w-4" /> Use this folder
          </Button>
        </PopoverContent>
      </Popover>
    </div>
  )
}
