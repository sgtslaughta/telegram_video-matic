import type * as T from './types'

const API_BASE = '/api'

// Typed fetch wrapper
async function fetchAPI<R>(
  endpoint: string,
  options?: RequestInit & { params?: Record<string, string | number | boolean> }
): Promise<R> {
  const { params, ...init } = options || {}

  let url = `${API_BASE}${endpoint}`
  if (params) {
    const qs = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) {
        qs.append(k, String(v))
      }
    }
    if (qs.toString()) url += `?${qs.toString()}`
  }

  const response = await fetch(url, {
    credentials: 'include',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  if (!response.ok) {
    const errorData = (await response.json().catch(() => ({}))) as T.ApiError | {}
    const msg = 'detail' in errorData ? errorData.detail : `HTTP ${response.status}`
    const error = new Error(Array.isArray(msg) ? msg[0] : msg)
    ;(error as any).status = response.status
    throw error
  }

  return response.json()
}

// Auth
export const auth = {
  login: (password: string) =>
    fetchAPI<void>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    }),

  logout: () =>
    fetchAPI<void>('/auth/logout', { method: 'POST' }),

  me: () =>
    fetchAPI<T.AuthMeRead>('/auth/me'),
}

// Telegram
export const tg = {
  status: () =>
    fetchAPI<T.TelegramStatusRead>('/tg/status'),

  loginPhone: (phone: string) =>
    fetchAPI<void>('/tg/login', {
      method: 'POST',
      body: JSON.stringify({ phone }),
    }),

  loginCode: (code: string) =>
    fetchAPI<void>('/tg/code', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),

  loginPassword: (password: string) =>
    fetchAPI<void>('/tg/password', {
      method: 'POST',
      body: JSON.stringify({ password }),
    }),

  logout: () =>
    fetchAPI<void>('/tg/logout', { method: 'POST' }),
}

// Channels
export const channels = {
  list: () =>
    fetchAPI<T.ChannelRead[]>('/channels'),

  topics: (channelId: number) =>
    fetchAPI<T.TopicRead[]>(`/channels/${channelId}/topics`),
}

// Subscriptions
export const subscriptions = {
  list: () =>
    fetchAPI<T.SubscriptionRead[]>('/subscriptions'),

  create: (data: T.SubscriptionCreateRequest) =>
    fetchAPI<T.SubscriptionRead>('/subscriptions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  get: (id: number) =>
    fetchAPI<T.SubscriptionRead>(`/subscriptions/${id}`),

  update: (id: number, data: T.SubscriptionUpdateRequest) =>
    fetchAPI<T.SubscriptionRead>(`/subscriptions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    fetchAPI<void>(`/subscriptions/${id}`, { method: 'DELETE' }),

  scan: (id: number) =>
    fetchAPI<void>(`/subscriptions/${id}/scan`, { method: 'POST' }),
}

// Media
export const media = {
  list: (filters?: {
    status?: string
    sub_id?: number
    channel_id?: number
    topic_id?: number
    limit?: number
    offset?: number
  }) =>
    fetchAPI<T.MediaItemRead[]>('/media', { params: filters }),

  get: (id: number) =>
    fetchAPI<T.MediaItemRead>(`/media/${id}`),

  download: (id: number) =>
    fetchAPI<T.DownloadJobRead>(`/media/${id}/download`, { method: 'POST' }),

  requeue: (id: number) =>
    fetchAPI<T.DownloadJobRead>(`/media/${id}/requeue`, { method: 'POST' }),

  thumbUrl: (id: number) => `/api/media/${id}/thumb`,
}

// Downloads
export const downloads = {
  active: () =>
    fetchAPI<T.DownloadJobRead[]>('/downloads/active'),
}

// Settings
export const settings = {
  get: () =>
    fetchAPI<T.SettingRead[]>('/settings'),

  update: (data: T.SettingPatchRequest) =>
    fetchAPI<T.SettingRead[]>('/settings', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
}

// Events
export const events = {
  list: (filters?: {
    limit?: number
    offset?: number
    level?: string
    kind?: string
  }) =>
    fetchAPI<T.EventRead[]>('/events', { params: filters }),
}

// Plugins
export const plugins = {
  list: () =>
    fetchAPI<T.PluginRead[]>('/plugins'),

  update: (name: string, config: Record<string, unknown>) =>
    fetchAPI<T.PluginRead>(`/plugins/${name}`, {
      method: 'PATCH',
      body: JSON.stringify(config),
    }),
}
