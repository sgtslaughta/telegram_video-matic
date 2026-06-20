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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type * as T from '@/lib/types'

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
            <CardTitle>System</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="poll">Poll Interval (seconds)</Label>
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
              <Label htmlFor="max-dl">Max Concurrent Downloads</Label>
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
              <Label htmlFor="retention">Retention Days</Label>
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
              <Label htmlFor="retention-pct">Retention Disk Percentage</Label>
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
            <Select value={theme} onValueChange={(v) => setTheme(v as any)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
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
                    className="flex items-center justify-between p-3 border border-slate-200 rounded-lg hover:shadow-md transition-all dark:border-slate-700"
                  >
                    <div>
                      <p className="font-medium">{plugin.name}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">v{plugin.version}</p>
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
              <p className="text-gray-500">No plugins installed</p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Save Button */}
      <motion.div className="mt-8">
        <Button
          onClick={handleSave}
          disabled={updateSettings.isPending || updatePlugin.isPending}
          className="w-full bg-[#229ED9] hover:bg-[#1a7aaf]"
          size="lg"
        >
          Save Changes
        </Button>
      </motion.div>
    </motion.div>
  )
}
