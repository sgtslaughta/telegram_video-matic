import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import { toast } from 'sonner'
import { Page, PageHeader } from '@/components/shared/PageHeader'
import { Skeleton } from '@/components/ui/skeleton'
import { RetentionSection } from '@/components/subscriptions/RetentionSection'
import { RugbySection } from '@/components/subscriptions/RugbySection'
import { SaveBar } from '@/components/subscriptions/SaveBar'
import { SourceSection } from '@/components/subscriptions/SourceSection'
import { StorageSection } from '@/components/subscriptions/StorageSection'
import { ToolsSection } from '@/components/subscriptions/ToolsSection'
import { WhatToDownload } from '@/components/subscriptions/WhatToDownload'
import { useCreateSubscription, useSubscription, useUpdateSubscription } from '@/hooks/useSubscriptions'
import { useSubscriptionEditor, type SubscriptionEditorState } from '@/hooks/useSubscriptionEditor'
import { usePlugins } from '@/hooks/usePlugins'
import { useRugbyLeagues, useSetSubscriptionLeague, useSubscriptionLeague } from '@/hooks/useRugby'
import type * as T from '@/lib/types'

type Sub = T.SubscriptionRead & { keep?: boolean }

function toState(d: Sub): Partial<SubscriptionEditorState> {
  return {
    channelId: d.channel_id,
    topicId: d.topic_id ?? null,
    name: d.name || '',
    filterMode: (d.filter_mode as 'include' | 'exclude') || 'include',
    filterRegex: d.filter_regex || '',
    checkFrequency: d.check_frequency || '5m',
    scheduleDays: d.schedule_days || [],
    minSizeMb: d.min_size_mb ?? null,
    maxSizeMb: d.max_size_mb ?? null,
    maxTotalGb: d.max_total_gb ?? null,
    dateFrom: d.date_from?.slice(0, 10) || '',
    dateTo: d.date_to?.slice(0, 10) || '',
    ongoing: !d.date_to,
    storagePath: d.storage_path,
    renameTemplate: d.rename_template,
    retentionDays: d.retention_days ?? null,
    seasonDetection: d.season_detection || false,
    jellyfinMetadata: d.jellyfin_metadata || false,
    keep: d.keep ?? false,
  }
}

function toPayload(s: SubscriptionEditorState) {
  return {
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
    date_from: s.dateFrom ? new Date(s.dateFrom + 'T00:00:00').toISOString() : null,
    date_to: !s.ongoing && s.dateTo ? new Date(s.dateTo + 'T23:59:59').toISOString() : null,
    retention_days: s.retentionDays,
    keep: s.keep,
    season_detection: s.seasonDetection,
    jellyfin_metadata: s.jellyfinMetadata,
  }
}

export default function SubscriptionEditor() {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const isNew = !id || id === 'new'
  const subId = isNew ? 0 : parseInt(id!)

  const existing = useSubscription(subId)
  const createMutation = useCreateSubscription()
  const updateMutation = useUpdateSubscription(subId)
  const editor = useSubscriptionEditor(
    existing.data ? toState(existing.data as Sub) : undefined,
    existing.data?.id ?? (isNew ? 'new' : 'loading'),
  )
  const { state: s, update } = editor

  const { data: plugins } = usePlugins()
  const rugbyEnabled = plugins?.find((p) => p.name === 'rugby')?.enabled ?? false
  const { data: rugbyLeagues } = useRugbyLeagues()
  const [league, setLeague] = useState<number | null>(null)
  const [leagueBase, setLeagueBase] = useState<number | null>(null)
  const [rugbyOn, setRugbyOn] = useState(true)
  const setSubscriptionLeague = useSetSubscriptionLeague()
  const { data: savedLeague } = useSubscriptionLeague(isNew ? null : subId)
  const [seenLeague, setSeenLeague] = useState(savedLeague)
  if (seenLeague !== savedLeague) {
    setSeenLeague(savedLeague)
    if (savedLeague?.league_id != null) { setLeague(savedLeague.league_id); setLeagueBase(savedLeague.league_id) }
  }
  const toggleRugby = (on: boolean) => { setRugbyOn(on); if (!on) setLeague(null) }

  const leagueDirty = league !== leagueBase
  const dirty = editor.dirty || (rugbyEnabled && leagueDirty)

  const save = async () => {
    if (!s.channelId || !s.topicId) return toast.error('Select a channel and topic')
    if (!s.storagePath) return toast.error('Enter a storage path')
    if (!s.renameTemplate) return toast.error('Enter a naming template')
    if (!editor.regexValid) return toast.error('Fix the filter regex first')
    const common = toPayload(s)
    try {
      let savedId = subId
      if (isNew) {
        const r = await createMutation.mutateAsync({
          channel_id: s.channelId, topic_id: s.topicId, enabled: true, mode: 'immediate', ...common,
        } as T.SubscriptionCreateRequest)
        savedId = r.id
      } else {
        await updateMutation.mutateAsync(common as T.SubscriptionUpdateRequest)
      }
      if (rugbyEnabled && league !== null) await setSubscriptionLeague.mutateAsync({ subId: savedId, leagueId: league })
      editor.markSaved()
      setLeagueBase(league)
      toast.success(isNew ? 'Subscription created' : 'Changes saved')
      if (isNew) navigate('/subscriptions')
    } catch (e) {
      toast.error('Could not save', { description: (e as Error).message })
    }
  }

  const discard = () => {
    if (isNew) return navigate('/subscriptions')
    editor.discard()
    setLeague(leagueBase)
  }

  const saveRef = useRef(save)
  useEffect(() => {
    saveRef.current = save
  })
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') { e.preventDefault(); void saveRef.current() }
    }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [])

  if (!isNew && existing.isLoading) {
    return <Page><PageHeader title="Edit subscription" /><div className="space-y-4">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-40 w-full" />)}</div></Page>
  }

  const saving = createMutation.isPending || updateMutation.isPending
  const title = isNew ? 'New subscription' : existing.data?.name || existing.data?.channel_title || 'Edit subscription'
  return (
    <Page>
      <button type="button" onClick={() => navigate('/subscriptions')}
        className="mb-2 flex items-center gap-1 text-[12px] text-muted-foreground transition-colors hover:text-foreground">
        <ChevronLeft className="h-3.5 w-3.5" />Subscriptions
      </button>
      <PageHeader title={title} description={isNew ? 'Choose a source, then decide what to download.' : undefined} />
      <div className="max-w-3xl space-y-4">
        <SourceSection s={s} update={update} />
        <WhatToDownload s={s} update={update} regexValid={editor.regexValid} regexError={editor.regexError} toggleDay={editor.toggleScheduleDay} />
        <StorageSection s={s} update={update} />
        {rugbyEnabled && rugbyLeagues && (
          <RugbySection leagues={rugbyLeagues} on={rugbyOn} setOn={toggleRugby} league={league} setLeague={setLeague} template={s.renameTemplate} />
        )}
        <RetentionSection s={s} update={update} />
        {!isNew && <ToolsSection id={subId} />}
        {(dirty || isNew) && (
          <SaveBar onSave={save} onDiscard={discard} saving={saving}
            label={isNew ? 'Create subscription' : 'Save changes'} />
        )}
      </div>
    </Page>
  )
}
