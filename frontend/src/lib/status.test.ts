import { projectIndicators } from '../test/fixtures'
import { costView, overallHealth } from './status'

describe('estado general del proyecto', () => {
  it('está en riesgo con sobrecosto y retraso', () => {
    expect(overallHealth(projectIndicators).tone).toBe('bad')
  })

  it('requiere atención si solo uno de los dos va mal', () => {
    const health = overallHealth({
      ...projectIndicators,
      schedule_status: 'AHEAD',
      schedule_band: 'FAVORABLE',
    })

    expect(health).toEqual({ tone: 'warning', title: 'Requiere atención' })
  })

  it('requiere atención si falta el costo real', () => {
    const health = overallHealth({
      ...projectIndicators,
      cost_status: 'NOT_CALCULABLE',
      schedule_status: 'ON_SCHEDULE',
    })

    expect(health.tone).toBe('warning')
  })

  it('un sobrecosto dentro del 5 % se ve en amarillo como "En línea", no en rojo', () => {
    const indicators = {
      ...projectIndicators,
      cost_performance_index: '0.9901',
      cost_band: 'WITHIN_TOLERANCE' as const,
      schedule_status: 'AHEAD' as const,
      schedule_band: 'FAVORABLE' as const,
    }

    expect(costView(indicators)).toEqual({ label: 'En línea', tone: 'warning' })
    expect(overallHealth(indicators)).toEqual({
      tone: 'warning',
      title: 'En línea, con desviaciones menores',
    })
  })

  it('fuera de la tolerancia manda el estado estricto', () => {
    expect(costView(projectIndicators)).toEqual({ label: 'Sobre presupuesto', tone: 'bad' })
  })

  it('va bien cuando costo y cronograma son favorables', () => {
    const health = overallHealth({
      ...projectIndicators,
      cost_status: 'UNDER_BUDGET',
      schedule_status: 'AHEAD',
      cost_band: 'FAVORABLE',
      schedule_band: 'FAVORABLE',
    })

    expect(health.tone).toBe('good')
  })

  it('no tiene veredicto si no hay avance', () => {
    const health = overallHealth({
      ...projectIndicators,
      cost_status: 'NOT_STARTED',
      schedule_status: 'NOT_STARTED',
      cost_band: 'NOT_AVAILABLE',
      schedule_band: 'NOT_AVAILABLE',
    })

    expect(health.tone).toBe('neutral')
  })
})
