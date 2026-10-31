const API_BASE = '/api';
// Typed fetch wrapper
export async function fetchAPI(endpoint, options) {
    const { params, ...init } = options || {};
    let url = `${API_BASE}${endpoint}`;
    if (params) {
        const qs = new URLSearchParams();
        for (const [k, v] of Object.entries(params)) {
            if (v !== undefined && v !== null) {
                qs.append(k, String(v));
            }
        }
        if (qs.toString())
            url += `?${qs.toString()}`;
    }
    const response = await fetch(url, {
        credentials: 'include',
        ...init,
        headers: {
            'Content-Type': 'application/json',
            ...init?.headers,
        },
    });
    if (!response.ok) {
        const errorData = (await response.json().catch(() => ({})));
        const msg = 'detail' in errorData ? errorData.detail : `HTTP ${response.status}`;
        const error = new Error(Array.isArray(msg) ? msg[0] : msg);
        error.status = response.status;
        // App-auth gate: an unauthenticated response means the app password is set
        // and we have no session — send the user to the login page (not the login
        // request itself, and not if we're already there, to avoid a redirect loop).
        if (response.status === 401 &&
            endpoint !== '/auth/login' &&
            typeof window !== 'undefined' &&
            window.location.pathname !== '/login') {
            window.location.assign('/login');
        }
        throw error;
    }
    // 204 / empty body (e.g. DELETE, logout) → don't call .json() (it throws)
    if (response.status === 204)
        return undefined;
    const text = await response.text();
    return (text ? JSON.parse(text) : undefined);
}
// Auth
export const auth = {
    login: (password) => fetchAPI('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ password }),
    }),
    logout: () => fetchAPI('/auth/logout', { method: 'POST' }),
    me: () => fetchAPI('/auth/me'),
};
// Telegram
export const tg = {
    status: () => fetchAPI('/tg/status'),
    setCredentials: (api_id, api_hash) => fetchAPI('/tg/credentials', {
        method: 'POST',
        body: JSON.stringify({ api_id, api_hash }),
    }),
    loginPhone: (phone) => fetchAPI('/tg/login', {
        method: 'POST',
        body: JSON.stringify({ phone }),
    }),
    loginCode: (code) => fetchAPI('/tg/code', {
        method: 'POST',
        body: JSON.stringify({ code }),
    }),
    loginPassword: (password) => fetchAPI('/tg/password', {
        method: 'POST',
        body: JSON.stringify({ password }),
    }),
    logout: () => fetchAPI('/tg/logout', { method: 'POST' }),
};
// Channels
export const channels = {
    list: () => fetchAPI('/channels'),
    topics: (channelId) => fetchAPI(`/channels/${channelId}/topics`),
    browse: (channelId, params) => fetchAPI(`/channels/${channelId}/browse`, { params }),
    messageDetail: (channelId, tgMsgId) => fetchAPI(`/channels/${channelId}/message/${tgMsgId}`),
    browseThumbUrl: (channelId, tgMsgId) => `/api/channels/${channelId}/thumb/${tgMsgId}`,
    browseDownload: (channelId, tgMsgId) => fetchAPI(`/channels/${channelId}/browse/${tgMsgId}/download`, { method: 'POST' }),
};
// Subscriptions
export const subscriptions = {
    list: () => fetchAPI('/subscriptions'),
    create: (data) => fetchAPI('/subscriptions', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
    get: (id) => fetchAPI(`/subscriptions/${id}`),
    update: (id, data) => fetchAPI(`/subscriptions/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
    }),
    delete: (id) => fetchAPI(`/subscriptions/${id}`, { method: 'DELETE' }),
    scan: (id) => fetchAPI(`/subscriptions/${id}/scan`, { method: 'POST' }),
};
// Media
export const media = {
    list: (filters) => fetchAPI('/media', { params: filters }),
    get: (id) => fetchAPI(`/media/${id}`),
    clear: () => fetchAPI('/media/clear', { method: 'POST' }),
    download: (id) => fetchAPI(`/media/${id}/download`, { method: 'POST' }),
    requeue: (id) => fetchAPI(`/media/${id}/requeue`, { method: 'POST' }),
    thumbUrl: (id) => `/api/media/${id}/thumb`,
};
// Downloads
export const downloads = {
    active: () => fetchAPI('/downloads/active'),
    queued: () => fetchAPI('/downloads/queued'),
    cancel: (jobId) => fetchAPI(`/downloads/${jobId}/cancel`, { method: 'POST' }),
    pause: (jobId) => fetchAPI(`/downloads/${jobId}/pause`, { method: 'POST' }),
    resume: (jobId) => fetchAPI(`/downloads/${jobId}/resume`, { method: 'POST' }),
};
// Settings
export const settings = {
    get: () => fetchAPI('/settings'),
    update: (data) => fetchAPI('/settings', {
        method: 'PATCH',
        body: JSON.stringify(data),
    }),
};
// Notifications
export const notifications = {
    get: () => fetchAPI('/notifications'),
    saveTargets: (targets) => fetchAPI('/notifications/targets', {
        method: 'PUT',
        body: JSON.stringify(targets),
    }),
    saveOptions: (options) => fetchAPI('/notifications/options', {
        method: 'PUT',
        body: JSON.stringify(options),
    }),
    saveJellyfin: (data) => fetchAPI('/notifications/jellyfin', {
        method: 'PUT',
        body: JSON.stringify(data),
    }),
    test: (body) => fetchAPI('/notifications/test', {
        method: 'POST',
        body: JSON.stringify(body),
    }),
    testJellyfin: () => fetchAPI('/notifications/jellyfin/test', { method: 'POST' }),
};
// Events
export const events = {
    list: (filters) => fetchAPI('/events', { params: filters }),
};
// Plugins
export const plugins = {
    list: () => fetchAPI('/plugins'),
    update: (name, config) => fetchAPI(`/plugins/${name}`, {
        method: 'PATCH',
        body: JSON.stringify(config),
    }),
};
// Rugby
export const rugby = {
    status: () => fetchAPI('/plugins/rugby/status'),
    leagues: (tracked) => fetchAPI('/plugins/rugby/leagues', { params: tracked !== undefined ? { tracked } : {} }),
    refreshCatalog: () => fetchAPI('/plugins/rugby/refresh', { method: 'POST' }),
    refreshLeague: (leagueId) => fetchAPI(`/plugins/rugby/leagues/${leagueId}/refresh`, { method: 'POST' }),
    fixtures: (leagueId, season) => fetchAPI(`/plugins/rugby/leagues/${leagueId}/fixtures`, { params: { season } }),
    matches: (status) => fetchAPI('/plugins/rugby/matches', { params: status ? { status } : {} }),
    patchMatch: (mediaId, data) => fetchAPI(`/plugins/rugby/matches/${mediaId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
    }),
    getSubscriptionLeague: (subId) => fetchAPI(`/plugins/rugby/subscriptions/${subId}`),
    // One topic can carry several leagues; [] unlinks (not a rugby subscription).
    setSubscriptionLeagues: (subId, leagueIds) => fetchAPI(`/plugins/rugby/subscriptions/${subId}`, {
        method: 'PUT',
        body: JSON.stringify({ league_ids: leagueIds }),
    }),
    enrichment: (channelId) => fetchAPI('/plugins/rugby/enrichment', {
        params: { channel_id: channelId },
    }),
    enrichMessages: (messages) => fetchAPI('/plugins/rugby/enrichment/messages', {
        method: 'POST',
        body: JSON.stringify({ messages }),
    }),
    enrichmentByMedia: (mediaIds) => fetchAPI('/plugins/rugby/enrichment/by-media', {
        params: { ids: mediaIds.join(',') },
    }),
    autodetect: (channelId) => fetchAPI(`/plugins/rugby/channels/${channelId}/autodetect`, { method: 'POST' }),
    rescan: () => fetchAPI('/plugins/rugby/rescan', { method: 'POST' }),
    /** Start a maintenance job; dry_run returns a plan in its report, moves nothing. */
    runJob: (job, dryRun) => fetchAPI(`/plugins/rugby/${job}`, {
        method: 'POST',
        params: job === 'rematch' ? { dry_run: dryRun, rescore: true } : { dry_run: dryRun },
    }),
    report: (job) => fetchAPI(`/plugins/rugby/reports/${job}`),
    preview: (leagueId, text) => fetchAPI('/plugins/rugby/preview', {
        method: 'POST',
        body: JSON.stringify({ league_id: leagueId, text }),
    }),
};
// Server-side directory browse for the storage-path picker (sandboxed to MEDIA_ROOT).
export const fs = {
    listDirs: (path) => fetchAPI('/fs/dirs', path ? { params: { path } } : undefined),
};
