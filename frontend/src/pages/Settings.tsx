import { useState } from 'react'
import { motion } from 'framer-motion'
import { useSettings, useUpdateSettings } from '@/hooks/useSettings'
import { useTheme } from '@/hooks/useTheme'
import { usePlugins, useUpdatePlugin } from '@/hooks/usePlugins'
import { useRugbyRescan, useRugbyStatus } from '@/hooks/useRugby'
import { RugbyMatchReview } from '@/components/RugbyMatchReview'
import { ProgressBar } from '@/components/shared/ProgressBar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Combobox } from '@/components/ui/combobox'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { AlertCircle, Info, RefreshCw, Clock, PackagePlus } from 'lucide-react'
import { toast } from 'sonner'
import type * as T from '@/lib/types'

function InstallPluginCard() {
  return (
    <Card className="mt-4 border-dashed">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <PackagePlus className="h-5 w-5" /> Install a plugin
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm text-muted-foreground">
        <p>
          Drop a <code className="rounded bg-muted px-1">*_plugin.py</code> file into the{' '}
          <code className="rounded bg-muted px-1">plugins/</code> directory, then restart the
          container. It's auto-discovered and appears above with its own settings.
        </p>
        <p className="text-xs">
          Plugins run as application code — only install ones you trust.
        </p>
      </CardContent>
    </Card>
  )
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

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3 },
  },
}

export default function Settings() {
  const { data: settings, isLoading: settingsLoading } = useSettings()
  const { data: plugins, isLoading: pluginsLoading } = usePlugins()
  const { theme, setTheme } = useTheme()
  const updateSettings = useUpdateSettings()
  const updatePlugin = useUpdatePlugin()
  const rescan = useRugbyRescan()
  const rugbyStatus = useRugbyStatus()
  const sync = (rugbyStatus.data?.status ?? {}) as Record<string, unknown>
  const syncing = Boolean(sync.syncing)
  const syncDone = Number(sync.sync_done ?? 0)
  const syncTotal = Number(sync.sync_total ?? 0)
  const syncCurrent = (sync.sync_current as string | null) ?? null

  const [formData, setFormData] = useState<T.SettingPatchRequest>(() => {
    if (!settings) return {}
    const data: T.SettingPatchRequest = {}
    settings.forEach((s) => {
      const val = s.value
      if (s.key === 'poll_interval_sec') data.poll_interval_sec = Number(val)
      else if (s.key === 'max_concurrent_downloads')
        data.max_concurrent_downloads = Number(val)
      else if (s.key === 'retention_days') data.retention_days = Number(val)
      else if (s.key === 'retention_disk_pct') data.retention_disk_pct = Number(val)
    })
    return data
  })

  const [pluginStates, setPluginStates] = useState<
    Record<string, { enabled: boolean; config?: Record<string, unknown> }>
  >(() => {
    if (!plugins) return {}
    const states: Record<string, { enabled: boolean; config?: Record<string, unknown> }> = {}
    plugins.forEach((p) => {
      states[p.name] = { enabled: p.enabled, config: p.config || {} }
    })
    return states
  })

  const handleSettingChange = (
    key: keyof T.SettingPatchRequest,
    value: string
  ) => {
    setFormData((prev) => ({
      ...prev,
      [key]: value === '' ? null : Number(value),
    }))
  }

  const handlePluginToggle = (name: string, enabled: boolean) => {
    setPluginStates((prev) => ({
      ...prev,
      [name]: { ...prev[name], enabled },
    }))
  }

  const handlePluginConfigChange = (name: string, key: string, value: unknown) => {
    setPluginStates((prev) => ({
      ...prev,
      [name]: {
        ...prev[name],
        config: { ...prev[name].config, [key]: value },
      },
    }))
  }

  const handleSave = () => {
    updateSettings.mutate(formData)
    Object.entries(pluginStates).forEach(([name, state]) => {
      updatePlugin.mutate({ name, config: { enabled: state.enabled, ...state.config } })
    })
    toast.success('Settings saved')
  }

  const getSettingValue = (key: string): string => {
    if (!settings) return ''
    const setting = settings.find((s) => s.key === key)
    return setting?.value || ''
  }

  if (settingsLoading || pluginsLoading) return <div className="p-6">Loading...</div>

  return (
    <motion.div
      className="space-y-8 max-w-2xl mx-auto p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      variants={containerVariants}
    >
      {/* Settings Section */}
      <motion.div variants={itemVariants}>
        <h2 className="text-2xl font-bold mb-4">Settings</h2>

        {/* System Settings */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>System & Purge</CardTitle>
            <p className="text-sm text-muted-foreground">Global download cadence and disk-space safety limits.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-1.5">
                <Label htmlFor="poll">Poll Interval (seconds)</Label>
                <InfoTip text="How often the app scans your subscriptions for new media." />
              </div>
              <Input
                id="poll"
                type="number"
                value={formData.poll_interval_sec || getSettingValue('poll_interval_sec')}
                onChange={(e) =>
                  handleSettingChange('poll_interval_sec', e.target.value)
                }
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-1.5">
                <Label htmlFor="max-dl">Max Concurrent Downloads</Label>
                <InfoTip text="How many files download at once. Higher = faster but more bandwidth/CPU." />
              </div>
              <Input
                id="max-dl"
                type="number"
                value={
                  formData.max_concurrent_downloads ||
                  getSettingValue('max_concurrent_downloads')
                }
                onChange={(e) =>
                  handleSettingChange('max_concurrent_downloads', e.target.value)
                }
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-1.5">
                <Label htmlFor="retention">Global Purge: Max Age (days)</Label>
                <InfoTip text="Safety net across ALL subscriptions: downloaded files older than this are deleted. Per-subscription retention can be stricter." />
              </div>
              <Input
                id="retention"
                type="number"
                value={formData.retention_days || getSettingValue('retention_days')}
                onChange={(e) =>
                  handleSettingChange('retention_days', e.target.value)
                }
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-1.5">
                <Label htmlFor="retention-pct">Global Purge: Disk Usage Limit (%)</Label>
                <InfoTip text="When the disk reaches this % full, the oldest downloads are deleted until back under. Prevents filling the disk." />
              </div>
              <Input
                id="retention-pct"
                type="number"
                value={
                  formData.retention_disk_pct ||
                  getSettingValue('retention_disk_pct')
                }
                onChange={(e) =>
                  handleSettingChange('retention_disk_pct', e.target.value)
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Theme Section */}
        <Card>
          <CardHeader>
            <CardTitle>Theme</CardTitle>
          </CardHeader>
          <CardContent>
            <Combobox
              value={theme}
              onChange={(v) => setTheme(v as any)}
              options={[
                { value: 'light', label: 'Light' },
                { value: 'dark', label: 'Dark' },
                { value: 'system', label: 'System' },
              ]}
            />
          </CardContent>
        </Card>
      </motion.div>

      {/* Plugins Section */}
      <motion.div variants={itemVariants} className="mt-8">
        <h2 className="text-2xl font-bold mb-4">Plugins</h2>

        <div className="space-y-4">
          {plugins && plugins.length > 0 ? (
            plugins.map((plugin) => {
            const isRugby = plugin.name === 'rugby'
            const enabled = pluginStates[plugin.name]?.enabled ?? plugin.enabled
            const rateLimited = isRugby && Boolean(
              (plugin.status as Record<string, unknown> | undefined)?.rate_limited
            )
            const onScan = () =>
              rescan.mutate(undefined, {
                onSuccess: () => toast.success('Scan started — fetching fixtures in the background'),
                onError: (e) => toast.error(e instanceof Error ? e.message : 'Scan failed'),
              })
            return (
              <Card key={plugin.id}>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    {/* Error Banner */}
                    {plugin.last_error && (
                      <div className="flex gap-3 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900 dark:bg-red-950">
                        <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-400" />
                        <div className="text-sm text-red-900 dark:text-red-100">
                          <p className="font-medium">Error</p>
                          <p>{plugin.last_error}</p>
                        </div>
                      </div>
                    )}

                    {/* Plugin Header */}
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div>
                          <p className="font-medium capitalize">{plugin.name}</p>
                          <p className="text-sm text-muted-foreground">v{plugin.version}</p>
                        </div>
                        {rateLimited && (
                          <span className="inline-flex items-center gap-1 rounded-full border border-amber-300 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
                            <Clock className="h-3 w-3" /> Rate limited — coverage may be incomplete
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {isRugby && enabled && (
                          <Button size="sm" variant="outline" onClick={onScan} disabled={rescan.isPending}>
                            <RefreshCw className={`mr-2 h-4 w-4 ${rescan.isPending ? 'animate-spin' : ''}`} />
                            {rescan.isPending ? 'Scanning…' : 'Scan now'}
                          </Button>
                        )}
                        <Switch
                          aria-label={plugin.name}
                          checked={enabled}
                          onCheckedChange={(checked) =>
                            handlePluginToggle(plugin.name, checked)
                          }
                        />
                      </div>
                    </div>

                    {/* Config Schema Fields */}
                    {plugin.config_schema?.fields && plugin.config_schema.fields.length > 0 && (
                      <div className="border-t pt-4 space-y-3">
                        {plugin.config_schema.fields.map((field) => (
                          <div key={field.key} className="space-y-2">
                            <div className="flex items-center gap-1">
                              <Label htmlFor={`${plugin.name}-${field.key}`} className="text-sm">
                                {field.label}
                              </Label>
                              {field.help && (
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button type="button" tabIndex={-1} className="text-muted-foreground hover:text-foreground" aria-label="Help">
                                      <Info className="h-3.5 w-3.5" />
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent className="text-sm">{field.help}</TooltipContent>
                                </Tooltip>
                              )}
                            </div>
                            {field.type === 'boolean' ? (
                              <Switch
                                id={`${plugin.name}-${field.key}`}
                                checked={(pluginStates[plugin.name]?.config?.[field.key] as boolean) ?? false}
                                onCheckedChange={(checked) =>
                                  handlePluginConfigChange(plugin.name, field.key, checked)
                                }
                              />
                            ) : (
                              <Input
                                id={`${plugin.name}-${field.key}`}
                                type={field.type === 'number' ? 'number' : 'text'}
                                value={(pluginStates[plugin.name]?.config?.[field.key] as string) ?? ''}
                                onChange={(e) =>
                                  handlePluginConfigChange(
                                    plugin.name,
                                    field.key,
                                    field.type === 'number' ? (e.target.value ? Number(e.target.value) : null) : e.target.value
                                  )
                                }
                              />
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Rugby: live metadata-sync progress */}
                    {isRugby && enabled && syncing && (
                      <div className="space-y-1 border-t pt-4">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>Syncing metadata{syncCurrent ? `: ${syncCurrent}` : ''}…</span>
                          <span className="tabular-nums">{syncDone}/{syncTotal || '—'}</span>
                        </div>
                        <ProgressBar progress={syncTotal ? (syncDone / syncTotal) * 100 : 5} animated />
                      </div>
                    )}

                    {/* Rugby-specific: needs-review queue (same card, no duplicate) */}
                    {isRugby && enabled && (
                      <div className="border-t pt-4">
                        <RugbyMatchReview />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )})
          ) : (
            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground">No plugins installed</p>
              </CardContent>
            </Card>
          )}
        </div>

        <InstallPluginCard />
      </motion.div>

      {/* Save Button */}
      <motion.div className="mt-8">
        <Button
          onClick={handleSave}
          disabled={updateSettings.isPending || updatePlugin.isPending}
          className="w-full bg-primary hover:bg-primary/90"
          size="lg"
        >
          Save Changes
        </Button>
      </motion.div>
    </motion.div>
  )
}
