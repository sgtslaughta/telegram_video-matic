import { Moon, Sun, User, LogOut } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import AccentPicker from '@/components/AccentPicker'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import * as api from '@/lib/api'

export default function Header({
  connected,
  onConnectClick,
}: {
  connected: boolean
  onConnectClick: () => void
}) {
  const { toggleTheme, effectiveTheme } = useTheme()

  const logout = async () => {
    await api.auth.logout().catch(() => {})
    window.location.href = '/login'
  }

  return (
    <header className="flex h-16 items-center gap-4 border-b border-border bg-background px-6">
      <div className="ml-auto flex items-center gap-2">
        <Badge
          variant="outline"
          className="cursor-pointer"
          onClick={onConnectClick}
        >
          <span
            className={`mr-1.5 h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-amber-500'}`}
          />
          {connected ? 'Telegram' : 'Connect'}
        </Badge>
        <AccentPicker />
        <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
          {effectiveTheme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="User menu">
              <User className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={logout}>
              <LogOut className="mr-2 h-4 w-4" /> Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
