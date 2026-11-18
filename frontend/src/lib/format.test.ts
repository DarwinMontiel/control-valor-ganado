import { NOT_AVAILABLE, formatIndex, formatMoney, formatPercent, formatSignedMoney } from './format'

const normalizeSpaces = (text: string) => text.replace(/\s/g, ' ')

describe('formato de cifras', () => {
  it('muestra los índices no calculables como "—", nunca como 0', () => {
    expect(formatIndex(null)).toBe(NOT_AVAILABLE)
    expect(formatMoney(null)).toBe(NOT_AVAILABLE)
    expect(formatSignedMoney(null)).toBe(NOT_AVAILABLE)
  })

  it('redondea los índices a dos decimales con coma decimal', () => {
    expect(formatIndex('0.9474')).toBe('0,95')
    expect(formatIndex('0.0000')).toBe('0,00')
  })

  it('formatea pesos colombianos sin decimales', () => {
    expect(normalizeSpaces(formatMoney('36944444.44'))).toBe('$ 36.944.444')
  })

  it('marca el signo de las variaciones positivas', () => {
    expect(normalizeSpaces(formatSignedMoney('1000000.00'))).toBe('+$ 1.000.000')
    expect(normalizeSpaces(formatSignedMoney('0.00'))).toBe('$ 0')
    expect(normalizeSpaces(formatSignedMoney('-5000000.00'))).toBe('-$ 5.000.000')
  })

  it('muestra porcentajes', () => {
    expect(normalizeSpaces(formatPercent('60.00'))).toBe('60 %')
  })
})
