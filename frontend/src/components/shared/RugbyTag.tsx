import { MapPin } from 'lucide-react'
import type { RugbyEnrichment } from '@/lib/types'

/** Compact inline rugby enrichment: team badges + "Home vs Away" + colored
 * round / venue chips. ponytail: one component for list rows + downloads;
 * cards keep their own larger layout. */
export function RugbyTag({ rugby, className = '' }: { rugby?: RugbyEnrichment | null; className?: string }) {
  if (!rugby) return null
  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      {rugby.home_badge && (
        <img src={rugby.home_badge} alt={rugby.home} className="h-4 w-4 shrink-0 object-contain" loading="lazy" />
      )}
      {rugby.away_badge && (
        <img src={rugby.away_badge} alt={rugby.away} className="h-4 w-4 shrink-0 object-contain" loading="lazy" />
      )}
      <span className="truncate">{rugby.home} vs {rugby.away}</span>
      {rugby.round && (
        <span className="whitespace-nowrap rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
          R{rugby.round}
        </span>
      )}
      {rugby.venue && (
        <span className="inline-flex items-center gap-0.5 whitespace-nowrap rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
          <MapPin className="h-2.5 w-2.5" /> {rugby.venue}
        </span>
      )}
    </span>
  )
}
