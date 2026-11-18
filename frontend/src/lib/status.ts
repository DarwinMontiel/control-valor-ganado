/** Traduce los estados que calcula la API a tono visual y texto corto. */

import type { CostStatus, Indicators, PerformanceBand, ScheduleStatus } from '../api/types'

export type Tone = 'good' | 'warning' | 'bad' | 'neutral'

interface StatusView {
  label: string
  tone: Tone
}

export const COST_STATUS_VIEW: Record<CostStatus, StatusView> = {
  UNDER_BUDGET: { label: 'Bajo presupuesto', tone: 'good' },
  ON_BUDGET: { label: 'En presupuesto', tone: 'good' },
  OVER_BUDGET: { label: 'Sobre presupuesto', tone: 'bad' },
  NOT_STARTED: { label: 'Sin iniciar', tone: 'neutral' },
  NOT_CALCULABLE: { label: 'Falta el costo', tone: 'warning' },
}

export const SCHEDULE_STATUS_VIEW: Record<ScheduleStatus, StatusView> = {
  AHEAD: { label: 'Adelantado', tone: 'good' },
  ON_SCHEDULE: { label: 'A tiempo', tone: 'good' },
  BEHIND: { label: 'Atrasado', tone: 'bad' },
  NOT_STARTED: { label: 'Sin iniciar', tone: 'neutral' },
}

const WITHIN_TOLERANCE_VIEW: StatusView = { label: 'En línea', tone: 'warning' }

/**
 * Semáforo de un índice. Si la API dice que está dentro de la tolerancia (±5 %), se muestra en
 * amarillo como "En línea"; si no, manda el estado estricto (bajo/sobre presupuesto, etc.).
 */
const withBand = (band: PerformanceBand, strict: StatusView): StatusView =>
  band === 'WITHIN_TOLERANCE' ? WITHIN_TOLERANCE_VIEW : strict

export const costView = (indicators: Indicators): StatusView =>
  withBand(indicators.cost_band, COST_STATUS_VIEW[indicators.cost_status])

export const scheduleView = (indicators: Indicators): StatusView =>
  withBand(indicators.schedule_band, SCHEDULE_STATUS_VIEW[indicators.schedule_status])

export interface HealthView {
  tone: Tone
  title: string
}

/** El mensaje "de un vistazo": combina los dos estados que ya calculó el backend. */
export function overallHealth(indicators: Indicators): HealthView {
  const tones = [costView(indicators).tone, scheduleView(indicators).tone]
  const badCount = tones.filter((tone) => tone === 'bad').length
  if (badCount === tones.length) {
    return { tone: 'bad', title: 'En riesgo: sobrecosto y retraso' }
  }
  if (badCount > 0 || indicators.cost_status === 'NOT_CALCULABLE') {
    return { tone: 'warning', title: 'Requiere atención' }
  }
  if (tones.includes('warning')) {
    return { tone: 'warning', title: 'En línea, con desviaciones menores' }
  }
  if (tones.every((tone) => tone === 'neutral')) {
    return { tone: 'neutral', title: 'Sin avance registrado' }
  }
  return { tone: 'good', title: 'Va bien en costo y cronograma' }
}
