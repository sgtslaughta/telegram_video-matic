import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMediaDetail, useDownloadMedia, useRequeueMedia } from '@/hooks/useMedia'
import { useActiveDownloads } from '@/hooks/useDownloads'
import { MediaThumb } from '@/components/shared/MediaThumb'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { ProgressBar } from '@/components/shared/ProgressBar'
import * as api from '@/lib/api'
import { MediaStatus } from '@/lib/types'

export default function MediaDetail() {
  const { id: idParam } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const mediaId = parseInt(idParam || '0', 10)

  const media = useMediaDetail(mediaId)
  const downloads = useActiveDownloads()
  const downloadMutation = useDownloadMedia(mediaId)
  const requeueMutation = useRequeueMedia(mediaId)

  const activeDownload = downloads.data?.find((d) => d.media_id === mediaId)
  const isDownloading = activeDownload?.status === 'downloading'

  if (media.isLoading) {
    return (
      <div className="flex h-screen items-center justify-center p-6">
        <div className="text-gray-600 dark:text-gray-400">Loading...</div>
      </div>
    )
  }

  if (media.error || !media.data) {
    return (
      <div className="flex h-screen items-center justify-center p-6">
        <div className="text-red-600 dark:text-red-400">
          Failed to load media
        </div>
      </div>
    )
  }

  const item = media.data
  const reactions = item.reactions as Record<string, number> | undefined

  return (
    <motion.div
      className="space-y-6 p-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Back Button */}
      <button
        onClick={() => navigate('/browse')}
        className="mb-4 flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back
      </button>

      {/* Main Card */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
        <div className="grid gap-8 md:grid-cols-2">
          {/* Left: Preview */}
          <div className="flex flex-col gap-4">
            <MediaThumb
              src={api.media.thumbUrl(mediaId)}
              alt={item.file_name || 'Media preview'}
              size="lg"
              className="w-full"
            />

            {/* Status & Progress */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Status
                </span>
                <StatusBadge status={item.status} />
              </div>

              {isDownloading && activeDownload && (
                <div className="space-y-1">
                  <ProgressBar
                    progress={activeDownload.progress || 0}
                    animated
                  />
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    {activeDownload.bytes_done && activeDownload.bytes_total
                      ? `${(activeDownload.bytes_done / 1024 / 1024).toFixed(1)}MB / ${(activeDownload.bytes_total / 1024 / 1024).toFixed(1)}MB`
                      : '—'}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right: Details */}
          <div className="space-y-4">
            {/* Caption */}
            {item.caption && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Caption
                </h3>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {item.caption}
                </p>
              </div>
            )}

            {/* Telegram Data */}
            <div className="space-y-3 border-t border-gray-200 pt-4 dark:border-slate-700">
              {/* Reactions */}
              {reactions && Object.keys(reactions).length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Reactions
                  </h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Object.entries(reactions).map(([emoji, count]) => (
                      <span
                        key={emoji}
                        className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs dark:bg-slate-800"
                      >
                        <span>{emoji}</span>
                        <span className="text-gray-600 dark:text-gray-400">
                          {count}
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Comments */}
              {item.comments_count !== undefined && item.comments_count > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Comments
                  </h4>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {item.comments_count} comment{item.comments_count !== 1 ? 's' : ''}
                  </p>
                </div>
              )}
            </div>

            {/* Tags */}
            {item.file_name && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  File
                </h4>
                <p className="mt-1 break-all text-xs text-gray-600 dark:text-gray-400">
                  {item.file_name}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-2 border-t border-gray-200 pt-4 dark:border-slate-700">
              {item.status !== MediaStatus.DOWNLOADED &&
                item.status !== MediaStatus.DOWNLOADING && (
                  <button
                    onClick={() => downloadMutation.mutate()}
                    disabled={downloadMutation.isPending}
                    className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-700 dark:hover:bg-blue-600"
                  >
                    {downloadMutation.isPending ? 'Downloading...' : 'Download'}
                  </button>
                )}

              {item.status === MediaStatus.FAILED && (
                <button
                  onClick={() => requeueMutation.mutate()}
                  disabled={requeueMutation.isPending}
                  className="flex-1 rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50 dark:bg-amber-700 dark:hover:bg-amber-600"
                >
                  {requeueMutation.isPending ? 'Requeuing...' : 'Requeue'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
