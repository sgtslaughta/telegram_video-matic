import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import TelegramLoginDialog from '@/components/telegram/TelegramLoginDialog'
import { useTgStatus } from '@/hooks/useTgStatus'
import { AccountStatus } from '@/lib/types'

export default function Shell() {
  const { data: tg, error } = useTgStatus()
  // Only a genuine network failure (no HTTP status) means "can't reach server".
  // HTTP errors like 401 are handled elsewhere (api client redirects to /login).
  const backendDown = !!error && (error as { status?: number }).status === undefined
  const [loginOpen, setLoginOpen] = useState(false)
  const connected = tg?.status === AccountStatus.CONNECTED

  // Auto-open once when we learn the account is not connected.
  useEffect(() => {
    if (tg && !connected) setLoginOpen(true)
  }, [tg, connected])

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar connected={connected} onConnectClick={() => setLoginOpen(true)} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header connected={connected} onConnectClick={() => setLoginOpen(true)} />
        {backendDown && (
          <div className="flex items-center gap-2 bg-destructive px-6 py-2 text-sm font-medium text-destructive-foreground">
            <span className="h-2 w-2 rounded-full bg-destructive-foreground" />
            Can’t reach the server — retrying…
          </div>
        )}
        <main className="flex-1 overflow-auto bg-background">
          <Outlet />
        </main>
      </div>
      <TelegramLoginDialog open={loginOpen} onOpenChange={setLoginOpen} />
    </div>
  )
}
