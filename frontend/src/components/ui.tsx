import type { ButtonHTMLAttributes, ReactNode } from 'react'

import type { Tone } from '../lib/status'
import { toneClasses } from '../lib/tone'

const TONE_ICONS: Record<Tone, string> = {
  good: '▲',
  warning: '●',
  bad: '▼',
  neutral: '○',
}

/** Insignia de estado: color + símbolo + texto, para no depender solo del color. */
export function Badge({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${toneClasses(tone)}`}
    >
      <span aria-hidden="true" className="text-[0.6rem]">
        {TONE_ICONS[tone]}
      </span>
      {children}
    </span>
  )
}

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'

const BUTTON_CLASSES: Record<ButtonVariant, string> = {
  primary: 'bg-brand text-surface hover:bg-brand-strong',
  secondary: 'border border-line bg-surface text-ink hover:bg-neutral-soft',
  danger: 'bg-bad text-surface hover:opacity-90',
  ghost: 'text-muted hover:bg-neutral-soft hover:text-ink',
}

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-3.5 py-2 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${BUTTON_CLASSES[variant]} ${className}`}
      {...props}
    />
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-line bg-surface p-5 ${className}`}>
      {children}
    </section>
  )
}

export function SectionTitle({ children, hint }: { children: ReactNode; hint?: ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
      <h2 className="text-base font-semibold">{children}</h2>
      {hint && <p className="text-sm text-muted">{hint}</p>}
    </div>
  )
}

export function Notice({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <div role={tone === 'bad' ? 'alert' : 'status'} className={`rounded-lg px-4 py-3 text-sm ${toneClasses(tone)}`}>
      {children}
    </div>
  )
}

export function Spinner({ label }: { label: string }) {
  return (
    <div role="status" className="flex items-center gap-3 py-10 text-sm text-muted">
      <span className="size-4 animate-spin rounded-full border-2 border-line border-t-brand" />
      {label}
    </div>
  )
}
