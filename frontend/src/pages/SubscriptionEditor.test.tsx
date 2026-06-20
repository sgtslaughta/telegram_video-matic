import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSubscriptionEditor } from '@/hooks/useSubscriptionEditor'

describe('SubscriptionEditor - Regex Validation', () => {
  it('shows valid ✅ for valid regex pattern', () => {
    const { result } = renderHook(() => useSubscriptionEditor())

    act(() => {
      result.current.update('filterRegex', '.*\\.mkv$')
    })

    expect(result.current.regexValid).toBe(true)
    expect(result.current.regexError).toBeNull()
  })

  it('shows error ❌ for invalid regex pattern', () => {
    const { result } = renderHook(() => useSubscriptionEditor())

    act(() => {
      result.current.update('filterRegex', '(?P<invalid')
    })

    expect(result.current.regexValid).toBe(false)
    expect(result.current.regexError).toBeTruthy()
  })

  it('clears error when regex becomes valid', () => {
    const { result } = renderHook(() => useSubscriptionEditor())

    // Start with invalid
    act(() => {
      result.current.update('filterRegex', '(unclosed')
    })
    expect(result.current.regexValid).toBe(false)

    // Fix it
    act(() => {
      result.current.update('filterRegex', '(closed)')
    })
    expect(result.current.regexValid).toBe(true)
    expect(result.current.regexError).toBeNull()
  })

  it('handles empty regex as valid', () => {
    const { result } = renderHook(() => useSubscriptionEditor())

    act(() => {
      result.current.update('filterRegex', '')
    })

    expect(result.current.regexValid).toBe(true)
  })
})
