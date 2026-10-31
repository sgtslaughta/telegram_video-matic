import { useState } from 'react'
import { Combobox } from '@/components/ui/combobox'
import { Input } from '@/components/ui/input'
import { MediaThumb } from '@/components/shared/MediaThumb'
import { useRugbyPreview } from '@/hooks/useRugby'
import type { RugbyLeague } from '@/lib/types'
import { Field, Section, ToggleRow } from './Section'
import { DEFAULT_TEMPLATE, renderTemplate } from './template'

interface Props {
  leagues: RugbyLeague[]
  on: boolean
  setOn: (v: boolean) => void
  league: number | null
  setLeague: (v: number | null) => void
  template: string
}

export function RugbySection({ leagues, on, setOn, league, setLeague, template }: Props) {
  const [filename, setFilename] = useState('Sale Sharks v Gloucester.mp4')
  const preview = useRugbyPreview()
  const r = preview.data
  return (
    <Section title="Rugby league" description="Match detection and file name enrichment.">
      <ToggleRow id="rugbyToggle" label="Rugby enrichment" hint="Detect matches and add teams to file names."
        checked={on} onChange={setOn} />
      {on && (
        <>
          <Field label="League">
            <Combobox value={league?.toString() || ''} onChange={(v) => setLeague(v ? parseInt(v) : null)} placeholder="None"
              options={[{ value: '', label: 'None' }, ...leagues.map((l) => ({ value: l.id.toString(), label: l.name }))]} />
          </Field>
          {league && (
            <div className="space-y-3 rounded-md border border-border bg-muted/40 p-3">
              <Field label="Test file name" htmlFor="testFilename">
                <Input id="testFilename" value={filename} placeholder="e.g. Sale Sharks v Gloucester.mp4"
                  onChange={(e) => { setFilename(e.target.value); preview.mutate({ leagueId: league, text: e.target.value }) }} />
              </Field>
              {r && (
                <div className="space-y-2 text-[12px]">
                  {r.matched ? (
                    <>
                      <p className="font-medium text-ok">Confident match ({Math.round(r.confidence * 100)}%)</p>
                      <div className="flex items-center gap-2">
                        {r.home_badge && <MediaThumb src={r.home_badge} alt={r.home || ''} size="sm" />}
                        {r.away_badge && <MediaThumb src={r.away_badge} alt={r.away || ''} size="sm" />}
                        <span>{r.home} vs {r.away}</span>
                      </div>
                      {r.tokens && <p className="font-mono">{renderTemplate(template || DEFAULT_TEMPLATE, r.tokens)}</p>}
                    </>
                  ) : <p className="text-warn">No confident match, so the original file name is kept.</p>}
                  <p className="text-muted-foreground">{r.fixtures_count} fixtures, {r.teams_count} teams loaded</p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </Section>
  )
}
