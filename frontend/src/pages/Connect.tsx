import TelegramLoginFlow from '@/components/telegram/TelegramLoginFlow'

export default function Connect() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="w-full max-w-md">
        <TelegramLoginFlow />
      </div>
    </div>
  )
}
