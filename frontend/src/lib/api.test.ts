import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as api from './api'

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('auth.login', () => {
    it('POSTs password and includes credentials', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({}), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      await api.auth.login('mypass')

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/auth/login',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({ password: 'mypass' }),
        })
      )
    })

    it('throws with parsed error message on non-2xx', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ detail: 'Invalid password' }), {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      await expect(api.auth.login('badpass')).rejects.toThrow('Invalid password')
    })

    it('throws 401 error', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ detail: 'Unauthorized' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      await expect(api.auth.login('nopass')).rejects.toThrow('Unauthorized')
    })
  })

  describe('subscriptions.list', () => {
    it('GETs subscriptions', async () => {
      const mockData = [
        {
          id: 1,
          name: 'Test',
          channel_id: 123,
          topic_id: 456,
          filter_mode: 'include' as const,
          filter_regex: '.*',
          mode: 'immediate' as const,
          schedule_days: [],
          min_size_bytes: 0,
          max_size_bytes: 1000000,
          storage_path: '/media',
          rename_template: '{channel}/{title}',
          season_detection: false,
          enabled: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ]

      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify(mockData), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      const result = await api.subscriptions.list()
      expect(result).toEqual(mockData)
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/subscriptions',
        expect.objectContaining({
          credentials: 'include',
        })
      )
    })
  })

  describe('media.list with filters', () => {
    it('returns a plain array, not paginated', async () => {
      const mockData = [
        { id: 1, channel_id: 123, tg_msg_id: 456, status: 'pending', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
      ]
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify(mockData), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      const result = await api.media.list({ status: 'pending', limit: 50, offset: 0 })
      expect(Array.isArray(result)).toBe(true)
      expect(result).toEqual(mockData)
    })

    it('constructs query params correctly', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify([]), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      await api.media.list({ status: 'pending', limit: 20, offset: 40 })

      const callUrl = (global.fetch as any).mock.calls[0][0]
      expect(callUrl).toContain('/api/media')
      expect(callUrl).toContain('status=pending')
      expect(callUrl).toContain('limit=20')
      expect(callUrl).toContain('offset=40')
    })
  })

  describe('error parsing', () => {
    it('handles array error detail', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ detail: ['Field is required', 'Another error'] }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      await expect(api.auth.login('test')).rejects.toThrow('Field is required')
    })

    it('handles non-JSON error response', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response('Internal Server Error', {
            status: 500,
            headers: { 'Content-Type': 'text/plain' },
          })
        )
      )

      await expect(api.auth.login('test')).rejects.toThrow('HTTP 500')
    })
  })

  describe('POST with payload', () => {
    it('sends JSON body for subscriptions.create', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ id: 1 }), {
            status: 201,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      const data = {
        channel_id: 10,
        topic_id: 20,
        name: 'Test Sub',
        filter_mode: 'include' as const,
        filter_regex: '.*',
        mode: 'immediate' as const,
        schedule_days: [],
        min_size_bytes: 100,
        max_size_bytes: 1000000,
        storage_path: '/media',
        rename_template: '{title}',
        season_detection: true,
      }

      await api.subscriptions.create(data)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/subscriptions',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify(data),
        })
      )
    })
  })

  describe('query params filtering', () => {
    it('skips undefined and null params', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify([]), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      await api.media.list({ status: 'pending', channel_id: undefined, limit: 50, offset: 0 })

      const callUrl = (global.fetch as any).mock.calls[0][0]
      expect(callUrl).not.toContain('channel_id')
      expect(callUrl).toContain('status=pending')
      expect(callUrl).toContain('limit=50')
    })
  })

  describe('events.list', () => {
    it('returns a plain array, not paginated', async () => {
      const mockData = [
        { id: 1, level: 'info', kind: 'sync', message: 'Test', created_at: '2026-01-01T00:00:00Z' },
      ]
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify(mockData), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      const result = await api.events.list({ limit: 50, offset: 0 })
      expect(Array.isArray(result)).toBe(true)
      expect(result).toEqual(mockData)
    })
  })

  describe('settings.get', () => {
    it('returns an array of settings, not a single object', async () => {
      const mockData = [
        { key: 'poll_interval_sec', value: '60' },
        { key: 'max_concurrent_downloads', value: '4' },
      ]
      global.fetch = vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify(mockData), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )

      const result = await api.settings.get()
      expect(Array.isArray(result)).toBe(true)
      expect(result).toEqual(mockData)
    })
  })

  describe('media.thumbUrl', () => {
    it('returns the URL string without making a fetch', () => {
      const url = api.media.thumbUrl(5)
      expect(url).toBe('/api/media/5/thumb')
    })
  })
})
