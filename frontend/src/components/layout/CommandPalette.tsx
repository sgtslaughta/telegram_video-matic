import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Command } from 'cmdk'
import { Moon, Rss } from 'lucide-react'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { useTheme } from '@/hooks/useTheme'
import { useSubscriptions } from '@/hooks/useSubscriptions'
import { NAV } from './nav'

const item =
  'flex h-9 cursor-pointer items-center gap-2.5 rounded-md px-2.5 text-[13px] text-muted-foreground aria-selected:bg-accent aria-selected:text-foreground'
const group = '[&_[cmdk-group-heading]]:px-2.5 [&_[cmdk-group-heading]]:pb-1 [&_[cmdk-group-heading]]:pt-2 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:text-muted-foreground'

export default function CommandPalette({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const navigate = useNavigate()
  const { toggleTheme } = useTheme()
  const { data: subs } = useSubscriptions()

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        onOpenChange(!open)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onOpenChange])

  const go = (href: string) => {
    onOpenChange(false)
    navigate(href)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="top-[20%] translate-y-0 gap-0 overflow-hidden p-0 sm:max-w-lg">
        <DialogTitle className="sr-only">Search</DialogTitle>
        <Command loop className="flex flex-col">
          <Command.Input
            autoFocus
            placeholder="Go to a page or subscription"
            className="h-11 border-b border-border bg-transparent px-4 text-[14px] outline-none placeholder:text-muted-foreground"
          />
          <Command.List className="max-h-80 overflow-y-auto p-1.5">
            <Command.Empty className="px-3 py-6 text-center text-[13px] text-muted-foreground">
              Nothing matches. Try a page name or a subscription.
            </Command.Empty>
            <Command.Group heading="Pages" className={group}>
              {NAV.map(({ label, href, icon: Icon, keys }) => (
                <Command.Item key={href} value={label} onSelect={() => go(href)} className={item}>
                  <Icon className="h-4 w-4" strokeWidth={1.75} />
                  <span className="flex-1">{label}</span>
                  <kbd className="text-[11px]">G {keys.toUpperCase()}</kbd>
                </Command.Item>
              ))}
            </Command.Group>
            {!!subs?.length && (
              <Command.Group heading="Subscriptions" className={group}>
                {subs.map((s) => (
                  <Command.Item key={s.id} value={`sub ${s.name ?? ''} ${s.channel_title ?? ''} ${s.topic_title ?? ''}`}
                    onSelect={() => go(`/subscriptions/${s.id}`)} className={item}>
                    <Rss className="h-4 w-4" strokeWidth={1.75} />
                    <span className="flex-1 truncate">{s.name || s.topic_title || s.channel_title}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}
            <Command.Group heading="Actions" className={group}>
              <Command.Item value="toggle theme" onSelect={() => { toggleTheme(); onOpenChange(false) }} className={item}>
                <Moon className="h-4 w-4" strokeWidth={1.75} />
                Toggle light and dark theme
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </DialogContent>
    </Dialog>
  )
}
