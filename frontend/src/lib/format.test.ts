import { describe, expect, it } from 'vitest'
import { formatBytes, formatDuration, relTime } from './format'

describe('format', () => {
  it('relTime', () => {
    const now = Date.parse('2026-11-01T12:00:00Z')
    expect(relTime('2026-11-01T11:59:50Z', now)).toBe('just now')
    expect(relTime('2026-11-01T10:00:00Z', now)).toMatch(/2 hours ago/)
    expect(relTime(null, now)).toBe('never')
  })
  it('bytes and duration', () => {
    expect(formatBytes(1536 * 1024 ** 2)).toBe('1.5 GB')
    expect(formatBytes(0)).toBe('0 B')
    expect(formatDuration(6120)).toBe('1h 42m')
    expect(formatDuration(600)).toBe('10m')
  })
})
