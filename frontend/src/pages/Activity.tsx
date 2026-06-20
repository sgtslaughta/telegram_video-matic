import { useState } from 'react'
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
  debug: 'bg-gray-100 text-gray-800',
  info: 'bg-blue-100 text-blue-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-amber-100 text-amber-800',
  error: 'bg-red-100 text-red-800',
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
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Activity</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">View and filter system events</p>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
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
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
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
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            >
              {EVENT_KINDS.map((kind) => (
                <option key={kind.value} value={kind.value}>
                  {kind.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Events Table */}
      <div className="rounded-lg border border-gray-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <div className="border-b border-gray-200 px-6 py-4 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Events</h2>
        </div>

        {events.isLoading ? (
          <div className="px-6 py-8 text-center text-gray-600 dark:text-gray-400">
            Loading...
          </div>
        ) : events.data && events.data.length > 0 ? (
          <>
            <div className="divide-y divide-gray-200 dark:divide-slate-700">
              {events.data.map((event) => (
                <div
                  key={event.id}
                  className="flex items-start gap-4 px-6 py-4 hover:bg-gray-50 dark:hover:bg-slate-800"
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
                </div>
              ))}
            </div>

            {/* Pagination */}
            <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-between dark:border-slate-700">
              <button
                onClick={handlePrevious}
                disabled={!canGoPrevious}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-transparent dark:text-gray-300 dark:hover:bg-slate-800 dark:disabled:text-gray-600"
              >
                Previous
              </button>

              <span className="text-sm text-gray-600 dark:text-gray-400">
                Offset: {offset}
              </span>

              <button
                onClick={handleNext}
                disabled={!canGoNext}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-transparent dark:text-gray-300 dark:hover:bg-slate-800 dark:disabled:text-gray-600"
              >
                Next
              </button>
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
      </div>
    </div>
  )
}
