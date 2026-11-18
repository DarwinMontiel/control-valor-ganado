import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useCreateProject, useProjects } from '../api/hooks'
import type { Project } from '../api/types'
import { inputClass } from '../components/Field'
import { Modal } from '../components/Modal'
import { ProjectForm } from '../components/ProjectForm'
import { Badge, Button, Card, Notice, Spinner } from '../components/ui'
import { formatDate, formatIndex, formatMoney } from '../lib/format'
import { overallHealth } from '../lib/status'

function ProjectCard({ project }: { project: Project }) {
  const health = overallHealth(project.indicators)
  return (
    <Link
      to={`/projects/${project.id}`}
      className="group block rounded-xl border border-line bg-surface p-5 transition-colors hover:border-brand"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold group-hover:text-brand">{project.name}</h3>
        <Badge tone={health.tone}>{health.title}</Badge>
      </div>
      <p className="mt-1 text-xs text-muted">
        {project.activity_count} {project.activity_count === 1 ? 'actividad' : 'actividades'} · corte{' '}
        {formatDate(project.cutoff_date)}
      </p>
      <dl className="tabular mt-4 grid grid-cols-3 gap-3 text-sm">
        <div>
          <dt className="text-xs text-muted">Presupuesto</dt>
          <dd className="font-semibold">{formatMoney(project.indicators.budget_at_completion)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">CPI</dt>
          <dd className="font-semibold">{formatIndex(project.indicators.cost_performance_index)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">SPI</dt>
          <dd className="font-semibold">{formatIndex(project.indicators.schedule_performance_index)}</dd>
        </div>
      </dl>
    </Link>
  )
}

export function ProjectsPage() {
  const [search, setSearch] = useState('')
  const [creating, setCreating] = useState(false)
  const projects = useProjects(search.trim())
  const createProject = useCreateProject()
  const navigate = useNavigate()

  const closeForm = () => {
    setCreating(false)
    createProject.reset()
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Proyectos</h1>
          <p className="text-sm text-muted">Elija un proyecto para ver su valor ganado.</p>
        </div>
        <Button onClick={() => setCreating(true)}>Nuevo proyecto</Button>
      </div>

      <label className="block max-w-sm">
        <span className="sr-only">Buscar proyecto</span>
        <input
          type="search"
          placeholder="Buscar por nombre…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className={inputClass}
        />
      </label>

      {projects.isPending && <Spinner label="Cargando proyectos…" />}
      {projects.isError && <Notice tone="bad">{projects.error.message}</Notice>}
      {projects.data?.items.length === 0 && (
        <Card className="text-center">
          <p className="font-semibold">{search ? 'Ningún proyecto coincide.' : 'Aún no hay proyectos.'}</p>
          <p className="mt-1 text-sm text-muted">Cree uno y registre sus actividades para ver el análisis.</p>
        </Card>
      )}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {projects.data?.items.map((project) => <ProjectCard key={project.id} project={project} />)}
      </div>

      <Modal open={creating} title="Nuevo proyecto" onClose={closeForm}>
        <ProjectForm
          initial={null}
          pending={createProject.isPending}
          error={createProject.error}
          onCancel={closeForm}
          onSubmit={(input) =>
            createProject.mutate(input, {
              onSuccess: (project) => {
                closeForm()
                void navigate(`/projects/${project.id}`)
              },
            })
          }
        />
      </Modal>
    </div>
  )
}
