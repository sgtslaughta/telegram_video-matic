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
    // App-auth gate: an unauthenticated response means the app password is set
    // and we have no session — send the user to the login page (not the login
    // request itself, and not if we're already there, to avoid a redirect loop).
    if (
      response.status === 401 &&
      endpoint !== '/auth/login' &&
      typeof window !== 'undefined' &&
      window.location.pathname !== '/login'
    ) {
      window.location.assign('/login')
    }
    throw error
  }

  // 204 / empty body (e.g. DELETE, logout) → don't call .json() (it throws)
  if (response.status === 204) return undefined as R
  const text = await response.text()
  return (text ? JSON.parse(text) : undefined) as R
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

  setCredentials: (api_id: string, api_hash: string) =>
    fetchAPI<void>('/tg/credentials', {
      method: 'POST',
      body: JSON.stringify({ api_id, api_hash }),
    }),

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

  browse: (channelId: number, params?: { topic_id?: number; limit?: number; offset_id?: number }) =>
    fetchAPI<{ items: any[]; next_offset_id: number | null; has_more: boolean }>(
      `/channels/${channelId}/browse`, { params }),

  messageDetail: (channelId: number, tgMsgId: number) =>
    fetchAPI<T.MessageDetail>(`/channels/${channelId}/message/${tgMsgId}`),

  browseThumbUrl: (channelId: number, tgMsgId: number) =>
    `/api/channels/${channelId}/thumb/${tgMsgId}`,

  browseDownload: (channelId: number, tgMsgId: number) =>
    fetchAPI<{ status: string; media_id: number }>(
      `/channels/${channelId}/browse/${tgMsgId}/download`, { method: 'POST' }
    ),
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

  clear: () =>
    fetchAPI<void>('/media/clear', { method: 'POST' }),

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

  queued: () =>
    fetchAPI<{ media_id: number; file_name: string | null; size_bytes: number | null }[]>('/downloads/queued'),

  cancel: (jobId: number) =>
    fetchAPI<{ status: string }>(`/downloads/${jobId}/cancel`, { method: 'POST' }),

  pause: (jobId: number) =>
    fetchAPI<{ status: string }>(`/downloads/${jobId}/pause`, { method: 'POST' }),

  resume: (jobId: number) =>
    fetchAPI<{ status: string }>(`/downloads/${jobId}/resume`, { method: 'POST' }),
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
