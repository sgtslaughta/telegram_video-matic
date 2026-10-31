// Shared formatters. Relative times everywhere, exact time on hover (absTime).
const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
const UNITS = [
    ['year', 31536000], ['month', 2592000], ['week', 604800], ['day', 86400], ['hour', 3600], ['minute', 60],
];
export function relTime(iso, now = Date.now()) {
    if (!iso)
        return 'never';
    const sec = (new Date(iso).getTime() - now) / 1000;
    if (Math.abs(sec) < 45)
        return 'just now';
    for (const [unit, s] of UNITS) {
        if (Math.abs(sec) >= s)
            return rtf.format(Math.round(sec / s), unit);
    }
    return rtf.format(Math.round(sec / 60), 'minute');
}
export function absTime(iso) {
    return iso ? new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '';
}
export function formatBytes(n) {
    if (!n || n <= 0)
        return '0 B';
    const u = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), u.length - 1);
    return `${(n / 1024 ** i).toFixed(i >= 3 ? 1 : 0)} ${u[i]}`;
}
export function formatDuration(sec) {
    if (!sec)
        return '';
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    return h ? `${h}h ${String(m).padStart(2, '0')}m` : `${m}m`;
}
