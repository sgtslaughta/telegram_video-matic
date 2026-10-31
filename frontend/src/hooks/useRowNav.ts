import { useEffect, useRef } from 'react'

/** j/k move focus between [data-row] elements inside the returned ref. */
export function useRowNav<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  useEffect(() => {
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.key !== 'j' && e.key !== 'k') return
      if (e.metaKey || e.ctrlKey || e.altKey) return
      const t = e.target as HTMLElement
      if (t.closest('input,textarea,select,[role=dialog]') || t.isContentEditable) return
      const rows = Array.from(ref.current?.querySelectorAll<HTMLElement>('[data-row]') ?? [])
      if (!rows.length) return
      const i = rows.indexOf(document.activeElement as HTMLElement)
      const next = e.key === 'j' ? Math.min(i + 1, rows.length - 1) : Math.max(i - 1, 0)
      rows[i < 0 ? 0 : next]?.focus()
      e.preventDefault()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])
  return ref
}
