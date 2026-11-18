import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { design, projectIndicators, referenceProject, testing } from '../test/fixtures'
import { ActivityForm } from './ActivityForm'
import { ActivityTable } from './ActivityTable'
import { AlertList } from './AlertList'
import { IndicatorPanel } from './IndicatorPanel'

const renderTable = () =>
  render(<ActivityTable activities={[design, testing]} onEdit={vi.fn()} onDelete={vi.fn()} />)

const rowNames = () => screen.getAllByRole('rowheader').map((cell) => cell.textContent)

const renderForm = (onSubmit = vi.fn()) => {
  render(<ActivityForm initial={null} pending={false} error={null} onSubmit={onSubmit} onCancel={vi.fn()} />)
  return onSubmit
}

describe('IndicatorPanel', () => {
  it('muestra el veredicto, los índices y su interpretación', () => {
    render(<IndicatorPanel indicators={projectIndicators} />)

    expect(screen.getByText('En riesgo: sobrecosto y retraso')).toBeInTheDocument()
    expect(screen.getByText('0,95')).toBeInTheDocument()
    expect(screen.getByText('0,78')).toBeInTheDocument()
    expect(screen.getByText('Sobre presupuesto')).toBeInTheDocument()
    expect(screen.getByText('Atrasado')).toBeInTheDocument()
    expect(screen.getByText(projectIndicators.cost_interpretation)).toBeInTheDocument()
  })

  it('muestra "—" cuando el CPI no se puede calcular', () => {
    render(<IndicatorPanel indicators={testing.indicators} />)

    const costGauge = screen.getByText('Costo · CPI').closest('div.rounded-xl')
    expect(costGauge).not.toBeNull()
    expect(within(costGauge as HTMLElement).getByText('—')).toBeInTheDocument()
  })
})

describe('EAC poco confiable', () => {
  it('avisa en el panel cuando el avance real es menor al 10 %', () => {
    render(<IndicatorPanel indicators={{ ...projectIndicators, estimate_is_reliable: false }} />)

    expect(screen.getAllByText(/Poco confiable/)).toHaveLength(2)
  })

  it('no avisa cuando el EAC es confiable', () => {
    render(<IndicatorPanel indicators={projectIndicators} />)

    expect(screen.queryByText(/Poco confiable/)).not.toBeInTheDocument()
  })

  it('marca con asterisco el EAC de la actividad en la tabla', () => {
    const early = { ...design, indicators: { ...design.indicators, estimate_is_reliable: false } }
    render(<ActivityTable activities={[early]} onEdit={vi.fn()} onDelete={vi.fn()} />)

    expect(screen.getAllByTitle(/Poco confiable/)).toHaveLength(2)
  })
})

describe('ActivityTable', () => {
  it('muestra una fila por actividad con sus indicadores', () => {
    renderTable()

    const designRow = screen.getByRole('row', { name: /Diseño/ })
    expect(within(designRow).getByText('1,11')).toBeInTheDocument()
    expect(within(designRow).getByText('Bajo presupuesto')).toBeInTheDocument()
    const testingRow = screen.getByRole('row', { name: /Pruebas/ })
    expect(within(testingRow).getAllByText('—').length).toBeGreaterThanOrEqual(3)
  })

  it('ordena por CPI y deja los no calculables al final', async () => {
    renderTable()
    const cpiHeader = screen.getByRole('button', { name: /^CPI/ })

    await userEvent.click(cpiHeader)
    expect(rowNames()).toEqual(['Diseño', 'Pruebas'])
    await userEvent.click(cpiHeader)
    expect(rowNames()).toEqual(['Diseño', 'Pruebas'])
  })

  it('ordena por SPI ascendente y descendente', async () => {
    renderTable()
    const spiHeader = screen.getByRole('button', { name: /^SPI/ })

    await userEvent.click(spiHeader)
    expect(rowNames()).toEqual(['Pruebas', 'Diseño'])
    await userEvent.click(spiHeader)
    expect(rowNames()).toEqual(['Diseño', 'Pruebas'])
  })

  it('avisa qué actividad se quiere editar o eliminar', async () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()
    render(<ActivityTable activities={[design]} onEdit={onEdit} onDelete={onDelete} />)

    await userEvent.click(screen.getByRole('button', { name: 'Editar Diseño' }))
    await userEvent.click(screen.getByRole('button', { name: 'Eliminar Diseño' }))

    expect(onEdit).toHaveBeenCalledWith(design)
    expect(onDelete).toHaveBeenCalledWith(design)
  })
})

describe('ActivityForm', () => {
  it('envía los valores como texto decimal', async () => {
    const onSubmit = renderForm()

    await userEvent.type(screen.getByLabelText('Nombre de la actividad'), 'Diseño')
    await userEvent.type(screen.getByLabelText('Presupuesto total (BAC)'), '1000.50')
    await userEvent.type(screen.getByLabelText('Avance planificado'), '50')
    await userEvent.type(screen.getByLabelText('Avance real'), '40')
    await userEvent.click(screen.getByRole('button', { name: 'Guardar actividad' }))

    expect(onSubmit).toHaveBeenCalledWith(
      {
        name: 'Diseño',
        budget_at_completion: '1000.50',
        planned_progress: '50',
        actual_progress: '40',
        actual_cost: '0',
      },
      expect.anything(),
    )
  })

  it('no envía avances fuera de 0–100 ni presupuesto en cero', async () => {
    const onSubmit = renderForm()

    await userEvent.type(screen.getByLabelText('Nombre de la actividad'), 'X')
    await userEvent.type(screen.getByLabelText('Presupuesto total (BAC)'), '0')
    await userEvent.type(screen.getByLabelText('Avance planificado'), '120')
    await userEvent.type(screen.getByLabelText('Avance real'), '1,5')
    await userEvent.click(screen.getByRole('button', { name: 'Guardar actividad' }))

    expect(onSubmit).not.toHaveBeenCalled()
    expect(screen.getByText('Debe ser mayor que cero.')).toBeInTheDocument()
    expect(screen.getByText('Debe estar entre 0 y 100.')).toBeInTheDocument()
    expect(screen.getByText(/punto decimal/)).toBeInTheDocument()
  })
})

describe('AlertList', () => {
  it('distingue alertas del proyecto y de cada actividad, con su valor observado', () => {
    render(<AlertList alerts={referenceProject.alerts} />)

    expect(screen.getByText('Proyecto completo')).toBeInTheDocument()
    expect(screen.getByText('Pruebas')).toBeInTheDocument()
    expect(screen.getByText('0,95')).toBeInTheDocument()
    expect(screen.getByText('Alta')).toBeInTheDocument()
  })

  it('dice explícitamente cuando no hay alertas', () => {
    render(<AlertList alerts={[]} />)

    expect(screen.getByText(/Sin alertas/)).toBeInTheDocument()
  })
})
