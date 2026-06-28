import type { RugbyEnrichment } from '@/lib/types'

/** Home-vs-Away block: HOME/AWAY label above each team logo, a "v" between,
 * optional score under each team. Shared by Browse cards (sm) and the drawer (lg). */
export function RugbyMatchup({
  rugby,
  size = 'sm',
  showScore = false,
}: {
  rugby: RugbyEnrichment
  size?: 'sm' | 'lg'
  showScore?: boolean
}) {
  const logo = size === 'lg' ? 'h-14 w-14' : 'h-9 w-9'
  const label = size === 'lg' ? 'text-[11px]' : 'text-[9px]'
  const name = size === 'lg' ? 'text-sm' : 'text-[10px]'
  const hasScore = showScore && rugby.home_score != null && rugby.away_score != null
  const winHome = hasScore && (rugby.home_score ?? 0) > (rugby.away_score ?? 0)
  const winAway = hasScore && (rugby.away_score ?? 0) > (rugby.home_score ?? 0)

  const Team = ({ side }: { side: 'home' | 'away' }) => {
    const badge = side === 'home' ? rugby.home_badge : rugby.away_badge
    const team = side === 'home' ? rugby.home : rugby.away
    const score = side === 'home' ? rugby.home_score : rugby.away_score
    const win = side === 'home' ? winHome : winAway
    return (
      <div className="flex min-w-0 flex-1 flex-col items-center gap-1">
        <span className={`font-semibold uppercase tracking-wide text-muted-foreground ${label}`}>
          {side}
        </span>
        {badge ? (
          <img src={badge} alt={team ?? side} className={`${logo} object-contain`} loading="lazy" />
        ) : (
          <div className={`${logo} rounded-full bg-muted`} />
        )}
        {size === 'lg' && (
          <span className={`max-w-full truncate text-center ${name}`} title={team ?? undefined}>
            {team}
          </span>
        )}
        {hasScore && (
          <span className={`font-bold tabular-nums ${size === 'lg' ? 'text-xl' : 'text-sm'} ${win ? 'text-primary' : 'text-muted-foreground'}`}>
            {score}
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="flex w-full items-start justify-center gap-2">
      <Team side="home" />
      <span className={`shrink-0 font-bold text-muted-foreground ${size === 'lg' ? 'pt-6 text-base' : 'pt-4 text-xs'}`}>
        v
      </span>
      <Team side="away" />
    </div>
  )
}
