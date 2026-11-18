import { useMemo, useState } from 'react'

import type { Activity, DecimalString } from '../api/types'
import {
  UNRELIABLE_ESTIMATE_NOTE,
  formatIndex,
  formatMoney,
  formatPercent,
  formatSignedMoney,
  toNumber,
} from '../lib/format'
import { costView, scheduleView } from '../lib/status'
import { Badge, Button } from './ui'

interface Column {
  key: string
  label: string
  title: string
  value: (activity: Activity) => DecimalString | null
  format: (value: DecimalString | null) => string
  signed?: boolean
  unreliable?: (activity: Activity) => boolean
}

const hasUnreliableEstimate = (activity: Activity) =>
  activity.indicators.estimate_is_reliable === false

const COLUMNS: Column[] = [
  { key: 'bac', label: 'BAC', title: 'Presupuesto total', value: (a) => a.budget_at_completion, format: formatMoney },
  { key: 'plan', label: '% plan', title: 'Avance planificado a la fecha de corte', value: (a) => a.planned_progress, format: formatPercent },
  { key: 'real', label: '% real', title: 'Avance real completado', value: (a) => a.actual_progress, format: formatPercent },
  { key: 'pv', label: 'PV', title: 'Valor planeado', value: (a) => a.indicators.planned_value, format: formatMoney },
  { key: 'ev', label: 'EV', title: 'Valor ganado', value: (a) => a.indicators.earned_value, format: formatMoney },
  { key: 'ac', label: 'AC', title: 'Costo real', value: (a) => a.indicators.actual_cost, format: formatMoney },
  { key: 'cv', label: 'CV', title: 'Variación de costo (EV − AC)', value: (a) => a.indicators.cost_variance, format: formatSignedMoney, signed: true },
  { key: 'sv', label: 'SV', title: 'Variación de cronograma (EV − PV)', value: (a) => a.indicators.schedule_variance, format: formatSignedMoney, signed: true },
  { key: 'cpi', label: 'CPI', title: 'EV / AC', value: (a) => a.indicators.cost_performance_index, format: formatIndex },
  { key: 'spi', label: 'SPI', title: 'EV / PV', value: (a) => a.indicators.schedule_performance_index, format: formatIndex },
  { key: 'eac', label: 'EAC', title: 'Costo estimado al terminar (BAC / CPI)', value: (a) => a.indicators.estimate_at_completion, format: formatMoney, unreliable: hasUnreliableEstimate },
  { key: 'vac', label: 'VAC', title: 'Desviación al terminar (BAC − EAC)', value: (a) => a.indicators.variance_at_completion, format: formatSignedMoney, signed: true, unreliable: hasUnreliableEstimate },
]

type SortState = { key: string; direction: 'asc' | 'desc' } | null

/** Los valores no calculables (null) siempre van al final, sin importar la dirección. */
function compareActivities(column: Column, direction: 'asc' | 'desc') {
  const factor = direction === 'asc' ? 1 : -1
  return (left: Activity, right: Activity) => {
    const a = toNumber(column.value(left))
    const b = toNumber(column.value(right))
    if (a === null || b === null) {
      return Number(a === null) - Number(b === null)
    }
    return (a - b) * factor
  }
}

function signClass(column: Column, value: DecimalString | null): string {
  const number = toNumber(value)
  if (!column.signed || number === null || number === 0) {
    return ''
  }
  return number < 0 ? 'text-bad' : 'text-good'
}

interface ActivityTableProps {
  activities: Activity[]
  onEdit: (activity: Activity) => void
  onDelete: (activity: Activity) => void
}

export function ActivityTable({ activities, onEdit, onDelete }: ActivityTableProps) {
  const [sort, setSort] = useState<SortState>(null)

  const rows = useMemo(() => {
    const column = COLUMNS.find((item) => item.key === sort?.key)
    return column && sort ? activities.toSorted(compareActivities(column, sort.direction)) : activities
  }, [activities, sort])

  const toggleSort = (key: string) =>
    setSort((current) =>
      current?.key === key && current.direction === 'asc'
        ? { key, direction: 'desc' }
        : current?.key === key
          ? null
          : { key, direction: 'asc' },
    )

  return (
    <div className="relative overflow-x-auto">
      <table className="tabular w-full min-w-[72rem] border-collapse text-sm">
        <caption className="sr-only">Actividades con sus indicadores de valor ganado</caption>
        <thead>
          <tr className="border-b border-line text-left text-xs text-muted">
            <th scope="col" className="sticky left-0 bg-surface py-2 pr-4 font-semibold">
              Actividad
            </th>
            {COLUMNS.map((column) => {
              const active = sort?.key === column.key
              return (
                <th
                  key={column.key}
                  scope="col"
                  className="px-2 py-2 text-right font-semibold"
                  aria-sort={active ? (sort.direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                >
                  <button
                    type="button"
                    title={`${column.title}. Clic para ordenar.`}
                    onClick={() => toggleSort(column.key)}
                    className="rounded px-1 hover:text-ink"
                  >
                    {column.label}
                    <span aria-hidden="true">{active ? (sort.direction === 'asc' ? ' ↑' : ' ↓') : ''}</span>
                  </button>
                </th>
              )
            })}
            <th scope="col" className="px-2 py-2 font-semibold">Estado</th>
            <th scope="col" className="py-2 pl-2 text-right font-semibold">
              <span className="sr-only">Acciones</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((activity) => (
            <tr key={activity.id} className="border-b border-line last:border-0 hover:bg-paper">
              <th scope="row" className="sticky left-0 max-w-56 truncate bg-surface py-3 pr-4 text-left font-semibold">
                {activity.name}
              </th>
              {COLUMNS.map((column) => {
                const value = column.value(activity)
                return (
                  <td key={column.key} className={`whitespace-nowrap px-2 py-3 text-right ${signClass(column, value)}`}>
                    {column.format(value)}
                    {column.unreliable?.(activity) && (
                      <span title={UNRELIABLE_ESTIMATE_NOTE} className="ml-0.5 text-warning">
                        *<span className="sr-only"> {UNRELIABLE_ESTIMATE_NOTE}</span>
                      </span>
                    )}
                  </td>
                )
              })}
              <td className="px-2 py-3">
                <div className="flex flex-col items-start gap-1">
                  <Badge tone={costView(activity.indicators).tone}>
                    {costView(activity.indicators).label}
                  </Badge>
                  <Badge tone={scheduleView(activity.indicators).tone}>
                    {scheduleView(activity.indicators).label}
                  </Badge>
                </div>
              </td>
              <td className="whitespace-nowrap py-3 pl-2 text-right">
                <Button variant="ghost" onClick={() => onEdit(activity)} aria-label={`Editar ${activity.name}`}>
                  Editar
                </Button>
                <Button variant="ghost" onClick={() => onDelete(activity)} aria-label={`Eliminar ${activity.name}`}>
                  Eliminar
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
