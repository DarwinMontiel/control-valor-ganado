import { Suspense, lazy, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import {
  useDeleteActivity,
  useDeleteProject,
  useProject,
  useSaveActivity,
  useUpdateProject,
} from '../api/hooks'
import type { Activity, ProjectDetail } from '../api/types'
import { ActivityForm } from '../components/ActivityForm'
import { ActivityTable } from '../components/ActivityTable'
import { AlertList } from '../components/AlertList'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { IndicatorPanel } from '../components/IndicatorPanel'
import { Modal } from '../components/Modal'
import { ProjectForm } from '../components/ProjectForm'
import { Button, Card, Notice, SectionTitle, Spinner } from '../components/ui'
import { formatDate } from '../lib/format'

// Recharts pesa más que el resto de la app junta: se carga solo cuando hay actividades.
const EvmChart = lazy(() =>
  import('../components/EvmChart').then((module) => ({ default: module.EvmChart })),
)

type ActivityEditor = { mode: 'closed' } | { mode: 'create' } | { mode: 'edit'; activity: Activity }

export function ProjectPage() {
  const { projectId = '' } = useParams()
  const project = useProject(projectId)

  if (project.isPending) {
    return <Spinner label="Cargando proyecto…" />
  }
  if (project.isError) {
    return (
      <div className="space-y-4">
        <Notice tone="bad">{project.error.message}</Notice>
        <Link to="/" className="text-sm font-semibold text-brand">
          ← Volver a proyectos
        </Link>
      </div>
    )
  }
  return <ProjectView project={project.data} />
}

function ProjectView({ project }: { project: ProjectDetail }) {
  const navigate = useNavigate()
  const [editor, setEditor] = useState<ActivityEditor>({ mode: 'closed' })
  const [activityToDelete, setActivityToDelete] = useState<Activity | null>(null)
  const [editingProject, setEditingProject] = useState(false)
  const [deletingProject, setDeletingProject] = useState(false)

  const saveActivity = useSaveActivity(project.id)
  const deleteActivity = useDeleteActivity()
  const updateProject = useUpdateProject(project.id)
  const deleteProject = useDeleteProject()

  const closeEditor = () => {
    setEditor({ mode: 'closed' })
    saveActivity.reset()
  }
  const closeProjectForm = () => {
    setEditingProject(false)
    updateProject.reset()
  }

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <Link to="/" className="text-sm font-semibold text-brand">
          ← Proyectos
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold">{project.name}</h1>
            {project.description && <p className="mt-1 text-sm text-muted">{project.description}</p>}
            <p className="mt-2 text-sm text-muted">
              Fecha de corte: <strong className="text-ink">{formatDate(project.cutoff_date)}</strong>
              {project.start_date && ` · Inicio ${formatDate(project.start_date)}`}
              {project.end_date && ` · Fin ${formatDate(project.end_date)}`}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setEditingProject(true)}>
              Editar proyecto
            </Button>
            <Button variant="ghost" onClick={() => setDeletingProject(true)}>
              Eliminar
            </Button>
          </div>
        </div>
      </header>

      <IndicatorPanel indicators={project.indicators} />

      <Card>
        <SectionTitle hint="Reglas fijas sobre los indicadores, no predicciones.">
          Alertas ({project.alerts.length})
        </SectionTitle>
        <AlertList alerts={project.alerts} />
      </Card>

      <Card>
        <SectionTitle hint="Montos en pesos colombianos. “—” = no calculable.">
          Actividades
        </SectionTitle>
        <div className="mb-4 flex justify-end">
          <Button onClick={() => setEditor({ mode: 'create' })}>Agregar actividad</Button>
        </div>
        {project.activities.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted">
            Este proyecto aún no tiene actividades. Agregue la primera para calcular el valor ganado.
          </p>
        ) : (
          <ActivityTable
            activities={project.activities}
            onEdit={(activity) => setEditor({ mode: 'edit', activity })}
            onDelete={setActivityToDelete}
          />
        )}
      </Card>

      {project.activities.length > 0 && (
        <Card>
          <SectionTitle>Planeado, ganado y gastado por actividad</SectionTitle>
          <Suspense fallback={<Spinner label="Cargando gráfica…" />}>
            <EvmChart activities={project.activities} />
          </Suspense>
        </Card>
      )}

      <Modal
        open={editor.mode !== 'closed'}
        title={editor.mode === 'edit' ? `Editar “${editor.activity.name}”` : 'Nueva actividad'}
        onClose={closeEditor}
      >
        <ActivityForm
          initial={editor.mode === 'edit' ? editor.activity : null}
          pending={saveActivity.isPending}
          error={saveActivity.error}
          onCancel={closeEditor}
          onSubmit={(input) =>
            saveActivity.mutate(
              { id: editor.mode === 'edit' ? editor.activity.id : null, input },
              { onSuccess: closeEditor },
            )
          }
        />
      </Modal>

      <Modal open={editingProject} title="Editar proyecto" onClose={closeProjectForm}>
        <ProjectForm
          initial={project}
          pending={updateProject.isPending}
          error={updateProject.error}
          onCancel={closeProjectForm}
          onSubmit={(input) => updateProject.mutate(input, { onSuccess: closeProjectForm })}
        />
      </Modal>

      <ConfirmDialog
        open={activityToDelete !== null}
        title="Eliminar actividad"
        confirmLabel="Eliminar actividad"
        pending={deleteActivity.isPending}
        onCancel={() => setActivityToDelete(null)}
        onConfirm={() =>
          activityToDelete &&
          deleteActivity.mutate(activityToDelete.id, { onSuccess: () => setActivityToDelete(null) })
        }
      >
        Se eliminará <strong className="text-ink">{activityToDelete?.name}</strong> y los indicadores
        del proyecto se recalcularán sin ella. Esta acción no se puede deshacer.
      </ConfirmDialog>

      <ConfirmDialog
        open={deletingProject}
        title="Eliminar proyecto"
        confirmLabel="Eliminar proyecto"
        pending={deleteProject.isPending}
        onCancel={() => setDeletingProject(false)}
        onConfirm={() => deleteProject.mutate(project.id, { onSuccess: () => void navigate('/') })}
      >
        Se eliminará <strong className="text-ink">{project.name}</strong> con sus{' '}
        {project.activities.length} actividades. Esta acción no se puede deshacer.
      </ConfirmDialog>
    </div>
  )
}
