import { motion } from 'framer-motion'
import { useActiveDownloads } from '@/hooks/useDownloads'
import { useEvents } from '@/hooks/useEvents'
import { useSubscriptions } from '@/hooks/useSubscriptions'
import { useTgStatus } from '@/hooks/useTgStatus'
import { ProgressBar } from '@/components/shared/ProgressBar'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
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
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Subscriptions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{subscriptions.data?.length ?? 0}</div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Pending</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {subscriptions.data?.filter((s) => !s.enabled).length ?? 0}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Downloaded</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {subscriptions.data?.filter((s) => s.enabled).length ?? 0}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Active Downloads */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Active Downloads</CardTitle>
          </CardHeader>
          <CardContent>
            {downloads.isLoading ? (
              <div className="py-8 text-center text-gray-600 dark:text-gray-400">
                Loading...
              </div>
            ) : downloads.data && downloads.data.length > 0 ? (
              <div className="space-y-4">
                {downloads.data.map((job) => (
                  <motion.div
                    key={job.id}
                    variants={itemVariants}
                    className="border rounded-lg p-4 border-slate-200 dark:border-slate-700"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-sm font-medium">Download #{job.id}</span>
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
              <EmptyState
                title="No active downloads"
                message="Your subscriptions will appear here when actively downloading."
              />
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Activity */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {events.isLoading ? (
              <div className="py-8 text-center text-gray-600 dark:text-gray-400">
                Loading...
              </div>
            ) : events.data && events.data.length > 0 ? (
              <div className="space-y-4">
                {events.data.map((event, idx) => (
                  <motion.div
                    key={event.id}
                    variants={itemVariants}
                    transition={{ delay: idx * 0.05 }}
                    className="flex items-start gap-3 pb-3 border-b border-slate-200 dark:border-slate-700 last:border-b-0"
                  >
                    <div className="mt-1.5 flex h-2 w-2 flex-shrink-0 rounded-full bg-[#229ED9]" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm">{event.message}</p>
                      <p className="mt-1 text-xs text-gray-500">
                        {new Date(event.created_at).toLocaleDateString()} at{' '}
                        {new Date(event.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No activity yet"
                message="Events will appear here as your subscriptions run."
              />
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* TG Status Debug */}
      {tgStatus.data && (
        <motion.div variants={itemVariants}>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Badge variant="outline">TG Status</Badge>
                <span className="font-mono text-sm">
                  {tgStatus.data.status}
                  {tgStatus.data.username && ` (@${tgStatus.data.username})`}
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  )
}
