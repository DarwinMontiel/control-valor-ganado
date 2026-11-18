import { projectIndicators } from '../test/fixtures'
import { overallHealth } from './status'

describe('estado general del proyecto', () => {
  it('está en riesgo con sobrecosto y retraso', () => {
    expect(overallHealth(projectIndicators).tone).toBe('bad')
  })

  it('requiere atención si solo uno de los dos va mal', () => {
    const health = overallHealth({ ...projectIndicators, schedule_status: 'AHEAD' })

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

  it('va bien cuando costo y cronograma son favorables', () => {
    const health = overallHealth({
      ...projectIndicators,
      cost_status: 'UNDER_BUDGET',
      schedule_status: 'ON_SCHEDULE',
    })

    expect(health.tone).toBe('good')
  })

  it('no tiene veredicto si no hay avance', () => {
    const health = overallHealth({
      ...projectIndicators,
      cost_status: 'NOT_STARTED',
      schedule_status: 'NOT_STARTED',
    })

    expect(health.tone).toBe('neutral')
  })
})
