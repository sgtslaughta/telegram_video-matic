import { MediaStatus, AccountStatus, JobStatus } from '@/lib/types'
import { clsx } from 'clsx'

interface StatusBadgeProps {
  status: string
}

const STATUS_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  // MediaStatus
  [MediaStatus.READY]: { bg: 'bg-green-100', text: 'text-green-800', label: 'Ready' },
  [MediaStatus.DOWNLOADED]: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    label: 'Downloaded',
  },
  [MediaStatus.PENDING]: { bg: 'bg-amber-100', text: 'text-amber-800', label: 'Pending' },
  [MediaStatus.DOWNLOADING]: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    label: 'Downloading',
  },
  [MediaStatus.PROCESSING]: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    label: 'Processing',
  },
  [MediaStatus.FAILED]: { bg: 'bg-red-100', text: 'text-red-800', label: 'Failed' },

  // AccountStatus
  [AccountStatus.CONNECTED]: { bg: 'bg-green-100', text: 'text-green-800', label: 'Connected' },
  [AccountStatus.DISCONNECTED]: {
    bg: 'bg-muted',
    text: 'text-foreground',
    label: 'Disconnected',
  },
  [AccountStatus.WAITING_PHONE]: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    label: 'Waiting Phone',
  },
  [AccountStatus.WAITING_CODE]: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    label: 'Waiting Code',
  },
  [AccountStatus.WAITING_PASSWORD]: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    label: 'Waiting Password',
  },

  // JobStatus
  [JobStatus.PENDING]: { bg: 'bg-amber-100', text: 'text-amber-800', label: 'Pending' },
  [JobStatus.DOWNLOADING]: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    label: 'Downloading',
  },
  [JobStatus.COMPLETED]: { bg: 'bg-green-100', text: 'text-green-800', label: 'Completed' },
  [JobStatus.FAILED]: { bg: 'bg-red-100', text: 'text-red-800', label: 'Failed' },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_COLORS[status] || {
    bg: 'bg-muted',
    text: 'text-foreground',
    label: status,
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-3 py-1 text-sm font-medium',
        config.bg,
        config.text
      )}
    >
      {config.label}
    </span>
  )
}
