export const DEFAULT_TEMPLATE = '{channel}/{title}{ext}';
/** Sample-value preview of a naming template. */
export function sampleName(template) {
    return (template || DEFAULT_TEMPLATE)
        .replaceAll('{channel}', 'RugbyChannel')
        .replaceAll('{topic}', 'General')
        .replaceAll('{title}', 'Final Match')
        .replaceAll('{season}', '01')
        .replaceAll('{episode}', '05')
        .replaceAll('{date}', '2026-06-20')
        .replaceAll('{original}', 'Final Match.mp4')
        .replaceAll('{ext}', 'mp4');
}
/** Render rugby tokens into a template for the match preview. */
export function renderTemplate(template, tokens) {
    let out = template;
    for (const k of ['rugby_league', 'rugby_season', 'rugby_round', 'home', 'away', 'rugby_sport']) {
        out = out.replaceAll(`{${k}}`, tokens[k] || '');
    }
    return out.replaceAll('{ext}', '.mp4');
}
