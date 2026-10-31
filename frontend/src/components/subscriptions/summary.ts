import type { SubscriptionRead } from '@/lib/types'

export function filterSummary(s: SubscriptionRead): string {
  const bits: string[] = []
  if (s.filter_regex) bits.push(`${s.filter_mode === 'exclude' ? 'Not' : 'Only'} ${s.filter_regex}`)
  if (s.min_size_mb) bits.push(`≥${s.min_size_mb} MB`)
  if (s.max_size_mb) bits.push(`≤${s.max_size_mb} MB`)
  return bits.join(', ') || 'Everything'
}
