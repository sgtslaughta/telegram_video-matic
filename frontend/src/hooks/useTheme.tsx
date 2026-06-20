import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useUpdateSettings } from './useSettings'
import type * as T from '@/lib/types'

type Theme = 'light' | 'dark' | 'system'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  effectiveTheme: 'light' | 'dark'
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('system')
  const [effectiveTheme, setEffectiveTheme] = useState<'light' | 'dark'>('light')
  const updateSettings = useUpdateSettings()

  useEffect(() => {
    const stored = localStorage.getItem('theme') as Theme | null
    if (stored) {
      setTheme(stored)
    }
  }, [])

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const updateEffective = () => {
      let resolved: 'light' | 'dark'
      if (theme === 'system') {
        resolved = mediaQuery.matches ? 'dark' : 'light'
      } else {
        resolved = theme
      }
      setEffectiveTheme(resolved)
      document.documentElement.classList.toggle('dark', resolved === 'dark')
    }

    updateEffective()

    if (theme === 'system') {
      mediaQuery.addEventListener('change', updateEffective)
      return () => mediaQuery.removeEventListener('change', updateEffective)
    }
  }, [theme])

  const toggleTheme = () => {
    const next: Theme = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'
    setTheme(next)
    localStorage.setItem('theme', next)
    updateSettings.mutate({ theme: next })
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, effectiveTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextType {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    throw new Error('useTheme must be used inside ThemeProvider')
  }
  return ctx
}
