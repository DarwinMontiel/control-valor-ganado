import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { Activity } from '../api/types'
import { formatCompactMoney, formatMoney, toNumber } from '../lib/format'

const CHART_HEIGHT = 320
const NAME_MAX_CHARS = 14

const SERIES = [
  { key: 'pv', label: 'PV · Planeado', color: 'var(--color-series-pv)' },
  { key: 'ev', label: 'EV · Ganado', color: 'var(--color-series-ev)' },
  { key: 'ac', label: 'AC · Costo real', color: 'var(--color-series-ac)' },
] as const

const shorten = (name: string) =>
  name.length > NAME_MAX_CHARS ? `${name.slice(0, NAME_MAX_CHARS - 1)}…` : name

/** Barras agrupadas por actividad: EV más bajo que AC = sobrecosto; más bajo que PV = retraso. */
export function EvmChart({ activities }: { activities: Activity[] }) {
  const data = activities.map((activity) => ({
    name: activity.name,
    pv: toNumber(activity.indicators.planned_value),
    ev: toNumber(activity.indicators.earned_value),
    ac: toNumber(activity.indicators.actual_cost),
  }))

  return (
    <figure>
      <div style={{ height: CHART_HEIGHT }} className="text-xs">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
            <CartesianGrid vertical={false} stroke="var(--color-line)" />
            <XAxis
              dataKey="name"
              tickFormatter={shorten}
              tick={{ fill: 'var(--color-muted)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-line)' }}
            />
            <YAxis
              tickFormatter={(value: number) => formatCompactMoney(String(value))}
              tick={{ fill: 'var(--color-muted)' }}
              tickLine={false}
              axisLine={false}
              width={64}
            />
            <Tooltip
              formatter={(value) => formatMoney(String(value))}
              cursor={{ fill: 'var(--color-neutral-soft)' }}
              contentStyle={{
                background: 'var(--color-surface)',
                border: '1px solid var(--color-line)',
                borderRadius: 8,
                color: 'var(--color-ink)',
              }}
            />
            <Legend wrapperStyle={{ paddingTop: 8 }} itemSorter={null} />
            {SERIES.map((series) => (
              <Bar
                key={series.key}
                dataKey={series.key}
                name={series.label}
                fill={series.color}
                radius={[3, 3, 0, 0]}
                maxBarSize={36}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="mt-2 text-sm text-muted">
        Si la barra azul (EV) queda por debajo de la naranja (AC), la actividad gastó más de lo que
        avanzó. Si queda por debajo de la gris (PV), va atrasada.
      </figcaption>
    </figure>
  )
}
