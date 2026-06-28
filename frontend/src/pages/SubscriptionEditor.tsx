import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Info } from 'lucide-react'
import { useSubscription, useCreateSubscription, useUpdateSubscription } from '@/hooks/useSubscriptions'
import { useChannels, useTopics } from '@/hooks/useChannels'
import { useSubscriptionEditor } from '@/hooks/useSubscriptionEditor'
import { useRugbyLeagues, useSetSubscriptionLeague, useSubscriptionLeague, useRugbyPreview } from '@/hooks/useRugby'
import { usePlugins } from '@/hooks/usePlugins'
import { MediaThumb } from '@/components/shared/MediaThumb'
import FolderPicker from '@/components/FolderPicker'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Combobox } from '@/components/ui/combobox'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import type * as T from '@/lib/types'

const DAYS = [
  { value: 'mon', label: 'Mon' }, { value: 'tue', label: 'Tue' },
  { value: 'wed', label: 'Wed' }, { value: 'thu', label: 'Thu' },
  { value: 'fri', label: 'Fri' }, { value: 'sat', label: 'Sat' },
  { value: 'sun', label: 'Sun' },
]

const SAMPLE = { channel: 'RugbyChannel', title: 'Final Match', season: 1, episode: 5, ext: 'mp4' }
const DEFAULT_TEMPLATE = '{channel}/{title}{ext}'

// ponytail: simple token replacement for preview rendering
function renderTemplate(template: string, tokens: Record<string, string | undefined>): string {
  let result = template
  result = result.replaceAll('{rugby_league}', tokens.rugby_league || '')
  result = result.replaceAll('{rugby_season}', tokens.rugby_season || '')
  result = result.replaceAll('{rugby_round}', tokens.rugby_round || '')
  result = result.replaceAll('{home}', tokens.home || '')
  result = result.replaceAll('{away}', tokens.away || '')
  result = result.replaceAll('{rugby_sport}', tokens.rugby_sport || '')
  result = result.replaceAll('{ext}', '.mp4')
  return result
}

function InfoTip({ text }: { text: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button type="button" tabIndex={-1} className="text-muted-foreground hover:text-foreground" aria-label="Help">
          <Info className="h-3.5 w-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs text-sm">{text}</TooltipContent>
    </Tooltip>
  )
}

function FieldLabel({ children, tip, htmlFor }: { children: React.ReactNode; tip: string; htmlFor?: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <Label htmlFor={htmlFor}>{children}</Label>
      <InfoTip text={tip} />
    </div>
  )
}

export default function SubscriptionEditor() {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const isNew = !id || id === 'new'

  const channels = useChannels()
  const existingSubscription = useSubscription(isNew ? 0 : parseInt(id!))
  const createMutation = useCreateSubscription()
  const updateMutation = useUpdateSubscription(isNew ? 0 : parseInt(id!))

  const editor = useSubscriptionEditor(
    existingSubscription.data
      ? {
          channelId: existingSubscription.data.channel_id,
          topicId: existingSubscription.data.topic_id ?? null,
          name: existingSubscription.data.name || '',
          filterMode: (existingSubscription.data.filter_mode as 'include' | 'exclude') || 'include',
          filterRegex: existingSubscription.data.filter_regex || '',
          checkFrequency: existingSubscription.data.check_frequency || '5m',
          scheduleDays: existingSubscription.data.schedule_days || [],
          minSizeMb: existingSubscription.data.min_size_mb ?? null,
          maxSizeMb: existingSubscription.data.max_size_mb ?? null,
          maxTotalGb: existingSubscription.data.max_total_gb ?? null,
          dateFrom: existingSubscription.data.date_from?.slice(0, 10) || '',
          dateTo: existingSubscription.data.date_to?.slice(0, 10) || '',
          ongoing: !existingSubscription.data.date_to,
          storagePath: existingSubscription.data.storage_path,
          renameTemplate: existingSubscription.data.rename_template,
          retentionDays: existingSubscription.data.retention_days ?? null,
          seasonDetection: existingSubscription.data.season_detection || false,
          jellyfinMetadata: existingSubscription.data.jellyfin_metadata || false,
        }
      : undefined,
    existingSubscription.data?.id ?? (isNew ? 'new' : 'loading')
  )
  const s = editor.state

  const topics = useTopics(s.channelId)
  const { data: plugins } = usePlugins()
  const rugbyEnabled = plugins?.find((p) => p.name === 'rugby')?.enabled ?? false
  const { data: rugbyLeagues } = useRugbyLeagues()
  const [selectedLeague, setSelectedLeague] = useState<number | null>(null)
  const [rugbyOn, setRugbyOn] = useState(true)
  const [testFilename, setTestFilename] = useState('Sale Sharks v Gloucester.mp4')
  const setSubscriptionLeague = useSetSubscriptionLeague()
  const previewMutation = useRugbyPreview()

  // Update selectedLeague when turning rugby off/on
  useEffect(() => {
    if (!rugbyOn) setSelectedLeague(null)
  }, [rugbyOn])

  // Preselect the saved league when editing an existing subscription.
  const { data: savedLeague } = useSubscriptionLeague(isNew ? null : parseInt(id!))
  useEffect(() => {
    if (savedLeague?.league_id != null) setSelectedLeague(savedLeague.league_id)
  }, [savedLeague])

  // Regex tester — mirrors backend re.search (substring, case-insensitive).
  const [testStr, setTestStr] = useState('')
  let testMatch: RegExpMatchArray | null = null
  if (s.filterRegex && editor.regexValid && testStr) {
    try { testMatch = testStr.match(new RegExp(s.filterRegex, 'i')) } catch { testMatch = null }
  }

  const previewFilename = (s.renameTemplate || DEFAULT_TEMPLATE)
    .replaceAll('{channel}', SAMPLE.channel)
    .replaceAll('{topic}', 'General')
    .replaceAll('{title}', SAMPLE.title)
    .replaceAll('{season}', String(SAMPLE.season).padStart(2, '0'))
    .replaceAll('{episode}', String(SAMPLE.episode).padStart(2, '0'))
    .replaceAll('{date}', '2026-06-20')
    .replaceAll('{original}', 'Final Match.mp4')
    .replaceAll('{ext}', SAMPLE.ext)

  const handleSubmit = async () => {
    if (!s.channelId || !s.topicId) return toast.error('Select channel and topic')
    if (!s.storagePath) return toast.error('Enter a storage path')
    if (!s.renameTemplate) return toast.error('Enter a naming template')
    if (!editor.regexValid) return toast.error('Fix the filter regex first')

    const tf = {
      date_from: s.dateFrom ? new Date(s.dateFrom + 'T00:00:00').toISOString() : null,
      date_to: !s.ongoing && s.dateTo ? new Date(s.dateTo + 'T23:59:59').toISOString() : null,
    }
    const common = {
      name: s.name || undefined,
      storage_path: s.storagePath,
      rename_template: s.renameTemplate,
      filter_regex: s.filterRegex || undefined,
      filter_mode: s.filterMode,
      check_frequency: s.checkFrequency,
      schedule_days: s.checkFrequency === 'scheduled' && s.scheduleDays.length > 0 ? s.scheduleDays : undefined,
      min_size_mb: s.minSizeMb,
      max_size_mb: s.maxSizeMb,
      max_total_gb: s.maxTotalGb,
      ...tf,
      retention_days: s.retentionDays,
      season_detection: s.seasonDetection,
      jellyfin_metadata: s.jellyfinMetadata,
    }

    try {
      let subId: number
      if (isNew) {
        const result = await createMutation.mutateAsync({
          channel_id: s.channelId, topic_id: s.topicId, enabled: true, mode: 'immediate', ...common,
        } as T.SubscriptionCreateRequest)
        subId = result.id
        toast.success('Subscription created')
      } else {
        await updateMutation.mutateAsync(common as T.SubscriptionUpdateRequest)
        subId = parseInt(id!)
        toast.success('Subscription updated')
      }

      if (rugbyEnabled && selectedLeague !== null) {
        await setSubscriptionLeague.mutateAsync({ subId, leagueId: selectedLeague })
      }

      navigate('/subscriptions')
    } catch (e) {
      toast.error((e as Error).message)
    }
  }

  const isLoading = !isNew && existingSubscription.isLoading
  const isSubmitting = createMutation.isPending || updateMutation.isPending
  if (isLoading) return <div className="p-6">Loading...</div>

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold">{isNew ? 'New Subscription' : 'Edit Subscription'}</h1>
        <p className="text-sm text-muted-foreground">
          {isNew ? 'Create a media subscription' : 'Update subscription settings'}
        </p>
      </div>

      {/* Name + Channel + Topic */}
      <Card>
        <CardHeader><CardTitle className="text-lg">Source</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <FieldLabel htmlFor="name" tip="A friendly label for this subscription, shown in the list. Optional — defaults to the channel name.">
              Name
            </FieldLabel>
            <Input id="name" value={s.name} onChange={(e) => editor.update('name', e.target.value)}
              placeholder="e.g. Premiership matches" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <FieldLabel tip="The Telegram channel to monitor for new media.">Channel</FieldLabel>
              <Combobox
                value={s.channelId?.toString() || ''}
                onChange={(v) => { editor.update('channelId', v ? parseInt(v) : null); editor.update('topicId', null) }}
                placeholder="Select channel" searchPlaceholder="Search channels…"
                options={(channels.data ?? []).map((ch) => ({ value: ch.id.toString(), label: ch.title }))}
              />
            </div>
            <div className="space-y-2">
              <FieldLabel tip="Forum topic within the channel. Required — pick the specific topic to capture.">Topic</FieldLabel>
              <Combobox
                value={s.topicId?.toString() || ''}
                onChange={(v) => editor.update('topicId', v ? parseInt(v) : null)}
                disabled={!s.channelId} placeholder="Select topic" searchPlaceholder="Search topics…"
                options={(topics.data ?? []).map((t) => ({ value: t.id.toString(), label: t.title }))}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filter */}
      <Card>
        <CardHeader><CardTitle className="text-lg">Filter</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <FieldLabel tip="Include = only capture media whose filename/caption matches the regex. Exclude = capture everything except matches.">
              Filter Mode
            </FieldLabel>
            <div className="flex gap-4">
              {['include', 'exclude'].map((mode) => (
                <label key={mode} className="flex cursor-pointer items-center gap-2">
                  <input type="radio" name="filterMode" value={mode}
                    checked={s.filterMode === mode}
                    onChange={(e) => editor.update('filterMode', e.target.value as any)} />
                  <span className="text-sm capitalize">{mode}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <FieldLabel htmlFor="regex" tip="Case-insensitive regular expression matched against filename + caption. Leave empty to capture everything.">
              Filter Regex
            </FieldLabel>
            <Textarea id="regex" value={s.filterRegex}
              onChange={(e) => editor.update('filterRegex', e.target.value)}
              placeholder={'e.g. \\.mkv$  or  (final|semi)'} className="font-mono text-sm" rows={2} />
            {s.filterRegex && (
              <div className="flex items-center gap-2 text-sm">
                {editor.regexValid
                  ? <span className="text-green-600">✓ Valid pattern</span>
                  : <span className="text-red-600">✗ {editor.regexError}</span>}
              </div>
            )}
          </div>

          {/* Regex tester */}
          <div className="space-y-2 rounded-md border bg-muted/30 p-3">
            <FieldLabel htmlFor="regexTest" tip="Type a sample filename/caption to see whether the regex above matches it.">
              Test a string
            </FieldLabel>
            <Input id="regexTest" value={testStr} onChange={(e) => setTestStr(e.target.value)}
              placeholder="Paste a filename or caption…" className="font-mono text-sm" />
            {testStr && editor.regexValid && s.filterRegex && (
              <div className="space-y-1 text-sm">
                {testMatch
                  ? <p className="text-green-600">✓ Matches{s.filterMode === 'exclude' ? ' → would be EXCLUDED' : ' → captured'}</p>
                  : <p className="text-amber-600">✗ No match{s.filterMode === 'exclude' ? ' → captured' : ' → skipped'}</p>}
                {testMatch && (
                  <p className="text-xs text-muted-foreground">
                    Matched <code className="rounded bg-muted px-1 font-mono text-foreground">{JSON.stringify(testMatch[0])}</code>
                    {' '}at position {testMatch.index}. (Substring match — use <code className="font-mono">^…$</code> to require the whole string, <code className="font-mono">\.</code> for a literal dot.)
                  </p>
                )}
              </div>
            )}
            {testStr && !s.filterRegex && <p className="text-sm text-muted-foreground">Enter a regex above to test.</p>}
          </div>
        </CardContent>
      </Card>

      {/* Capture frequency */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-1.5">
            <CardTitle className="text-lg">Capture Frequency</CardTitle>
            <InfoTip text="How quickly new posts are captured. Real-time queues media the instant it's posted (live Telegram events). Intervals poll on a timer. Scheduled only checks on chosen weekdays." />
          </div>
          <p className="text-sm text-muted-foreground">How often this subscription looks for new media.</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <Combobox
            value={s.checkFrequency}
            onChange={(v) => editor.update('checkFrequency', v)}
            options={[
              { value: 'realtime', label: 'Real-time (instant)' },
              { value: '1m', label: 'Every 1 minute' },
              { value: '5m', label: 'Every 5 minutes' },
              { value: '15m', label: 'Every 15 minutes' },
              { value: '30m', label: 'Every 30 minutes' },
              { value: 'hourly', label: 'Hourly' },
              { value: 'daily', label: 'Daily' },
              { value: 'scheduled', label: 'Scheduled (specific weekdays)' },
            ]}
          />
          {s.checkFrequency === 'realtime' && (
            <p className="text-sm text-muted-foreground">⚡ Media is queued the moment it's posted, via live Telegram events.</p>
          )}
          {s.checkFrequency === 'scheduled' && (
            <div className="space-y-2">
              <FieldLabel tip="Only these weekdays are scanned. Pick at least one.">Weekdays</FieldLabel>
              <div className="flex flex-wrap gap-3">
                {DAYS.map((day) => (
                  <label key={day.value} className="flex cursor-pointer items-center gap-2">
                    <Checkbox checked={s.scheduleDays.includes(day.value)}
                      onCheckedChange={() => editor.toggleScheduleDay(day.value)} />
                    <span className="text-sm">{day.label}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Disk Quota */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-1.5">
            <CardTitle className="text-lg">Disk Quota</CardTitle>
            <InfoTip text="Cap total disk space for this subscription. When exceeded, the oldest downloads are deleted to stay under the limit (newest always kept)." />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex cursor-pointer items-center gap-2">
            <Checkbox checked={s.maxTotalGb === null}
              onCheckedChange={(c) => editor.update('maxTotalGb', c ? null : 50)} />
            <span className="text-sm">Unlimited</span>
          </label>
          {s.maxTotalGb !== null && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Max size</Label>
                <span className="text-sm font-medium tabular-nums">{s.maxTotalGb} GB</span>
              </div>
              <div className="flex items-center gap-3">
                <input type="range" min={1} max={1000} step={1} value={s.maxTotalGb}
                  onChange={(e) => editor.update('maxTotalGb', parseInt(e.target.value))}
                  className="h-2 flex-1 cursor-pointer accent-primary" />
                <Input type="number" min={1} value={s.maxTotalGb}
                  onChange={(e) => editor.update('maxTotalGb', e.target.value ? Math.max(1, parseInt(e.target.value)) : 1)}
                  className="w-24" />
              </div>
              <p className="text-xs text-muted-foreground">Oldest files deleted once this subscription exceeds {s.maxTotalGb} GB.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Timeframe */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-1.5">
            <CardTitle className="text-lg">Timeframe</CardTitle>
            <InfoTip text="Limit which posts to capture by date. Set a From date in the past and keep Ongoing on to catch up missed media AND keep getting new posts." />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <FieldLabel htmlFor="dateFrom" tip="Capture posts from this date onward. Empty = from the very beginning.">From</FieldLabel>
              <Input id="dateFrom" type="date" value={s.dateFrom}
                onChange={(e) => editor.update('dateFrom', e.target.value)} />
            </div>
            <div className="space-y-2">
              <FieldLabel htmlFor="dateTo" tip="Only used when Ongoing is off — stops capturing after this date.">To</FieldLabel>
              <Input id="dateTo" type="date" value={s.dateTo} disabled={s.ongoing}
                onChange={(e) => editor.update('dateTo', e.target.value)} />
            </div>
          </div>
          <label className="flex cursor-pointer items-center gap-2">
            <Checkbox checked={s.ongoing}
              onCheckedChange={(c) => editor.update('ongoing', c as boolean)} />
            <span className="text-sm">Ongoing — keep capturing new posts (no end date)</span>
          </label>
          <p className="text-sm text-muted-foreground">
            {!s.dateFrom && s.ongoing && 'Capturing all history + everything new.'}
            {s.dateFrom && s.ongoing && `From ${s.dateFrom} onward — catches up missed, keeps going.`}
            {s.dateFrom && !s.ongoing && s.dateTo && `Window: ${s.dateFrom} → ${s.dateTo} (stops after).`}
            {s.dateFrom && !s.ongoing && !s.dateTo && `From ${s.dateFrom}; set a To date or turn Ongoing back on.`}
            {!s.dateFrom && !s.ongoing && s.dateTo && `Up to ${s.dateTo}.`}
          </p>
        </CardContent>
      </Card>

      {/* Rugby League */}
      {rugbyEnabled && rugbyLeagues && (
        <Card>
          <CardHeader><CardTitle className="text-lg">Rugby League</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <FieldLabel htmlFor="rugbyToggle" tip="Enable automatic rugby match detection and filename enrichment for this subscription.">
                Rugby Enrichment
              </FieldLabel>
              <Switch id="rugbyToggle" checked={rugbyOn} onCheckedChange={setRugbyOn} />
            </div>

            {rugbyOn && (
              <>
                <div className="space-y-2">
                  <FieldLabel tip="Select which rugby league to link to this subscription.">
                    League
                  </FieldLabel>
                  <Combobox
                    value={selectedLeague?.toString() || ''}
                    onChange={(v) => setSelectedLeague(v ? parseInt(v) : null)}
                    placeholder="— None —"
                    options={[
                      { value: '', label: '— None —' },
                      ...rugbyLeagues.map((l) => ({ value: l.id.toString(), label: l.name })),
                    ]}
                  />
                </div>

                {/* Preview */}
                {selectedLeague && (
                  <div className="space-y-3 rounded-md border bg-muted/30 p-3">
                    <div className="space-y-2">
                      <FieldLabel htmlFor="testFilename" tip="Test how the preview works with a sample filename.">
                        Test Filename
                      </FieldLabel>
                      <Input
                        id="testFilename"
                        value={testFilename}
                        onChange={(e) => {
                          setTestFilename(e.target.value)
                          if (selectedLeague) previewMutation.mutate({ leagueId: selectedLeague, text: e.target.value })
                        }}
                        placeholder="e.g. Sale Sharks v Gloucester.mp4"
                      />
                    </div>

                    {previewMutation.data && (
                      <div className="space-y-2 rounded bg-background p-2">
                        {previewMutation.data.matched ? (
                          <>
                            <p className="text-sm font-medium text-green-600">✓ Confident match ({Math.round(previewMutation.data.confidence * 100)}%)</p>
                            <div className="flex items-center gap-2">
                              {previewMutation.data.home_badge && <MediaThumb src={previewMutation.data.home_badge} alt={previewMutation.data.home || ''} size="sm" />}
                              {previewMutation.data.away_badge && <MediaThumb src={previewMutation.data.away_badge} alt={previewMutation.data.away || ''} size="sm" />}
                              <span className="text-sm">{previewMutation.data.home} vs {previewMutation.data.away}</span>
                            </div>
                            {previewMutation.data.tokens && (
                              <div className="mt-2 border-t pt-2">
                                <p className="text-xs text-muted-foreground">Rendered path:</p>
                                <p className="font-mono text-xs">
                                  {renderTemplate(s.renameTemplate || DEFAULT_TEMPLATE, previewMutation.data.tokens)}
                                </p>
                              </div>
                            )}
                          </>
                        ) : (
                          <p className="text-sm text-amber-600">No confident match — would keep original filename.</p>
                        )}
                        <p className="text-xs text-muted-foreground">
                          {previewMutation.data.fixtures_count} fixtures · {previewMutation.data.teams_count} teams loaded
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Storage & Naming */}
      <Card>
        <CardHeader><CardTitle className="text-lg">Storage & Naming</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <FieldLabel htmlFor="path" tip="Base folder on the server where files are saved. Must be writable.">Storage Path</FieldLabel>
            <FolderPicker id="path" value={s.storagePath}
              onChange={(p) => editor.update('storagePath', p)} placeholder="/media/downloads" />
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="template" tip="Tokens: {channel} {topic} {title} {season} {episode} {date} {original} {ext}. Slashes create folders.">
              Naming Template
            </FieldLabel>
            <Input id="template" value={s.renameTemplate}
              onChange={(e) => editor.update('renameTemplate', e.target.value)} placeholder={DEFAULT_TEMPLATE} />
            <div className="text-xs text-muted-foreground">
              Preview: <Badge variant="outline" className="ml-1 font-mono">{previewFilename}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Advanced */}
      <Card>
        <CardHeader><CardTitle className="text-lg">Advanced</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center justify-between">
            <FieldLabel htmlFor="seasonDet" tip="Detect SxxExx patterns in filenames to fill {season}/{episode} tokens.">
              Season detection
            </FieldLabel>
            <Switch id="seasonDet" checked={s.seasonDetection}
              onCheckedChange={(c) => editor.update('seasonDetection', c as boolean)} />
          </div>

          <div className="flex items-center justify-between">
            <FieldLabel htmlFor="jellyfin" tip="Write Jellyfin/Kodi .nfo sidecars (+ season folders & tvshow.nfo when episodes are detected).">
              Jellyfin metadata
            </FieldLabel>
            <Switch id="jellyfin" checked={s.jellyfinMetadata}
              onCheckedChange={(c) => editor.update('jellyfinMetadata', c as boolean)} />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <FieldLabel htmlFor="retToggle" tip="Auto-delete this subscription's files older than N days. Off = keep until disk-quota or global purge applies.">
                Retention
              </FieldLabel>
              <Switch id="retToggle" checked={s.retentionDays !== null}
                onCheckedChange={(c) => editor.update('retentionDays', c ? 30 : null)} />
            </div>
            {s.retentionDays !== null && (
              <div className="flex items-center gap-2">
                <Input type="number" min={1} value={s.retentionDays}
                  onChange={(e) => editor.update('retentionDays', e.target.value ? Math.max(1, parseInt(e.target.value)) : 1)}
                  className="w-28" />
                <span className="text-sm text-muted-foreground">days, then delete</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button onClick={handleSubmit} disabled={isSubmitting} className="flex-1 bg-primary hover:bg-primary/90">
          {isSubmitting ? 'Saving…' : isNew ? 'Create' : 'Update'}
        </Button>
        <Button onClick={() => navigate('/subscriptions')} disabled={isSubmitting} variant="outline">Cancel</Button>
      </div>
    </div>
  )
}
