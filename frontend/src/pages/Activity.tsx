import { useState } from 'react'
import { motion } from 'framer-motion'
import { useEvents } from '@/hooks/useEvents'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import type * as T from '@/lib/types'

const LIMIT = 10
const EVENT_LEVELS = [
  { value: '', label: 'All Levels' },
  { value: 'debug', label: 'Debug' },
  { value: 'info', label: 'Info' },
  { value: 'warning', label: 'Warning' },
  { value: 'error', label: 'Error' },
]

const EVENT_KINDS = [
  { value: '', label: 'All Kinds' },
  { value: 'subscription', label: 'Subscription' },
  { value: 'download', label: 'Download' },
  { value: 'job', label: 'Job' },
]

const LEVEL_COLORS: Record<string, string> = {
  debug: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  info: 'bg-blue-100 text-blue-800 dark:bg-[#229ED9]/20 dark:text-blue-300',
  success: 'bg-green-100 text-green-800 dark:bg-green-700 dark:text-green-200',
  warning: 'bg-amber-100 text-amber-800 dark:bg-amber-700 dark:text-amber-200',
  error: 'bg-red-100 text-red-800 dark:bg-red-700 dark:text-red-200',
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.2 },
  },
}

export default function Activity() {
  const [levelFilter, setLevelFilter] = useState('')
  const [kindFilter, setKindFilter] = useState('')
  const [offset, setOffset] = useState(0)

  const filters: Parameters<typeof useEvents>[0] = {
    limit: LIMIT,
    offset,
    ...(levelFilter && { level: levelFilter }),
    ...(kindFilter && { kind: kindFilter }),
  }

  const events = useEvents(filters)

  const handlePrevious = () => {
    if (offset >= LIMIT) {
      setOffset(offset - LIMIT)
    }
  }

  const handleNext = () => {
    if (events.data && events.data.length === LIMIT) {
      setOffset(offset + LIMIT)
    }
  }

  const canGoPrevious = offset >= LIMIT
  const canGoNext = events.data && events.data.length === LIMIT

  return (
    <motion.div
      className="space-y-6 p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Activity</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">View and filter system events</p>
      </div>

      {/* Filters */}
      <motion.div
        className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900"
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Level
            </label>
            <select
              value={levelFilter}
              onChange={(e) => {
                setLevelFilter(e.target.value)
                setOffset(0)
              }}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-[#229ED9] focus:ring-2 focus:ring-[#229ED9]/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            >
              {EVENT_LEVELS.map((level) => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Kind
            </label>
            <select
              value={kindFilter}
              onChange={(e) => {
                setKindFilter(e.target.value)
                setOffset(0)
              }}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-[#229ED9] focus:ring-2 focus:ring-[#229ED9]/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            >
              {EVENT_KINDS.map((kind) => (
                <option key={kind.value} value={kind.value}>
                  {kind.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </motion.div>

      {/* Events Table */}
      <motion.div
        className="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <div className="border-b border-gray-200 px-6 py-4 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Events</h2>
        </div>

        {events.isLoading ? (
          <div className="px-6 py-8 text-center text-gray-600 dark:text-gray-400">
            Loading...
          </div>
        ) : events.data && events.data.length > 0 ? (
          <>
            <motion.div
              className="divide-y divide-gray-200 dark:divide-slate-700"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {events.data.map((event) => (
                <motion.div
                  key={event.id}
                  variants={itemVariants}
                  className="flex items-start gap-4 px-6 py-4 transition-colors hover:bg-gray-50 dark:hover:bg-slate-800/50"
                >
                  {/* Level Badge */}
                  <div className="mt-1 flex-shrink-0">
                    <span
                      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${
                        LEVEL_COLORS[event.level as T.EventLevel] ||
                        LEVEL_COLORS['debug']
                      }`}
                    >
                      {event.level}
                    </span>
                  </div>

                  {/* Message and Details */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 dark:text-white">{event.message}</p>
                    <div className="mt-1 flex gap-4 text-xs text-gray-500 dark:text-gray-500">
                      <span>{event.kind}</span>
                      <span>
                        {new Date(event.created_at).toLocaleDateString()} at{' '}
                        {new Date(event.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>

            {/* Pagination */}
            <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-between dark:border-slate-700">
              <motion.button
                onClick={handlePrevious}
                disabled={!canGoPrevious}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors disabled:text-gray-400 disabled:hover:bg-transparent dark:text-gray-300 dark:hover:bg-slate-800 dark:disabled:text-gray-600"
              >
                Previous
              </motion.button>

              <span className="text-sm text-gray-600 dark:text-gray-400">
                Offset: {offset}
              </span>

              <motion.button
                onClick={handleNext}
                disabled={!canGoNext}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors disabled:text-gray-400 disabled:hover:bg-transparent dark:text-gray-300 dark:hover:bg-slate-800 dark:disabled:text-gray-600"
              >
                Next
              </motion.button>
            </div>
          </>
        ) : (
          <div className="px-6 py-8">
            <EmptyState
              title="No events"
              message="Events will appear here as system activity occurs."
            />
          </div>
        )}
      </motion.div>
    </motion.div>
  )
}
