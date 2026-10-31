import type { PreviewParams } from '@/hooks/useSubscriptionTools'
import type { SectionProps } from './Section'

export function previewParams(s: SectionProps['s'], regexValid: boolean): PreviewParams | null {
  if (!s.channelId || !regexValid) return null
  return {
    channel_id: s.channelId,
    topic_id: s.topicId,
    filter_regex: s.filterRegex || undefined,
    filter_mode: s.filterMode,
    min_size_mb: s.minSizeMb,
    max_size_mb: s.maxSizeMb,
    date_from: s.dateFrom ? new Date(s.dateFrom + 'T00:00:00').toISOString() : null,
    date_to: !s.ongoing && s.dateTo ? new Date(s.dateTo + 'T23:59:59').toISOString() : null,
    schedule_days: s.checkFrequency === 'scheduled' ? s.scheduleDays : undefined,
  }
}
