import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '../api/client'
import type { ActivityInput } from '../api/types'
import { Field, inputClass } from './Field'
import { Button, Notice } from './ui'

const MAX_PERCENT = 100
const NAME_MAX_LENGTH = 120
const MONEY_PATTERN = /^\d+(\.\d{1,2})?$/
const MONEY_MESSAGE = 'Use solo números, con hasta 2 decimales y punto decimal.'

const money = z.string().trim().regex(MONEY_PATTERN, MONEY_MESSAGE)
const percent = money.refine((value) => Number(value) <= MAX_PERCENT, 'Debe estar entre 0 y 100.')

const activitySchema = z.object({
  name: z.string().trim().min(1, 'Escriba un nombre.').max(NAME_MAX_LENGTH, 'Máximo 120 caracteres.'),
  budget_at_completion: money.refine((value) => Number(value) > 0, 'Debe ser mayor que cero.'),
  planned_progress: percent,
  actual_progress: percent,
  actual_cost: money,
})

interface FieldSpec {
  name: keyof ActivityInput
  label: string
  hint: string
  suffix?: string
}

const NUMBER_FIELDS: FieldSpec[] = [
  { name: 'budget_at_completion', label: 'Presupuesto total (BAC)', hint: 'Costo total planeado de la actividad.', suffix: 'COP' },
  { name: 'actual_cost', label: 'Costo real (AC)', hint: 'Lo gastado hasta la fecha de corte.', suffix: 'COP' },
  { name: 'planned_progress', label: 'Avance planificado', hint: 'Qué porcentaje debía estar hecho a la fecha de corte.', suffix: '%' },
  { name: 'actual_progress', label: 'Avance real', hint: 'Qué porcentaje está hecho de verdad.', suffix: '%' },
]

const EMPTY_ACTIVITY: ActivityInput = {
  name: '',
  budget_at_completion: '',
  planned_progress: '',
  actual_progress: '',
  actual_cost: '0',
}

interface ActivityFormProps {
  initial: ActivityInput | null
  pending: boolean
  error: Error | null
  onSubmit: (input: ActivityInput) => void
  onCancel: () => void
}

export function ActivityForm({ initial, pending, error, onSubmit, onCancel }: ActivityFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ActivityInput>({
    resolver: zodResolver(activitySchema),
    defaultValues: initial ?? EMPTY_ACTIVITY,
  })
  const serverErrors = error instanceof ApiError ? error.fieldErrors : {}
  const fieldError = (name: keyof ActivityInput) => errors[name]?.message ?? serverErrors[name]

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      {error && <Notice tone="bad">{error.message}</Notice>}
      <Field label="Nombre de la actividad" id="name" error={fieldError('name')}>
        <input id="name" autoFocus {...register('name')} className={inputClass} aria-invalid={Boolean(fieldError('name'))} />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        {NUMBER_FIELDS.map((field) => (
          <Field key={field.name} label={field.label} id={field.name} hint={field.hint} error={fieldError(field.name)}>
            <div className="relative">
              <input
                id={field.name}
                inputMode="decimal"
                {...register(field.name)}
                className={`${inputClass} tabular pr-12`}
                aria-invalid={Boolean(fieldError(field.name))}
              />
              <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs text-muted">
                {field.suffix}
              </span>
            </div>
          </Field>
        ))}
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onCancel} disabled={pending}>
          Cancelar
        </Button>
        <Button type="submit" disabled={pending}>
          {pending ? 'Guardando…' : 'Guardar actividad'}
        </Button>
      </div>
    </form>
  )
}
