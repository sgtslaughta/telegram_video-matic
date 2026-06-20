import { createContext, useContext, useEffect, useState } from 'react'
import { ACCENTS, DEFAULT_ACCENT, applyAccent, type AccentName } from '@/lib/accent'

const KEY = 'accent'

interface AccentCtx {
  accent: AccentName
  setAccent: (a: AccentName) => void
}

const AccentContext = createContext<AccentCtx | null>(null)

export function AccentProvider({ children }: { children: React.ReactNode }) {
  const [accent, setAccent] = useState<AccentName>(() => {
    const saved = typeof localStorage !== 'undefined' ? localStorage.getItem(KEY) : null
    return saved && ACCENTS.some((a) => a.name === saved) ? (saved as AccentName) : DEFAULT_ACCENT
  })

  useEffect(() => {
    applyAccent(accent)
    localStorage.setItem(KEY, accent)
  }, [accent])

  return <AccentContext.Provider value={{ accent, setAccent }}>{children}</AccentContext.Provider>
}

export function useAccent(): AccentCtx {
  const ctx = useContext(AccentContext)
  // ponytail: graceful fallback so components render in isolation (tests) without a provider
  if (!ctx) return { accent: DEFAULT_ACCENT, setAccent: () => {} }
  return ctx
}
