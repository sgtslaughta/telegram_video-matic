import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog'
import TelegramLoginFlow from './TelegramLoginFlow'

export default function TelegramLoginDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (o: boolean) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Connect Telegram</DialogTitle>
          <DialogDescription>
            Sign in to your Telegram account to start syncing media.
          </DialogDescription>
        </DialogHeader>
        <TelegramLoginFlow onConnected={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  )
}
