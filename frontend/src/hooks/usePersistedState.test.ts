import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePersistedState } from './usePersistedState'

describe('usePersistedState', () => {
  beforeEach(() => localStorage.clear())

  it('uses initial when nothing stored', () => {
    const { result } = renderHook(() => usePersistedState('k', 'a'))
    expect(result.current[0]).toBe('a')
  })

  it('persists and rehydrates across mounts', () => {
    const first = renderHook(() => usePersistedState('k', 'a'))
    act(() => first.result.current[1]('b'))
    expect(localStorage.getItem('k')).toBe('"b"')

    const second = renderHook(() => usePersistedState('k', 'a'))
    expect(second.result.current[0]).toBe('b')
  })

  it('falls back to initial on corrupt JSON', () => {
    localStorage.setItem('k', '{bad json')
    const { result } = renderHook(() => usePersistedState('k', 42))
    expect(result.current[0]).toBe(42)
  })
})
