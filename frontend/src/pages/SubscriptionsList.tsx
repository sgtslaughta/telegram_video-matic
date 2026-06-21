import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Trash2, Edit, RefreshCw, Power, Search } from 'lucide-react'
import {
  useSubscriptions,
  useUpdateSubscription,
  useDeleteSubscription,
  useScanSubscription,
} from '@/hooks/useSubscriptions'
import { useChannels } from '@/hooks/useChannels'
import { ConfirmDialog, EmptyState, StatusBadge } from '@/components/shared'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import type { SubscriptionRead } from '@/lib/types'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
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

export default function SubscriptionsList() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const q = search.toLowerCase()
  const { data: subscriptions = [], isLoading } = useSubscriptions()
  const { data: channels } = useChannels()
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [scanId, setScanId] = useState<number | null>(null)
  const [toggleId, setToggleId] = useState<number | null>(null)

  // ponytail: hooks called once per sub at top level
  const deleteMut = useDeleteSubscription(deleteId || 0)
  const scanMut = useScanSubscription(scanId || 0)
  const updateMut = useUpdateSubscription(toggleId || 0)

  const channelTitle = (id: number) => channels?.find(c => c.id === id)?.title ?? `Channel ${id}`

  const handleToggle = (sub: SubscriptionRead) => {
    setToggleId(sub.id)
    updateMut.mutate({ enabled: !sub.enabled })
  }

  const handleDelete = async () => {
    if (deleteId) {
      await deleteMut.mutateAsync()
      setDeleteId(null)
    }
  }

  const handleScan = (id: number) => {
    setScanId(id)
    scanMut.mutate()
  }

  const truncate = (text: string, len: number = 40) =>
    text.length > len ? text.slice(0, len) + '...' : text

  if (isLoading) return <div className="p-6">Loading...</div>

  const visible = (subscriptions ?? []).filter(
    (s) => !q || channelTitle(s.channel_id).toLowerCase().includes(q)
  )

  return (
    <motion.div
      className="space-y-6 p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Subscriptions</h1>
        <Button
          onClick={() => navigate('/subscriptions/new')}
          className="bg-primary hover:bg-primary/90"
        >
          Add Subscription
        </Button>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search subscriptions…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-8"
        />
      </div>

      {visible.length === 0 ? (
        <EmptyState
          title="No subscriptions yet"
          message="Create your first subscription to start downloading media."
          action={{
            label: 'Add Subscription',
            onClick: () => navigate('/subscriptions/new'),
          }}
        />
      ) : (
        <motion.div
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {visible.map((sub) => (
            <motion.div
              key={sub.id}
              variants={itemVariants}
              className="transition-all hover:shadow-lg hover:scale-[1.02]"
            >
              <Card className="flex flex-col h-full">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-base">{sub.name || sub.channel_title || channelTitle(sub.channel_id)}</CardTitle>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {sub.name ? `${sub.channel_title || channelTitle(sub.channel_id)}` : null}
                        {sub.name && (sub.topic_title || sub.topic_id) ? ' · ' : ''}
                        {sub.topic_title || (sub.topic_id ? `Topic ${sub.topic_id}` : '')}
                      </p>
                    </div>
                    <StatusBadge status={sub.enabled ? 'enabled' : 'disabled'} />
                  </div>
                </CardHeader>

                <CardContent className="flex-1 space-y-3">
                  {sub.filter_regex && (
                    <p className="text-xs text-muted-foreground">
                      Filter: {truncate(sub.filter_regex)}
                    </p>
                  )}

                  <p className="text-xs text-muted-foreground">
                    Last scan:{' '}
                    {sub.updated_at
                      ? new Date(sub.updated_at).toLocaleDateString()
                      : 'Never'}
                  </p>

                  <div className="flex flex-wrap gap-2 pt-3">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          variant={sub.enabled ? 'secondary' : 'outline'}
                          onClick={() => handleToggle(sub)}
                          className="flex-1"
                        >
                          <Power className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        {sub.enabled ? 'Disable' : 'Enable'}
                      </TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          className="flex-1 bg-primary hover:bg-primary/90"
                          onClick={() => navigate(`/subscriptions/${sub.id}`)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Edit</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleScan(sub.id)}
                          className="flex-1"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Scan</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => setDeleteId(sub.id)}
                          className="flex-1"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Delete</TooltipContent>
                    </Tooltip>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}

      <ConfirmDialog
        isOpen={deleteId !== null}
        title="Delete Subscription"
        description="This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </motion.div>
  )
}
