/**
 * Formato de cifras para mostrar. El frontend no calcula EVM: solo presenta lo que devuelve
 * la API. Un valor `null` se muestra como "—" (no calculable), nunca como 0.
 */

import type { DecimalString } from '../api/types'

export const NOT_AVAILABLE = '—'
export const UNRELIABLE_ESTIMATE_NOTE = 'Poco confiable: el avance real es menor al 10 %.'
const LOCALE = 'es-CO'
const INDEX_DECIMALS = 2
const PERCENT_DECIMALS = 0

const moneyFormat = new Intl.NumberFormat(LOCALE, {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
})
const compactMoneyFormat = new Intl.NumberFormat(LOCALE, {
  notation: 'compact',
  maximumFractionDigits: 1,
})
const indexFormat = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: INDEX_DECIMALS,
  maximumFractionDigits: INDEX_DECIMALS,
})
const percentFormat = new Intl.NumberFormat(LOCALE, {
  maximumFractionDigits: PERCENT_DECIMALS,
})

export const toNumber = (value: DecimalString | null): number | null =>
  value === null ? null : Number(value)

const withFallback =
  (format: (value: number) => string) =>
  (value: DecimalString | null): string => {
    const number = toNumber(value)
    return number === null ? NOT_AVAILABLE : format(number)
  }

export const formatMoney = withFallback((value) => moneyFormat.format(value))
export const formatCompactMoney = withFallback((value) => `$${compactMoneyFormat.format(value)}`)
export const formatIndex = withFallback((value) => indexFormat.format(value))
export const formatPercent = withFallback((value) => `${percentFormat.format(value)} %`)

export function formatSignedMoney(value: DecimalString | null): string {
  const number = toNumber(value)
  if (number === null) {
    return NOT_AVAILABLE
  }
  const sign = number > 0 ? '+' : ''
  return `${sign}${moneyFormat.format(number)}`
}

export function formatDate(value: string | null): string {
  if (!value) {
    return NOT_AVAILABLE
  }
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year ?? 0, (month ?? 1) - 1, day ?? 1).toLocaleDateString(LOCALE, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
