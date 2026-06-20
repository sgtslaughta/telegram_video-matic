import { useTheme } from '@/hooks/useTheme'
import { useTgStatus } from '@/hooks/useTgStatus'
import { useWebSocket } from '@/hooks/useWebSocket'

export default function Header() {
  const { toggleTheme, effectiveTheme } = useTheme()
  const { data: tgStatus } = useTgStatus()
  const wsConnected = useWebSocket()

  return (
    <header className="h-16 bg-white dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        {tgStatus?.authenticated && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-100">
            TG Connected
          </span>
        )}
        {wsConnected && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100">
            WS Connected
          </span>
        )}
      </div>
      <button
        onClick={toggleTheme}
        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
        aria-label="Toggle theme"
      >
        {effectiveTheme === 'dark' ? '☀️' : '🌙'}
      </button>
    </header>
  )
}
