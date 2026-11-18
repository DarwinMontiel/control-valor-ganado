import type { Indicators } from '../api/types'
import { UNRELIABLE_ESTIMATE_NOTE, formatIndex, formatMoney, formatSignedMoney } from '../lib/format'
import { costView, overallHealth, scheduleView, type Tone } from '../lib/status'
import { toneClasses, toneTextClass } from '../lib/tone'
import { Badge } from './ui'

interface GaugeProps {
  label: string
  name: string
  value: string | null
  tone: Tone
  statusLabel: string
  interpretation: string
}

function IndexGauge({ label, name, value, tone, statusLabel, interpretation }: GaugeProps) {
  return (
    <div className="rounded-xl border border-line bg-surface p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{label}</p>
          <p className="text-xs text-muted">{name}</p>
        </div>
        <Badge tone={tone}>{statusLabel}</Badge>
      </div>
      <p className={`tabular mt-3 text-4xl font-semibold ${toneTextClass(tone)}`}>
        {formatIndex(value)}
      </p>
      <p className="mt-2 text-sm text-muted">{interpretation}</p>
    </div>
  )
}

interface FigureProps {
  label: string
  hint: string
  value: string
  note?: string
}

function Figure({ label, hint, value, note }: FigureProps) {
  return (
    <div className="min-w-0">
      <dt className="text-xs font-medium text-muted" title={hint}>
        {label}
      </dt>
      <dd className="tabular mt-1 truncate text-lg font-semibold">{value}</dd>
      {note && <dd className="mt-0.5 text-xs font-medium text-warning">{note}</dd>}
    </div>
  )
}

/** Indicadores consolidados del proyecto, con el veredicto "de un vistazo" arriba. */
export function IndicatorPanel({ indicators }: { indicators: Indicators }) {
  const health = overallHealth(indicators)
  const cost = costView(indicators)
  const schedule = scheduleView(indicators)

  return (
    <div className="space-y-4">
      <div className={`rounded-xl px-5 py-4 ${toneClasses(health.tone)}`} role="status">
        <p className="text-xs font-semibold uppercase tracking-wider opacity-80">
          Estado del proyecto
        </p>
        <p className="mt-0.5 text-xl font-semibold">{health.title}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <IndexGauge
          label="Costo · CPI"
          name="Índice de desempeño del costo = EV / AC"
          value={indicators.cost_performance_index}
          tone={cost.tone}
          statusLabel={cost.label}
          interpretation={indicators.cost_interpretation}
        />
        <IndexGauge
          label="Cronograma · SPI"
          name="Índice de desempeño del cronograma = EV / PV"
          value={indicators.schedule_performance_index}
          tone={schedule.tone}
          statusLabel={schedule.label}
          interpretation={indicators.schedule_interpretation}
        />
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-5 rounded-xl border border-line bg-surface p-5 sm:grid-cols-4">
        <Figure label="Presupuesto (BAC)" hint="Costo total planeado" value={formatMoney(indicators.budget_at_completion)} />
        <Figure label="Valor planeado (PV)" hint="Trabajo que debía estar hecho, en dinero" value={formatMoney(indicators.planned_value)} />
        <Figure label="Valor ganado (EV)" hint="Trabajo realmente hecho, en dinero" value={formatMoney(indicators.earned_value)} />
        <Figure label="Costo real (AC)" hint="Lo gastado a la fecha de corte" value={formatMoney(indicators.actual_cost)} />
        <Figure label="Variación de costo (CV)" hint="EV − AC" value={formatSignedMoney(indicators.cost_variance)} />
        <Figure label="Variación de cronograma (SV)" hint="EV − PV" value={formatSignedMoney(indicators.schedule_variance)} />
        <Figure
          label="Costo estimado final (EAC)"
          hint="BAC / CPI"
          value={formatMoney(indicators.estimate_at_completion)}
          note={indicators.estimate_is_reliable === false ? UNRELIABLE_ESTIMATE_NOTE : undefined}
        />
        <Figure
          label="Desviación final (VAC)"
          hint="BAC − EAC"
          value={formatSignedMoney(indicators.variance_at_completion)}
          note={indicators.estimate_is_reliable === false ? UNRELIABLE_ESTIMATE_NOTE : undefined}
        />
      </dl>
    </div>
  )
}
