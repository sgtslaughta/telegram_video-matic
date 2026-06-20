import { useParams, useNavigate } from 'react-router-dom'
import { useSubscription, useCreateSubscription, useUpdateSubscription } from '@/hooks/useSubscriptions'
import { useChannels, useTopics } from '@/hooks/useChannels'
import { useSubscriptionEditor } from '@/hooks/useSubscriptionEditor'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type * as T from '@/lib/types'

const DAYS = [
  { value: 'mon', label: 'Monday' },
  { value: 'tue', label: 'Tuesday' },
  { value: 'wed', label: 'Wednesday' },
  { value: 'thu', label: 'Thursday' },
  { value: 'fri', label: 'Friday' },
  { value: 'sat', label: 'Saturday' },
  { value: 'sun', label: 'Sunday' },
]

const SAMPLE_PREVIEW = {
  channel: 'TestChannel',
  title: 'Sample Video',
  season: 1,
  episode: 5,
  ext: 'mp4',
}

export default function SubscriptionEditor() {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const isNew = !id || id === 'new'

  const channels = useChannels()
  const existingSubscription = useSubscription(isNew ? 0 : parseInt(id!))
  const topics = useTopics(existingSubscription.data?.channel_id ?? null)
  const createMutation = useCreateSubscription()
  const updateMutation = useUpdateSubscription(isNew ? 0 : parseInt(id!))

  const editor = useSubscriptionEditor(
    existingSubscription.data
      ? {
          channelId: existingSubscription.data.channel_id,
          topicId: existingSubscription.data.topic_id ?? null,
          name: existingSubscription.data.storage_path || '',
          filterMode: (existingSubscription.data.filter_mode as 'include' | 'exclude') || 'include',
          filterRegex: existingSubscription.data.filter_regex || '',
          scheduleDays: existingSubscription.data.schedule_days || [],
          minSizeMb: existingSubscription.data.min_size_mb ?? null,
          maxSizeMb: existingSubscription.data.max_size_mb ?? null,
          storagePath: existingSubscription.data.storage_path,
          renameTemplate: existingSubscription.data.rename_template,
          retentionDays: existingSubscription.data.retention_days ?? null,
          seasonDetection: existingSubscription.data.season_detection || false,
        }
      : undefined
  )

  const previewFilename = editor.state.renameTemplate
    ? editor.state.renameTemplate
        .replace('{channel}', SAMPLE_PREVIEW.channel)
        .replace('{title}', SAMPLE_PREVIEW.title)
        .replace('{season}', String(SAMPLE_PREVIEW.season))
        .replace('{episode}', String(SAMPLE_PREVIEW.episode))
        .replace('{ext}', SAMPLE_PREVIEW.ext)
    : 'preview'

  const handleSubmit = async () => {
    if (!editor.state.channelId || !editor.state.topicId) {
      toast.error('Please select channel and topic')
      return
    }
    if (!editor.state.storagePath) {
      toast.error('Please enter storage path')
      return
    }
    if (!editor.state.renameTemplate) {
      toast.error('Please enter rename template')
      return
    }
    if (!editor.regexValid) {
      toast.error('Invalid regex pattern')
      return
    }

    const payload: T.SubscriptionCreateRequest = {
      channel_id: editor.state.channelId,
      topic_id: editor.state.topicId,
      enabled: true,
      storage_path: editor.state.storagePath,
      rename_template: editor.state.renameTemplate,
      filter_regex: editor.state.filterRegex || undefined,
      filter_mode: editor.state.filterMode,
      mode: 'immediate',
      schedule_days: editor.state.scheduleDays.length > 0 ? editor.state.scheduleDays : undefined,
      min_size_mb: editor.state.minSizeMb,
      max_size_mb: editor.state.maxSizeMb,
      retention_days: editor.state.retentionDays,
      season_detection: editor.state.seasonDetection,
    }

    try {
      if (isNew) {
        await createMutation.mutateAsync(payload)
        toast.success('Subscription created')
      } else {
        const updatePayload: T.SubscriptionUpdateRequest = {
          storage_path: editor.state.storagePath,
          rename_template: editor.state.renameTemplate,
          filter_regex: editor.state.filterRegex || undefined,
          filter_mode: editor.state.filterMode,
          schedule_days: editor.state.scheduleDays.length > 0 ? editor.state.scheduleDays : undefined,
          min_size_mb: editor.state.minSizeMb,
          max_size_mb: editor.state.maxSizeMb,
          retention_days: editor.state.retentionDays,
          season_detection: editor.state.seasonDetection,
        }
        await updateMutation.mutateAsync(updatePayload)
        toast.success('Subscription updated')
      }
      navigate('/subscriptions')
    } catch (e) {
      toast.error((e as Error).message)
    }
  }

  const isLoading = !isNew && existingSubscription.isLoading
  const isSubmitting = createMutation.isPending || updateMutation.isPending

  if (isLoading) {
    return <div className="p-6">Loading...</div>
  }

  return (
    <div className="space-y-6 p-6 max-w-2xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold">{isNew ? 'New Subscription' : 'Edit Subscription'}</h1>
        <p className="text-sm text-muted-foreground">
          {isNew ? 'Create a new media subscription' : 'Update subscription settings'}
        </p>
      </div>

      {/* Channel + Topic */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Channel & Topic</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="channel">Channel</Label>
              <Select value={editor.state.channelId?.toString() || ''} onValueChange={(v) => {
                editor.update('channelId', v ? parseInt(v) : null)
                editor.update('topicId', null)
              }}>
                <SelectTrigger id="channel">
                  <SelectValue placeholder="Select channel" />
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

            <div className="space-y-2">
              <Label htmlFor="topic">Topic</Label>
              <Select value={editor.state.topicId?.toString() || ''} onValueChange={(v) => editor.update('topicId', v ? parseInt(v) : null)} disabled={!editor.state.channelId}>
                <SelectTrigger id="topic">
                  <SelectValue placeholder="Select topic" />
                </SelectTrigger>
                <SelectContent>
                  {topics.data?.map((t) => (
                    <SelectItem key={t.id} value={t.id.toString()}>
                      {t.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filter */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filter</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Filter Mode</Label>
            <div className="flex gap-4">
              {['include', 'exclude'].map((mode) => (
                <label key={mode} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="filterMode"
                    value={mode}
                    checked={editor.state.filterMode === mode}
                    onChange={(e) => editor.update('filterMode', e.target.value as any)}
                  />
                  <span className="text-sm capitalize">{mode}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="regex">Filter Regex</Label>
            <Textarea
              id="regex"
              value={editor.state.filterRegex}
              onChange={(e) => editor.update('filterRegex', e.target.value)}
              placeholder="e.g., .*\\.mkv$ to match video files"
              className="font-mono text-sm"
              rows={3}
            />
            <div className="flex items-center gap-2 mt-2">
              {editor.state.filterRegex && (
                <>
                  <span className={editor.regexValid ? 'text-green-600' : 'text-red-600'}>
                    {editor.regexValid ? '✅ Valid' : '❌ Invalid'}
                  </span>
                  {!editor.regexValid && <span className="text-xs text-red-600">{editor.regexError}</span>}
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Schedule */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Label>Schedule Days</Label>
            <div className="grid grid-cols-4 gap-3">
              {DAYS.map((day) => (
                <label key={day.value} className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={editor.state.scheduleDays.includes(day.value)}
                    onCheckedChange={() => editor.toggleScheduleDay(day.value)}
                  />
                  <span className="text-sm">{day.label}</span>
                </label>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Size Bounds */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Size Bounds</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="minSize">Min Size (MB)</Label>
              <Input
                id="minSize"
                type="number"
                value={editor.state.minSizeMb ?? ''}
                onChange={(e) => editor.update('minSizeMb', e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="0"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="maxSize">Max Size (MB)</Label>
              <Input
                id="maxSize"
                type="number"
                value={editor.state.maxSizeMb ?? ''}
                onChange={(e) => editor.update('maxSizeMb', e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="1000"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Storage & Template */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Storage & Naming</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="path">Storage Path</Label>
            <Input
              id="path"
              value={editor.state.storagePath}
              onChange={(e) => editor.update('storagePath', e.target.value)}
              placeholder="/media/downloads"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="template">Rename Template</Label>
            <Input
              id="template"
              value={editor.state.renameTemplate}
              onChange={(e) => editor.update('renameTemplate', e.target.value)}
              placeholder="{channel}/{title}/{season}/{episode}.{ext}"
            />
            <div className="mt-2 text-xs text-muted-foreground">
              Preview: <Badge variant="outline" className="inline-block mt-1">{previewFilename}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Advanced */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Advanced</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="retention">Retention Days (override global)</Label>
            <Input
              id="retention"
              type="number"
              value={editor.state.retentionDays ?? ''}
              onChange={(e) => editor.update('retentionDays', e.target.value ? parseInt(e.target.value) : null)}
              placeholder="30"
            />
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <Checkbox
              checked={editor.state.seasonDetection}
              onCheckedChange={(checked) => editor.update('seasonDetection', checked as boolean)}
            />
            <span className="text-sm">Enable season detection</span>
          </label>
        </CardContent>
      </Card>

      {/* Buttons */}
      <div className="flex gap-3">
        <Button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="flex-1 bg-primary hover:bg-primary/90"
        >
          {isSubmitting ? 'Saving...' : isNew ? 'Create' : 'Update'}
        </Button>
        <Button
          onClick={() => navigate('/subscriptions')}
          disabled={isSubmitting}
          variant="outline"
        >
          Cancel
        </Button>
      </div>
    </div>
  )
}
