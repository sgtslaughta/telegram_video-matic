import { motion } from 'framer-motion'
import { useActiveDownloads } from '@/hooks/useDownloads'
import { useEvents } from '@/hooks/useEvents'
import { useSubscriptions } from '@/hooks/useSubscriptions'
import { useTgStatus } from '@/hooks/useTgStatus'
import { ProgressBar } from '@/components/shared/ProgressBar'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import type * as T from '@/lib/types'

export default function Dashboard() {
  const downloads = useActiveDownloads()
  const events = useEvents({ limit: 5 })
  const subscriptions = useSubscriptions()
  const tgStatus = useTgStatus()

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.4, ease: 'easeOut' },
    },
  }

  const heroVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: { duration: 0.6, ease: 'easeOut' },
    },
  }

  const activeDownloadCount = downloads.data?.length ?? 0

  return (
    <motion.div
      className="space-y-6 p-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Hero Banner */}
      <motion.div
        variants={heroVariants}
        className="relative overflow-hidden rounded-lg bg-gradient-to-br from-[#229ED9] to-[#1a7aaf] px-8 py-12 text-white"
      >
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_50%,rgba(255,255,255,0.1),transparent_50%)]" />
        </div>
        <div className="relative">
          <h1 className="text-4xl font-bold tracking-tight">Welcome back</h1>
          <p className="mt-2 text-lg text-blue-100">
            {activeDownloadCount > 0
              ? `${activeDownloadCount} active download${activeDownloadCount !== 1 ? 's' : ''}`
              : 'Your media manager is ready'}
          </p>
        </div>
      </motion.div>

      {/* Stat Cards */}
      <motion.div
        variants={containerVariants}
        className="grid grid-cols-1 gap-4 md:grid-cols-3"
      >
        <motion.div
          variants={itemVariants}
          className="rounded-lg border border-gray-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
        >
          <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Subscriptions
          </div>
          <div className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            {subscriptions.data?.length ?? 0}
          </div>
        </motion.div>

        <motion.div
          variants={itemVariants}
          className="rounded-lg border border-gray-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
        >
          <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Pending
          </div>
          <div className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            {subscriptions.data?.filter((s) => !s.enabled).length ?? 0}
          </div>
        </motion.div>

        <motion.div
          variants={itemVariants}
          className="rounded-lg border border-gray-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
        >
          <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Downloaded
          </div>
          <div className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            {subscriptions.data?.filter((s) => s.enabled).length ?? 0}
          </div>
        </motion.div>
      </motion.div>

      {/* Active Downloads */}
      <motion.div variants={itemVariants}>
        <div className="rounded-lg border border-gray-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          <div className="border-b border-gray-200 px-6 py-4 dark:border-slate-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Active Downloads
            </h2>
          </div>

          {downloads.isLoading ? (
            <div className="px-6 py-8 text-center text-gray-600 dark:text-gray-400">
              Loading...
            </div>
          ) : downloads.data && downloads.data.length > 0 ? (
            <div className="divide-y divide-gray-200 dark:divide-slate-700">
              {downloads.data.map((job) => (
                <motion.div
                  key={job.id}
                  variants={itemVariants}
                  className="px-6 py-4"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      Download #{job.id}
                    </span>
                    <StatusBadge status={job.status} />
                  </div>
                  <ProgressBar progress={job.progress} animated showLabel />
                  <div className="mt-2 flex justify-between text-xs text-gray-600 dark:text-gray-400">
                    <span>
                      {job.bytes_done && job.bytes_total
                        ? `${(job.bytes_done / 1024 / 1024).toFixed(1)}MB / ${(job.bytes_total / 1024 / 1024).toFixed(1)}MB`
                        : '—'}
                    </span>
                    <span>
                      {job.speed_bps
                        ? `${(job.speed_bps / 1024 / 1024).toFixed(1)}MB/s`
                        : '—'}
                    </span>
                    {job.eta_sec && (
                      <span>
                        ETA{' '}
                        {Math.floor(job.eta_sec / 60) > 0
                          ? `${Math.floor(job.eta_sec / 60)}m`
                          : `${job.eta_sec}s`}
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="px-6 py-8">
              <EmptyState
                title="No active downloads"
                message="Your subscriptions will appear here when actively downloading."
              />
            </div>
          )}
        </div>
      </motion.div>

      {/* Recent Activity */}
      <motion.div variants={itemVariants}>
        <div className="rounded-lg border border-gray-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          <div className="border-b border-gray-200 px-6 py-4 dark:border-slate-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Activity
            </h2>
          </div>

          {events.isLoading ? (
            <div className="px-6 py-8 text-center text-gray-600 dark:text-gray-400">
              Loading...
            </div>
          ) : events.data && events.data.length > 0 ? (
            <div className="divide-y divide-gray-200 dark:divide-slate-700">
              {events.data.map((event, idx) => (
                <motion.div
                  key={event.id}
                  variants={itemVariants}
                  transition={{ delay: idx * 0.05 }}
                  className="flex items-start gap-4 px-6 py-4"
                >
                  <div className="mt-1 flex h-2 w-2 flex-shrink-0 rounded-full bg-[#229ED9]" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 dark:text-white">
                      {event.message}
                    </p>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                      {new Date(event.created_at).toLocaleDateString()} at{' '}
                      {new Date(event.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="px-6 py-8">
              <EmptyState
                title="No activity yet"
                message="Events will appear here as your subscriptions run."
              />
            </div>
          )}
        </div>
      </motion.div>

      {/* TG Status Debug */}
      {tgStatus.data && (
        <motion.div
          variants={itemVariants}
          className="rounded-lg border border-gray-200 bg-white p-4 text-xs text-gray-600 dark:border-slate-700 dark:bg-slate-900 dark:text-gray-400"
        >
          <span className="font-mono">
            TG: {tgStatus.data.status}
            {tgStatus.data.username && ` (@${tgStatus.data.username})`}
          </span>
        </motion.div>
      )}
    </motion.div>
  )
}
