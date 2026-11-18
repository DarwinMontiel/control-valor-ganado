import type { Tone } from './status'

const TONE_CLASSES: Record<Tone, string> = {
  good: 'bg-good-soft text-good',
  warning: 'bg-warning-soft text-warning',
  bad: 'bg-bad-soft text-bad',
  neutral: 'bg-neutral-soft text-neutral',
}

const TONE_TEXT_CLASSES: Record<Tone, string> = {
  good: 'text-good',
  warning: 'text-warning',
  bad: 'text-bad',
  neutral: 'text-ink',
}

export const toneClasses = (tone: Tone) => TONE_CLASSES[tone]
export const toneTextClass = (tone: Tone) => TONE_TEXT_CLASSES[tone]
