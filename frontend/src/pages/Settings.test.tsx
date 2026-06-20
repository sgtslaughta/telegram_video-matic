import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Settings from './Settings'
import * as settingsHooks from '@/hooks/useSettings'
import * as themeHook from '@/hooks/useTheme'
import * as pluginsHook from '@/hooks/usePlugins'
import type * as T from '@/lib/types'

const createWrapper = () => {
  const queryClient = new QueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

const mockSettings: T.SettingRead[] = [
  { key: 'poll_interval_sec', value: '300' },
  { key: 'max_concurrent_downloads', value: '4' },
  { key: 'retention_days', value: '90' },
  { key: 'retention_disk_pct', value: '80' },
]

const mockPlugins: T.PluginRead[] = [
  {
    id: 1,
    name: 'test-plugin',
    version: '1.0.0',
    enabled: true,
    config: null,
    installed_at: '2026-01-01T00:00:00Z',
  },
]

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders settings form with all fields', async () => {
    vi.spyOn(settingsHooks, 'useSettings').mockReturnValue({
      data: mockSettings,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    vi.spyOn(themeHook, 'useTheme').mockReturnValue({
      theme: 'system',
      toggleTheme: vi.fn(),
      setTheme: vi.fn(),
      effectiveTheme: 'light',
    })

    vi.spyOn(pluginsHook, 'usePlugins').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Settings />, { wrapper: createWrapper() })

    expect(screen.getByDisplayValue('300')).toBeTruthy()
    expect(screen.getByDisplayValue('4')).toBeTruthy()
    expect(screen.getByDisplayValue('90')).toBeTruthy()
    expect(screen.getByDisplayValue('80')).toBeTruthy()
  })

  it('renders theme selector with radio buttons', async () => {
    vi.spyOn(settingsHooks, 'useSettings').mockReturnValue({
      data: mockSettings,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    vi.spyOn(themeHook, 'useTheme').mockReturnValue({
      theme: 'light',
      toggleTheme: vi.fn(),
      effectiveTheme: 'light',
    })

    vi.spyOn(pluginsHook, 'usePlugins').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Settings />, { wrapper: createWrapper() })

    const lightRadio = screen.getByRole('radio', { name: /light/i }) as HTMLInputElement
    expect(lightRadio.checked).toBe(true)
  })

  it('renders plugins section with toggle', async () => {
    vi.spyOn(settingsHooks, 'useSettings').mockReturnValue({
      data: mockSettings,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    vi.spyOn(themeHook, 'useTheme').mockReturnValue({
      theme: 'system',
      toggleTheme: vi.fn(),
      setTheme: vi.fn(),
      effectiveTheme: 'light',
    })

    vi.spyOn(pluginsHook, 'usePlugins').mockReturnValue({
      data: mockPlugins,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    render(<Settings />, { wrapper: createWrapper() })

    expect(screen.getByText('test-plugin')).toBeTruthy()
    const checkbox = screen.getByRole('checkbox', { name: /test-plugin/i }) as HTMLInputElement
    expect(checkbox.checked).toBe(true)
  })

  it('calls updateSettings when save button is clicked', async () => {
    const updateMutate = vi.fn()
    vi.spyOn(settingsHooks, 'useSettings').mockReturnValue({
      data: mockSettings,
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    vi.spyOn(settingsHooks, 'useUpdateSettings').mockReturnValue({
      mutate: updateMutate,
      isPending: false,
      isError: false,
      error: null,
      status: 'idle',
    } as any)

    vi.spyOn(themeHook, 'useTheme').mockReturnValue({
      theme: 'system',
      toggleTheme: vi.fn(),
      setTheme: vi.fn(),
      effectiveTheme: 'light',
    })

    vi.spyOn(pluginsHook, 'usePlugins').mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      status: 'success',
      refetch: vi.fn(),
      isPending: false,
    } as any)

    const user = userEvent.setup()
    render(<Settings />, { wrapper: createWrapper() })

    const saveButton = screen.getByRole('button', { name: /save/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(updateMutate).toHaveBeenCalled()
    })
  })
})
