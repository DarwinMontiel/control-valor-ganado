import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '../api/client'
import type { ProjectInput } from '../api/types'
import { Field, inputClass } from './Field'
import { Button, Notice } from './ui'

const NAME_MAX_LENGTH = 120
const DESCRIPTION_MAX_LENGTH = 2000

const projectSchema = z
  .object({
    name: z.string().trim().min(1, 'Escriba un nombre.').max(NAME_MAX_LENGTH, 'Máximo 120 caracteres.'),
    description: z.string().trim().max(DESCRIPTION_MAX_LENGTH, 'Máximo 2000 caracteres.'),
    start_date: z.string(),
    end_date: z.string(),
    cutoff_date: z.string(),
  })
  .refine((value) => !value.start_date || !value.end_date || value.end_date >= value.start_date, {
    path: ['end_date'],
    message: 'La fecha de fin no puede ser anterior a la de inicio.',
  })

type ProjectFormValues = z.infer<typeof projectSchema>

const toFormValues = (input: ProjectInput | null): ProjectFormValues => ({
  name: input?.name ?? '',
  description: input?.description ?? '',
  start_date: input?.start_date ?? '',
  end_date: input?.end_date ?? '',
  cutoff_date: input?.cutoff_date ?? '',
})

/** Los campos vacíos del formulario viajan como null: la API decide el valor por defecto. */
const toInput = (values: ProjectFormValues): ProjectInput => ({
  name: values.name,
  description: values.description || null,
  start_date: values.start_date || null,
  end_date: values.end_date || null,
  cutoff_date: values.cutoff_date || null,
})

interface ProjectFormProps {
  initial: ProjectInput | null
  pending: boolean
  error: Error | null
  onSubmit: (input: ProjectInput) => void
  onCancel: () => void
}

export function ProjectForm({ initial, pending, error, onSubmit, onCancel }: ProjectFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: toFormValues(initial),
  })
  const serverErrors = error instanceof ApiError ? error.fieldErrors : {}
  const fieldError = (name: keyof ProjectFormValues) => errors[name]?.message ?? serverErrors[name]

  return (
    <form onSubmit={handleSubmit((values) => onSubmit(toInput(values)))} noValidate className="space-y-4">
      {error && <Notice tone="bad">{error.message}</Notice>}
      <Field id="project-name" label="Nombre del proyecto" error={fieldError('name')}>
        <input id="project-name" autoFocus {...register('name')} className={inputClass} aria-invalid={Boolean(fieldError('name'))} />
      </Field>
      <Field id="project-description" label="Descripción (opcional)" error={fieldError('description')}>
        <textarea id="project-description" rows={2} {...register('description')} className={inputClass} />
      </Field>
      <div className="grid gap-4 sm:grid-cols-3">
        <Field id="start_date" label="Inicio" error={fieldError('start_date')}>
          <input id="start_date" type="date" {...register('start_date')} className={inputClass} />
        </Field>
        <Field id="end_date" label="Fin" error={fieldError('end_date')}>
          <input id="end_date" type="date" {...register('end_date')} className={inputClass} aria-invalid={Boolean(fieldError('end_date'))} />
        </Field>
        <Field id="cutoff_date" label="Fecha de corte" hint="Si la deja vacía, es hoy." error={fieldError('cutoff_date')}>
          <input id="cutoff_date" type="date" {...register('cutoff_date')} className={inputClass} />
        </Field>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onCancel} disabled={pending}>
          Cancelar
        </Button>
        <Button type="submit" disabled={pending}>
          {pending ? 'Guardando…' : 'Guardar proyecto'}
        </Button>
      </div>
    </form>
  )
}
