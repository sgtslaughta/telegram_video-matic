import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Download } from 'lucide-react'
import { useChannels, useTopics } from '@/hooks/useChannelsTopics'
import { useMedia, useDownloadMedia } from '@/hooks/useMedia'
import { MediaThumb } from '@/components/shared/MediaThumb'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
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
  const [params] = useSearchParams()
  const q = (params.get('q') ?? '').toLowerCase()
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
        <h1 className="text-2xl font-bold text-foreground">Browse Media</h1>
        <p className="mt-1 text-sm text-muted-foreground">Filter and download media from your channels</p>
      </div>

      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <Card>
          <CardContent className="pt-6 space-y-4">
            <div className="space-y-2">
              <Label>Channel</Label>
              <Select value={selectedChannel?.toString() || ''} onValueChange={(v) => {
                const id = v ? parseInt(v) : null
                setSelectedChannel(id)
                setSelectedTopic(null)
              }} disabled={channels.isLoading}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a channel..." />
                </SelectTrigger>
                <SelectContent>
                  {channels.data?.map((ch) => (
                    <SelectItem key={ch.id} value={ch.id.toString()}>
                      {ch.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedChannel && (
              <motion.div
                className="space-y-2"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <Label>Topic (optional)</Label>
                <Select value={selectedTopic?.toString() || ''} onValueChange={(v) => {
                  const id = v ? parseInt(v) : null
                  setSelectedTopic(id)
                }} disabled={topics.isLoading}>
                  <SelectTrigger>
                    <SelectValue placeholder="All topics" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All topics</SelectItem>
                    {topics.data?.map((t) => (
                      <SelectItem key={t.id} value={t.id.toString()}>
                        {t.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </motion.div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {!selectedChannel ? (
        <EmptyState
          title="Select a channel"
          message="Choose a channel above to browse and download media"
        />
      ) : media.isLoading ? (
        <div className="text-center py-12 text-muted-foreground">Loading media...</div>
      ) : !media.data?.length ? (
        <EmptyState
          title="No media found"
          message="This channel has no media available"
        />
      ) : (
        <>
          {(() => {
            const visible = (media.data ?? []).filter(
              (item) => !q || (item.caption ?? '').toLowerCase().includes(q)
            )
            return visible.length === 0 ? (
              <EmptyState
                title="No media matches"
                message="Try a different search"
              />
            ) : (
              <motion.div
                className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
              >
                {visible.map((item) => (
                  <MediaCard key={item.id} item={item} />
                ))}
              </motion.div>
            )
          })()}
        </>
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
      className="transition-all hover:shadow-lg hover:scale-[1.03]"
    >
      <Card className="h-full flex flex-col">
        <button
          onClick={() => navigate(`/media/${item.id}`)}
          className="w-full overflow-hidden rounded-t-lg transition-all hover:opacity-80"
        >
          <MediaThumb
            src={api.media.thumbUrl(item.id)}
            alt={item.caption || 'Media'}
            size="md"
          />
        </button>
        <CardContent className="flex-1 flex flex-col p-3 space-y-3">
          {item.caption && (
            <p className="text-xs text-foreground line-clamp-2">{item.caption}</p>
          )}
          <div className="flex items-center justify-between mt-auto">
            <StatusBadge status={item.status} />
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="sm"
                  onClick={() => download.mutate()}
                  disabled={download.isPending}
                  className="bg-primary hover:bg-primary/90"
                >
                  <Download className="h-3 w-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Download</TooltipContent>
            </Tooltip>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
