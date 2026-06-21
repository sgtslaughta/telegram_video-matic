import { useState } from 'react'
import { motion } from 'framer-motion'
import { useSettings, useUpdateSettings } from '@/hooks/useSettings'
import { useTheme } from '@/hooks/useTheme'
import { usePlugins, useUpdatePlugin } from '@/hooks/usePlugins'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Combobox } from '@/components/ui/combobox'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { Info } from 'lucide-react'
import type * as T from '@/lib/types'

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
    Record<string, { enabled: boolean }>
  >(() => {
    if (!plugins) return {}
    const states: Record<string, { enabled: boolean }> = {}
    plugins.forEach((p) => {
      states[p.name] = { enabled: p.enabled }
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
      [name]: { enabled },
    }))
  }

  const handleSave = () => {
    updateSettings.mutate(formData)
    Object.entries(pluginStates).forEach(([name, state]) => {
      updatePlugin.mutate({ name, config: { enabled: state.enabled } })
    })
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

        <Card>
          <CardContent className="pt-6">
            {plugins && plugins.length > 0 ? (
              <div className="space-y-3">
                {plugins.map((plugin) => (
                  <motion.div
                    key={plugin.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center justify-between p-3 border border-border rounded-lg hover:shadow-md transition-all"
                  >
                    <div>
                      <p className="font-medium">{plugin.name}</p>
                      <p className="text-sm text-muted-foreground">v{plugin.version}</p>
                    </div>
                    <Switch
                      aria-label={plugin.name}
                      checked={pluginStates[plugin.name]?.enabled ?? plugin.enabled}
                      onCheckedChange={(checked) =>
                        handlePluginToggle(plugin.name, checked)
                      }
                    />
                  </motion.div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">No plugins installed</p>
            )}
          </CardContent>
        </Card>
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
