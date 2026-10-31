import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useTgStatus } from '@/hooks/useTgStatus'
import { AccountStatus } from '@/lib/types'
import { cn } from '@/lib/utils'
import { SettingsSection } from './SettingsSection'

export function AccountSection() {
  const { data } = useTgStatus()
  const connected = data?.status === AccountStatus.CONNECTED
  const who = data?.username ? `@${data.username}` : data?.display_name
  return (
    <SettingsSection id="account" title="Account" description="The Telegram account used to find and download videos.">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className={cn('h-2 w-2 shrink-0 rounded-full', connected ? 'bg-ok' : data?.configured ? 'bg-warn' : 'bg-idle')} />
          <div className="min-w-0 text-[13px]">
            <p className="truncate font-medium">{connected ? `Connected${who ? ` as ${who}` : ''}` : data?.configured ? 'Not signed in' : 'Not set up'}</p>
            {connected && data?.phone && <p className="text-[12px] text-muted-foreground">{data.phone}</p>}
          </div>
        </div>
        <Button asChild size="sm" variant="outline" className="h-8 text-[13px]">
          <Link to="/connect">{connected ? 'Manage account' : 'Connect Telegram'}</Link>
        </Button>
      </div>
    </SettingsSection>
  )
}
