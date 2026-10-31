import { Area, AreaChart, ReferenceArea, XAxis, YAxis } from 'recharts'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { cn } from '@/lib/utils'

export interface Band { from: number; to: number; tone: 'err' | 'warn' }

/** Minimal shadcn area sparkline: no axes, optional shaded bands, hover tooltip. */
export function Sparkline<T extends Record<string, unknown>>({
  data, dataKey, label, bands = [], format, className, labelKey = 't',
}: {
  data: T[]
  dataKey: keyof T & string
  label: string
  bands?: Band[]
  format?: (v: number) => string
  className?: string
  labelKey?: keyof T & string
}) {
  const config = { [dataKey]: { label, color: 'hsl(var(--foreground))' } } satisfies ChartConfig
  const rows = data.map((d, i) => ({ ...d, i }))
  return (
    <ChartContainer config={config} className={cn('aspect-auto h-10 w-full', className)}>
      <AreaChart data={rows} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
        <XAxis dataKey="i" type="number" domain={[0, Math.max(rows.length - 1, 1)]} hide />
        <YAxis hide domain={[0, (max: number) => Math.max(max, 1) * 1.15]} />
        {bands.map((b) => (
          <ReferenceArea key={`${b.from}-${b.tone}`} x1={Math.max(b.from - 0.5, 0)} x2={Math.min(b.to + 0.5, rows.length - 1)}
            fill={`hsl(var(--${b.tone}))`} fillOpacity={0.14} strokeOpacity={0} ifOverflow="hidden" />
        ))}
        <ChartTooltip
          cursor={{ stroke: 'hsl(var(--border))' }}
          isAnimationActive={false}
          content={
            <ChartTooltipContent
              indicator="line"
              labelFormatter={(_, p) => {
                const t = p?.[0]?.payload?.[labelKey] as string | undefined
                return t ? new Date(t).toLocaleString(undefined, { weekday: 'short', hour: 'numeric' }) : ''
              }}
              formatter={(v) => (
                <span className="flex w-full justify-between gap-3">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-medium tabular-nums">{format ? format(Number(v)) : String(v)}</span>
                </span>
              )}
            />
          }
        />
        <Area type="monotone" dataKey={dataKey} stroke={`var(--color-${dataKey})`} strokeWidth={1.5}
          fill={`var(--color-${dataKey})`} fillOpacity={0.06} isAnimationActive={false} dot={false}
          activeDot={{ r: 3, strokeWidth: 0 }} />
      </AreaChart>
    </ChartContainer>
  )
}

/** Stat tile: label, big tabular number, sparkline underneath. */
export function StatTile<T extends Record<string, unknown>>({
  label, value, data, dataKey, format,
}: { label: string; value: string | number; data: T[]; dataKey: keyof T & string; format?: (v: number) => string }) {
  return (
    <div className="bg-card px-4 pb-2 pt-3">
      <dt className="text-[12px] text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 text-[18px] font-semibold tabular-nums">{value}</dd>
      <Sparkline data={data} dataKey={dataKey} label={label} format={format} className="mt-1 h-8" />
    </div>
  )
}
