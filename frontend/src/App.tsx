import { Link, Route, Routes } from 'react-router-dom'

import { ProjectPage } from './pages/ProjectPage'
import { ProjectsPage } from './pages/ProjectsPage'

export function App() {
  return (
    <div className="min-h-dvh">
      <header className="graph-paper border-b border-line">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Link to="/" className="flex items-center gap-3">
            <img src="/favicon.svg" alt="" className="size-8" />
            <span>
              <span className="block font-semibold leading-tight">Valor Ganado</span>
              <span className="block text-xs text-muted">Control de costo y cronograma</span>
            </span>
          </Link>
          <a href="/api-docs" className="text-sm font-semibold text-brand hover:underline">
            API
          </a>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <Routes>
          <Route path="/" element={<ProjectsPage />} />
          <Route path="/projects/:projectId" element={<ProjectPage />} />
          <Route path="*" element={<p>Página no encontrada.</p>} />
        </Routes>
      </main>
    </div>
  )
}
