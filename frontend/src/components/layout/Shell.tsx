import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import TelegramLoginDialog from '@/components/telegram/TelegramLoginDialog'
import { useTgStatus } from '@/hooks/useTgStatus'
import { AccountStatus } from '@/lib/types'

export default function Shell() {
  const { data: tg } = useTgStatus()
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
        <main className="flex-1 overflow-auto bg-background">
          <Outlet />
        </main>
      </div>
      <TelegramLoginDialog open={loginOpen} onOpenChange={setLoginOpen} />
    </div>
  )
}
