import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useChannels, useTopics } from '@/hooks/useChannelsTopics'
import { useMedia, useDownloadMedia } from '@/hooks/useMedia'
import { MediaThumb } from '@/components/shared/MediaThumb'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import * as api from '@/lib/api'

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
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3 },
  },
}

export default function Browse() {
  const navigate = useNavigate()
  const [selectedChannel, setSelectedChannel] = useState<number | null>(null)
  const [selectedTopic, setSelectedTopic] = useState<number | null>(null)

  const channels = useChannels()
  const topics = useTopics(selectedChannel)
  const media = useMedia({
    channel_id: selectedChannel ?? undefined,
    topic_id: selectedTopic ?? undefined,
  })

  const handleChannelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value ? parseInt(e.target.value) : null
    setSelectedChannel(id)
    setSelectedTopic(null)
  }

  const handleTopicChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value ? parseInt(e.target.value) : null
    setSelectedTopic(id)
  }

  return (
    <motion.div
      className="space-y-6 p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Browse Media</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">Filter and download media from your channels</p>
      </div>

      <motion.div
        className="space-y-4 rounded-lg bg-white p-6 shadow-sm dark:bg-slate-900 dark:border dark:border-slate-700"
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Channel</label>
          <select
            value={selectedChannel || ''}
            onChange={handleChannelChange}
            className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-[#229ED9] focus:ring-2 focus:ring-[#229ED9]/20 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:focus:border-[#229ED9]"
            disabled={channels.isLoading}
          >
            <option value="">Select a channel...</option>
            {channels.data?.map((ch) => (
              <option key={ch.id} value={ch.id}>
                {ch.title}
              </option>
            ))}
          </select>
        </div>

        {selectedChannel && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Topic (optional)</label>
            <select
              value={selectedTopic || ''}
              onChange={handleTopicChange}
              className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-[#229ED9] focus:ring-2 focus:ring-[#229ED9]/20 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:focus:border-[#229ED9]"
              disabled={topics.isLoading}
            >
              <option value="">All topics</option>
              {topics.data?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.title}
                </option>
              ))}
            </select>
          </motion.div>
        )}
      </motion.div>

      {!selectedChannel ? (
        <EmptyState
          title="Select a channel"
          message="Choose a channel above to browse and download media"
        />
      ) : media.isLoading ? (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading media...</div>
      ) : !media.data?.length ? (
        <EmptyState
          title="No media found"
          message="This channel has no media available"
        />
      ) : (
        <motion.div
          className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {media.data.map((item) => (
            <MediaCard key={item.id} item={item} />
          ))}
        </motion.div>
      )}
    </motion.div>
  )
}

function MediaCard({ item }: { item: any }) {
  const navigate = useNavigate()
  const download = useDownloadMedia(item.id)

  return (
    <motion.div
      variants={itemVariants}
      className="space-y-2 rounded-lg bg-white p-4 shadow-sm transition-all hover:shadow-lg hover:scale-[1.03] dark:bg-slate-900 dark:border dark:border-slate-700"
    >
      <button
        onClick={() => navigate(`/media/${item.id}`)}
        className="w-full overflow-hidden rounded-md transition-all hover:opacity-80"
      >
        <MediaThumb
          src={api.media.thumbUrl(item.id)}
          alt={item.caption || 'Media'}
          size="md"
        />
      </button>
      {item.caption && (
        <p className="text-xs text-gray-700 dark:text-gray-300 line-clamp-2">{item.caption}</p>
      )}
      <div className="flex items-center justify-between">
        <StatusBadge status={item.status} />
        <button
          onClick={() => download.mutate()}
          disabled={download.isPending}
          className="rounded-md bg-[#229ED9] px-2 py-1 text-xs font-medium text-white transition-all hover:bg-[#1a7aaf] hover:shadow-md hover:scale-105 disabled:opacity-50 active:scale-95"
        >
          {download.isPending ? '...' : 'Get'}
        </button>
      </div>
    </motion.div>
  )
}
