import type { EventRead } from '@/lib/types'
import { useStats } from '@/hooks/useStats'
import { useDownloadSeries } from '@/hooks/useDownloadSeries'
import { useEvents } from '@/hooks/useEvents'
import { EmptyState } from '@/components/shared/EmptyState'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { Layers, Download, HardDrive, AlertTriangle, type LucideIcon } from 'lucide-react'

function formatBytes(n: number): string {
  if (n <= 0) return '0 B'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), u.length - 1)
  return `${(n / 1024 ** i).toFixed(1)} ${u[i]}`
}

function StatCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string
  value: string | number
  hint: string
  icon: LucideIcon
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold tracking-tight">{value}</div>
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      </CardContent>
    </Card>
  )
}

function ActivityCard({ events, truncate }: { events: EventRead[] | undefined; truncate?: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent activity</CardTitle>
      </CardHeader>
      <CardContent>
        {events && events.length > 0 ? (
          <div className="space-y-3">
            {events.map((e) => (
              <div key={e.id} className="flex items-start gap-3 border-b border-border pb-3 last:border-0">
                <span className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full bg-primary" />
                <div className="min-w-0 flex-1">
                  <p className={truncate ? 'truncate text-sm' : 'text-sm'}>{e.message}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {new Date(e.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No activity yet" message="Events appear here as subscriptions run." />
        )}
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  const stats = useStats()
  const series = useDownloadSeries(14)
  const events = useEvents({ limit: 8 })

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Active subscriptions" value={stats.activeSubs} hint="Currently enabled" icon={Layers} />
        <StatCard label="Downloaded" value={stats.downloaded} hint="Media items stored" icon={Download} />
        <StatCard label="Storage used" value={formatBytes(stats.storageBytes)} hint="Across all downloads" icon={HardDrive} />
        <StatCard label="Failed" value={stats.failed} hint="Need attention" icon={AlertTriangle} />
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4 grid gap-4 lg:grid-cols-7">
          <Card className="lg:col-span-4">
            <CardHeader>
              <CardTitle>Downloads — last 14 days</CardTitle>
            </CardHeader>
            <CardContent className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={series.data} margin={{ left: -20, right: 8, top: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis
                    dataKey="day"
                    tickFormatter={(d: string) => d.slice(5)}
                    fontSize={12}
                    className="fill-muted-foreground"
                  />
                  <YAxis allowDecimals={false} fontSize={12} className="fill-muted-foreground" />
                  <Tooltip
                    contentStyle={{
                      background: 'hsl(var(--popover))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: 8,
                      color: 'hsl(var(--popover-foreground))',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="hsl(var(--primary))"
                    fill="hsl(var(--primary))"
                    fillOpacity={0.15}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="lg:col-span-3">
            <ActivityCard events={events.data} truncate />
          </div>
        </TabsContent>

        <TabsContent value="activity" className="mt-4">
          <ActivityCard events={events.data} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
