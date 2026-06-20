import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChannels, useTopics } from '@/hooks/useChannelsTopics'
import { useMedia, useDownloadMedia } from '@/hooks/useMedia'
import { MediaThumb } from '@/components/shared/MediaThumb'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import * as api from '@/lib/api'

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
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Browse Media</h1>
        <p className="mt-1 text-sm text-gray-600">Filter and download media from your channels</p>
      </div>

      <div className="space-y-4 rounded-lg bg-white p-6 shadow-sm">
        <div>
          <label className="block text-sm font-medium text-gray-700">Channel</label>
          <select
            value={selectedChannel || ''}
            onChange={handleChannelChange}
            className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
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
          <div>
            <label className="block text-sm font-medium text-gray-700">Topic (optional)</label>
            <select
              value={selectedTopic || ''}
              onChange={handleTopicChange}
              className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              disabled={topics.isLoading}
            >
              <option value="">All topics</option>
              {topics.data?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.title}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {!selectedChannel ? (
        <EmptyState
          title="Select a channel"
          message="Choose a channel above to browse and download media"
        />
      ) : media.isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading media...</div>
      ) : !media.data?.length ? (
        <EmptyState
          title="No media found"
          message="This channel has no media available"
        />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {media.data.map((item) => (
            <MediaCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}

function MediaCard({ item }: { item: any }) {
  const navigate = useNavigate()
  const download = useDownloadMedia(item.id)

  return (
    <div className="space-y-2 rounded-lg bg-white p-4 shadow-sm">
      <button
        onClick={() => navigate(`/media/${item.id}`)}
        className="w-full overflow-hidden rounded-md hover:opacity-80"
      >
        <MediaThumb
          src={api.media.thumbUrl(item.id)}
          alt={item.caption || 'Media'}
          size="md"
        />
      </button>
      {item.caption && (
        <p className="text-xs text-gray-700 line-clamp-2">{item.caption}</p>
      )}
      <div className="flex items-center justify-between">
        <StatusBadge status={item.status} />
        <button
          onClick={() => download.mutate()}
          disabled={download.isPending}
          className="rounded-md bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {download.isPending ? '...' : 'Get'}
        </button>
      </div>
    </div>
  )
}
