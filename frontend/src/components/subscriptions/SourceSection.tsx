import { useChannels, useTopics } from '@/hooks/useChannels'
import { Input } from '@/components/ui/input'
import { Combobox } from '@/components/ui/combobox'
import { Field, Section, type SectionProps } from './Section'

export function SourceSection({ s, update }: SectionProps) {
  const channels = useChannels()
  const topics = useTopics(s.channelId)
  return (
    <Section title="Source" description="Where new videos are picked up from.">
      <Field label="Name" htmlFor="name" hint="Shown in the list. Defaults to the channel name.">
        <Input id="name" value={s.name} onChange={(e) => update('name', e.target.value)} placeholder="e.g. Premiership matches" />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Channel">
          <Combobox
            value={s.channelId?.toString() || ''}
            onChange={(v) => { update('channelId', v ? parseInt(v) : null); update('topicId', null) }}
            placeholder="Select channel" searchPlaceholder="Search channels…"
            options={(channels.data ?? []).map((ch) => ({ value: ch.id.toString(), label: ch.title }))}
          />
        </Field>
        <Field label="Topic" hint="The forum topic to capture.">
          <Combobox
            value={s.topicId?.toString() || ''}
            onChange={(v) => update('topicId', v ? parseInt(v) : null)}
            disabled={!s.channelId} placeholder="Select topic" searchPlaceholder="Search topics…"
            options={(topics.data ?? []).map((t) => ({ value: t.id.toString(), label: t.title }))}
          />
        </Field>
      </div>
    </Section>
  )
}
