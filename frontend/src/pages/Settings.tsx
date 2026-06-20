import { useState } from 'react'
import { motion } from 'framer-motion'
import { useSettings, useUpdateSettings } from '@/hooks/useSettings'
import { useTheme } from '@/hooks/useTheme'
import { usePlugins, useUpdatePlugin } from '@/hooks/usePlugins'
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
        <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Settings</h2>

        {/* System Settings */}
        <motion.div className="space-y-4 mb-6 p-6 rounded-lg bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">System</h3>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Poll Interval (seconds)
            </label>
            <input
              type="number"
              value={formData.poll_interval_sec || getSettingValue('poll_interval_sec')}
              onChange={(e) =>
                handleSettingChange('poll_interval_sec', e.target.value)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded focus:border-[#229ED9] focus:ring-2 focus:ring-[#229ED9]/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Max Concurrent Downloads
            </label>
            <input
              type="number"
              value={
                formData.max_concurrent_downloads ||
                getSettingValue('max_concurrent_downloads')
              }
              onChange={(e) =>
                handleSettingChange('max_concurrent_downloads', e.target.value)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded focus:border-[#229ED9] focus:ring-2 focus:ring-[#229ED9]/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Retention Days
            </label>
            <input
              type="number"
              value={formData.retention_days || getSettingValue('retention_days')}
              onChange={(e) =>
                handleSettingChange('retention_days', e.target.value)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded focus:border-[#229ED9] focus:ring-2 focus:ring-[#229ED9]/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Retention Disk Percentage
            </label>
            <input
              type="number"
              value={
                formData.retention_disk_pct ||
                getSettingValue('retention_disk_pct')
              }
              onChange={(e) =>
                handleSettingChange('retention_disk_pct', e.target.value)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded focus:border-[#229ED9] focus:ring-2 focus:ring-[#229ED9]/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            />
          </div>
        </motion.div>

        {/* Theme Section */}
        <motion.div className="space-y-4 p-6 rounded-lg bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Theme</h3>

          <div className="space-y-2">
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="theme"
                value="light"
                checked={theme === 'light'}
                onChange={() => setTheme('light')}
                className="mr-2"
              />
              <span className="text-gray-700 dark:text-gray-300">Light</span>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="theme"
                value="dark"
                checked={theme === 'dark'}
                onChange={() => setTheme('dark')}
                className="mr-2"
              />
              <span className="text-gray-700 dark:text-gray-300">Dark</span>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="theme"
                value="system"
                checked={theme === 'system'}
                onChange={() => setTheme('system')}
                className="mr-2"
              />
              <span className="text-gray-700 dark:text-gray-300">System</span>
            </label>
          </div>
        </motion.div>
      </motion.div>

      {/* Plugins Section */}
      <motion.div variants={itemVariants}>
        <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Plugins</h2>

        {plugins && plugins.length > 0 ? (
          <div className="space-y-3">
            {plugins.map((plugin) => (
              <motion.div
                key={plugin.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-white hover:shadow-md transition-all dark:bg-slate-900 dark:border-slate-700"
              >
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">{plugin.name}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">v{plugin.version}</p>
                </div>
                <div className="flex items-center gap-2">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      aria-label={plugin.name}
                      checked={pluginStates[plugin.name]?.enabled ?? plugin.enabled}
                      onChange={(e) =>
                        handlePluginToggle(plugin.name, e.target.checked)
                      }
                      className="mr-2 accent-[#229ED9]"
                    />
                    <span className="text-gray-700 dark:text-gray-300">Enable</span>
                  </label>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">No plugins installed</p>
        )}
      </motion.div>

      {/* Save Button */}
      <motion.button
        onClick={handleSave}
        disabled={updateSettings.isPending || updatePlugin.isPending}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="w-full px-4 py-2 bg-[#229ED9] text-white rounded-lg font-medium shadow-md hover:bg-[#1a7aaf] hover:shadow-lg transition-all disabled:opacity-50"
      >
        Save Changes
      </motion.button>
    </motion.div>
  )
}
