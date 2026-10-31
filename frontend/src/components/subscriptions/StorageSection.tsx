import FolderPicker from '@/components/FolderPicker'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Field, Section, ToggleRow, type SectionProps } from './Section'
import { DEFAULT_TEMPLATE, sampleName } from './template'

export function StorageSection({ s, update }: SectionProps) {
  return (
    <Section title="Storage and naming" description="Where files go and what they are called.">
      <Field label="Storage path" htmlFor="path" hint="Base folder on the server. Must be writable.">
        <FolderPicker id="path" value={s.storagePath} onChange={(p) => update('storagePath', p)} placeholder="/media/downloads" />
      </Field>
      <Field label="Naming template" htmlFor="template"
        hint="Tokens: {channel} {topic} {title} {season} {episode} {date} {original} {ext}. Slashes create folders.">
        <Input id="template" value={s.renameTemplate} onChange={(e) => update('renameTemplate', e.target.value)} placeholder={DEFAULT_TEMPLATE} />
        <div className="text-[12px] text-muted-foreground">Preview <Badge variant="outline" className="ml-1 font-mono">{sampleName(s.renameTemplate)}</Badge></div>
      </Field>
      <ToggleRow id="seasonDet" label="Season detection" hint="Detect SxxExx in file names to fill {season} and {episode}."
        checked={s.seasonDetection} onChange={(c) => update('seasonDetection', c)} />
      <ToggleRow id="jellyfin" label="Jellyfin metadata" hint="Write .nfo sidecars, plus season folders when episodes are detected."
        checked={s.jellyfinMetadata} onChange={(c) => update('jellyfinMetadata', c)} />
    </Section>
  )
}
