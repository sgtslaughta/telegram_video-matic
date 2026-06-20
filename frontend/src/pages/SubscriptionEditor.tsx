import { useParams, useNavigate } from 'react-router-dom'
import { useSubscription, useCreateSubscription, useUpdateSubscription } from '@/hooks/useSubscriptions'
import { useChannels, useTopics } from '@/hooks/useChannels'
import { useSubscriptionEditor } from '@/hooks/useSubscriptionEditor'
import type * as T from '@/lib/types'
import { toast } from 'sonner'

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
    <div className="space-y-6 p-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">{isNew ? 'New Subscription' : 'Edit Subscription'}</h1>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {isNew ? 'Create a new media subscription' : 'Update subscription settings'}
        </p>
      </div>

      {/* Channel + Topic */}
      <div className="space-y-4 border-b pb-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="channel" className="block text-sm font-medium mb-1">Channel</label>
            <select
              id="channel"
              className="w-full px-3 py-2 border rounded-md bg-background border-gray-300 dark:border-gray-600"
              value={editor.state.channelId || ''}
              onChange={(e) => {
                editor.update('channelId', e.target.value ? parseInt(e.target.value) : null)
                editor.update('topicId', null)
              }}
            >
              <option value="">Select channel</option>
              {channels.data?.map((ch) => (
                <option key={ch.id} value={ch.id}>
                  {ch.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="topic" className="block text-sm font-medium mb-1">Topic</label>
            <select
              id="topic"
              className="w-full px-3 py-2 border rounded-md bg-background border-gray-300 dark:border-gray-600"
              value={editor.state.topicId || ''}
              onChange={(e) => editor.update('topicId', e.target.value ? parseInt(e.target.value) : null)}
              disabled={!editor.state.channelId}
            >
              <option value="">Select topic</option>
              {topics.data?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="space-y-4 border-b pb-6">
        <div>
          <span className="block text-sm font-medium mb-2">Filter Mode</span>
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
                <span className="capitalize">{mode} (whitelist)</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="regex" className="block text-sm font-medium mb-1">Filter Regex</label>
          <textarea
            id="regex"
            value={editor.state.filterRegex}
            onChange={(e) => editor.update('filterRegex', e.target.value)}
            placeholder="e.g., .*\\.mkv$ to match video files"
            className="font-mono text-sm w-full px-3 py-2 border rounded-md bg-background border-gray-300 dark:border-gray-600"
            rows={3}
          />
          <div className="mt-2 flex items-center gap-2">
            {editor.state.filterRegex && (
              <>
                <span className={editor.regexValid ? 'text-green-600 text-lg' : 'text-red-600 text-lg'}>
                  {editor.regexValid ? '✅' : '❌'}
                </span>
                {!editor.regexValid && <span className="text-xs text-red-600">{editor.regexError}</span>}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Schedule */}
      <div className="space-y-4 border-b pb-6">
        <span className="block text-sm font-medium">Schedule Days</span>
        <div className="grid grid-cols-4 gap-3">
          {DAYS.map((day) => (
            <label key={day.value} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={editor.state.scheduleDays.includes(day.value)}
                onChange={() => editor.toggleScheduleDay(day.value)}
                className="w-4 h-4 rounded"
              />
              <span className="text-sm">{day.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Size Bounds */}
      <div className="space-y-4 border-b pb-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="minSize" className="block text-sm font-medium mb-1">Min Size (MB)</label>
            <input
              id="minSize"
              type="number"
              value={editor.state.minSizeMb ?? ''}
              onChange={(e) => editor.update('minSizeMb', e.target.value ? parseFloat(e.target.value) : null)}
              placeholder="0"
              className="w-full px-3 py-2 border rounded-md bg-background border-gray-300 dark:border-gray-600"
            />
          </div>
          <div>
            <label htmlFor="maxSize" className="block text-sm font-medium mb-1">Max Size (MB)</label>
            <input
              id="maxSize"
              type="number"
              value={editor.state.maxSizeMb ?? ''}
              onChange={(e) => editor.update('maxSizeMb', e.target.value ? parseFloat(e.target.value) : null)}
              placeholder="1000"
              className="w-full px-3 py-2 border rounded-md bg-background border-gray-300 dark:border-gray-600"
            />
          </div>
        </div>
      </div>

      {/* Storage & Template */}
      <div className="space-y-4 border-b pb-6">
        <div>
          <label htmlFor="path" className="block text-sm font-medium mb-1">Storage Path</label>
          <input
            id="path"
            value={editor.state.storagePath}
            onChange={(e) => editor.update('storagePath', e.target.value)}
            placeholder="/media/downloads"
            className="w-full px-3 py-2 border rounded-md bg-background border-gray-300 dark:border-gray-600"
          />
        </div>

        <div>
          <label htmlFor="template" className="block text-sm font-medium mb-1">Rename Template</label>
          <input
            id="template"
            value={editor.state.renameTemplate}
            onChange={(e) => editor.update('renameTemplate', e.target.value)}
            placeholder="{channel}/{title}/{season}/{episode}.{ext}"
            className="w-full px-3 py-2 border rounded-md bg-background border-gray-300 dark:border-gray-600"
          />
          <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
            Preview: <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">{previewFilename}</code>
          </p>
        </div>
      </div>

      {/* Advanced */}
      <div className="space-y-4 border-b pb-6">
        <div>
          <label htmlFor="retention" className="block text-sm font-medium mb-1">Retention Days (override global)</label>
          <input
            id="retention"
            type="number"
            value={editor.state.retentionDays ?? ''}
            onChange={(e) => editor.update('retentionDays', e.target.value ? parseInt(e.target.value) : null)}
            placeholder="30"
            className="w-full px-3 py-2 border rounded-md bg-background border-gray-300 dark:border-gray-600"
          />
        </div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={editor.state.seasonDetection}
            onChange={(e) => editor.update('seasonDetection', e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <span className="text-sm">Enable season detection</span>
        </label>
      </div>

      {/* Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="flex-1 px-4 py-2 bg-[#229ED9] text-white rounded-md hover:bg-[#1a7aaf] disabled:opacity-50"
        >
          {isSubmitting ? 'Saving...' : isNew ? 'Create' : 'Update'}
        </button>
        <button
          onClick={() => navigate('/subscriptions')}
          disabled={isSubmitting}
          className="px-4 py-2 border rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
