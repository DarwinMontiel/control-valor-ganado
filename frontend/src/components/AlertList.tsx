import type { Alert, AlertSeverity } from '../api/types'
import { formatIndex, formatMoney } from '../lib/format'
import type { Tone } from '../lib/status'
import { Badge } from './ui'

const SEVERITY_VIEW: Record<AlertSeverity, { label: string; tone: Tone }> = {
  HIGH: { label: 'Alta', tone: 'bad' },
  MEDIUM: { label: 'Media', tone: 'warning' },
}

const INDEX_INDICATORS = new Set(['CPI', 'SPI'])

const formatObserved = (alert: Alert) =>
  INDEX_INDICATORS.has(alert.indicator)
    ? formatIndex(alert.observed_value)
    : formatMoney(alert.observed_value)

/** Alertas que calcula el backend con reglas fijas; aquí solo se presentan. */
export function AlertList({ alerts }: { alerts: Alert[] }) {
  if (alerts.length === 0) {
    return <p className="text-sm text-muted">Sin alertas: ningún indicador está fuera de lo esperado.</p>
  }
  return (
    <ul className="divide-y divide-line">
      {alerts.map((alert) => (
        <li
          key={`${alert.activity_id ?? 'project'}-${alert.type}`}
          className="flex flex-wrap items-start gap-x-3 gap-y-1 py-3 first:pt-0 last:pb-0"
        >
          <Badge tone={SEVERITY_VIEW[alert.severity].tone}>{SEVERITY_VIEW[alert.severity].label}</Badge>
          <div className="min-w-0 flex-1">
            <p className="text-sm">
              <strong>{alert.activity_id ? alert.scope_name : 'Proyecto completo'}</strong>
              <span className="text-muted">
                {' '}
                · {alert.indicator} = <span className="tabular">{formatObserved(alert)}</span>
              </span>
            </p>
            <p className="text-sm text-muted">{alert.message}</p>
          </div>
        </li>
      ))}
    </ul>
  )
}
