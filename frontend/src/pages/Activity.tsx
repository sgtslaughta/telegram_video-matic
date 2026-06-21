import { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useEvents } from '@/hooks/useEvents'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { EmptyState } from '@/components/shared/EmptyState'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Combobox } from '@/components/ui/combobox'
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
  debug: 'bg-muted text-foreground',
  info: 'bg-primary/10 text-primary',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-amber-100 text-amber-800',
  error: 'bg-red-100 text-red-800',
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
        <h1 className="text-3xl font-bold text-foreground">Activity</h1>
        <p className="mt-2 text-muted-foreground">View and filter system events</p>
      </div>

      {/* Filters */}
      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <Card>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Level</Label>
                <Combobox
                  value={levelFilter}
                  onChange={(v) => { setLevelFilter(v); setOffset(0) }}
                  placeholder="All Levels"
                  options={EVENT_LEVELS.map((level) => ({ value: level.value, label: level.label }))}
                />
              </div>

              <div className="space-y-2">
                <Label>Kind</Label>
                <Combobox
                  value={kindFilter}
                  onChange={(v) => { setKindFilter(v); setOffset(0) }}
                  placeholder="All Kinds"
                  options={EVENT_KINDS.map((kind) => ({ value: kind.value, label: kind.label }))}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Events Table */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Events</CardTitle>
          </CardHeader>
          <CardContent>
            {events.isLoading ? (
              <div className="py-8 text-center text-muted-foreground">
                Loading...
              </div>
            ) : events.data && events.data.length > 0 ? (
              <>
                <motion.div
                  className="space-y-3 mb-4"
                  variants={containerVariants}
                  initial="hidden"
                  animate="visible"
                >
                  {events.data.map((event) => (
                    <motion.div
                      key={event.id}
                      variants={itemVariants}
                      className="flex items-start gap-3 p-3 rounded-lg border border-border transition-colors hover:bg-muted/50"
                    >
                      {/* Level Badge */}
                      <div className="flex-shrink-0 pt-0.5">
                        <Badge className={LEVEL_COLORS[event.level as T.EventLevel] || LEVEL_COLORS['debug']}>
                          {event.level}
                        </Badge>
                      </div>

                      {/* Message and Details */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm">{event.message}</p>
                        <div className="mt-1 flex gap-3 text-xs text-muted-foreground">
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
                <div className="flex items-center justify-between pt-4 border-t border-border">
                  <Button
                    onClick={handlePrevious}
                    disabled={!canGoPrevious}
                    variant="outline"
                    size="sm"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>

                  <span className="text-sm text-muted-foreground">
                    Offset: {offset}
                  </span>

                  <Button
                    onClick={handleNext}
                    disabled={!canGoNext}
                    variant="outline"
                    size="sm"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </>
            ) : (
              <EmptyState
                title="No events"
                message="Events will appear here as system activity occurs."
              />
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}
