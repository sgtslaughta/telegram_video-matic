import { motion } from 'framer-motion'
import { clsx } from 'clsx'

interface ProgressBarProps {
  progress: number
  className?: string
  showLabel?: boolean
  animated?: boolean
}

export function ProgressBar({
  progress,
  className,
  showLabel = false,
  animated = true,
}: ProgressBarProps) {
  const clampedProgress = Math.min(Math.max(progress, 0), 100)

  return (
    <div className={clsx('w-full', className)}>
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <motion.div
          className="h-full bg-blue-500"
          initial={animated ? { width: 0 } : { width: `${clampedProgress}%` }}
          animate={{ width: `${clampedProgress}%` }}
          transition={{ duration: animated ? 0.5 : 0, ease: 'easeOut' }}
        />
      </div>
      {showLabel && (
        <p className="mt-1 text-right text-xs text-gray-600">{Math.round(clampedProgress)}%</p>
      )}
    </div>
  )
}
