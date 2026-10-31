import { useState } from 'react'
import { X } from 'lucide-react'
import { Combobox } from '@/components/ui/combobox'
import { Input } from '@/components/ui/input'
import { MediaThumb } from '@/components/shared/MediaThumb'
import { useRugbyPreview } from '@/hooks/useRugby'
import type { RugbyLeague } from '@/lib/types'
import { Field, Section, ToggleRow } from './Section'
import { DEFAULT_TEMPLATE, renderTemplate } from './template'

interface Props {
  allLeagues: RugbyLeague[]
  on: boolean
  setOn: (v: boolean) => void
  leagues: number[]
  setLeagues: (v: number[]) => void
  template: string
}

export function RugbySection({ allLeagues, on, setOn, leagues, setLeagues, template }: Props) {
  const league = leagues[0] ?? null  // preview tests against the first league
  const name = (id: number) => allLeagues.find((l) => l.id === id)?.name ?? `League ${id}`
  const [filename, setFilename] = useState('Sale Sharks v Gloucester.mp4')
  const preview = useRugbyPreview()
  const r = preview.data
  return (
    <Section title="Rugby league" description="Match detection and file name enrichment.">
      <ToggleRow id="rugbyToggle" label="Rugby enrichment" hint="Detect matches and add teams to file names."
        checked={on} onChange={setOn} />
      {on && (
        <>
          <Field label="Leagues" hint="Add every competition this topic posts, e.g. Champions Cup and Challenge Cup.">
            {leagues.length > 0 && (
              <ul className="mb-2 flex flex-wrap gap-1.5">
                {leagues.map((id) => (
                  <li key={id} className="flex items-center gap-1 rounded-full bg-brand/10 py-0.5 pl-2.5 pr-1 text-[12px] font-medium text-brand">
                    {name(id)}
                    <button type="button" aria-label={`Remove ${name(id)}`} onClick={() => setLeagues(leagues.filter((x) => x !== id))}
                      className="rounded-full p-0.5 hover:bg-brand/20"><X className="h-3 w-3" /></button>
                  </li>
                ))}
              </ul>
            )}
            <Combobox value="" onChange={(v) => { if (v) setLeagues([...leagues, parseInt(v)]) }}
              placeholder={leagues.length ? 'Add another league' : 'Add a league'}
              options={allLeagues.filter((l) => !leagues.includes(l.id)).map((l) => ({ value: l.id.toString(), label: l.name }))} />
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
