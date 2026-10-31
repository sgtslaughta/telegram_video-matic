import Logo from '@/components/Logo'
import TelegramLoginFlow from '@/components/telegram/TelegramLoginFlow'

export default function Connect() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <Logo className="h-16 w-16" title="TGVM" />
          <h1 className="text-[20px] font-semibold tracking-tight">Connect Telegram</h1>
          <p className="text-[13px] text-muted-foreground">Sign in to the account that can see your channels.</p>
        </div>
        <TelegramLoginFlow />
      </div>
    </div>
  )
}
