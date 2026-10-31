import { useFilterPreview } from '@/hooks/useSubscriptionTools'
import { FilterFields } from './FilterFields'
import { FilterPreview } from './FilterPreview'
import { Section, type SectionProps } from './Section'
import { WindowFields } from './WindowFields'
import { previewParams } from './previewParams'

type Props = SectionProps & { regexValid: boolean; regexError?: string | null; toggleDay: (d: string) => void }

export function WhatToDownload({ regexValid, regexError, toggleDay, ...p }: Props) {
  const preview = useFilterPreview(previewParams(p.s, regexValid))
  const bad = (preview.error as (Error & { status?: number }) | null)?.status === 400 ? preview.error!.message : null
  return (
    <Section title="What to download" description="Filter, size limits, date window and schedule.">
      <FilterFields {...p} regexValid={regexValid} regexError={regexError} serverError={bad} />
      <WindowFields {...p} toggleDay={toggleDay} />
      <FilterPreview items={preview.data} loading={preview.isFetching} idle={!p.s.channelId} />
    </Section>
  )
}
