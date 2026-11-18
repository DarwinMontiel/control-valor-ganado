import type {
  Activity,
  ActivityInput,
  ApiErrorBody,
  ProjectDetail,
  ProjectInput,
  ProjectPage,
} from './types'

const API_BASE = `${import.meta.env.VITE_API_URL ?? ''}/api/v1`
const NO_CONTENT = 204
const UNREACHABLE_MESSAGE = 'No se pudo conectar con la API. Verifique que el backend esté en marcha.'

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fieldErrors: Record<string, string>

  constructor(status: number, body: ApiErrorBody | null) {
    super(body?.error.message ?? `Error inesperado (${status}).`)
    this.status = status
    this.code = body?.error.code ?? 'UNKNOWN'
    this.fieldErrors = Object.fromEntries(
      (body?.error.details ?? []).map((detail) => [detail.field, detail.message]),
    )
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new Error(UNREACHABLE_MESSAGE)
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null
    throw new ApiError(response.status, body)
  }
  if (response.status === NO_CONTENT) {
    return undefined as T
  }
  return (await response.json()) as T
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  body: JSON.stringify(body),
})

export const api = {
  listProjects: (search: string) =>
    request<ProjectPage>(`/projects?limit=100${search ? `&search=${encodeURIComponent(search)}` : ''}`),
  getProject: (id: string) => request<ProjectDetail>(`/projects/${id}`),
  createProject: (input: ProjectInput) => request<ProjectDetail>('/projects', json('POST', input)),
  updateProject: (id: string, input: ProjectInput) =>
    request<ProjectDetail>(`/projects/${id}`, json('PUT', input)),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE' }),
  createActivity: (projectId: string, input: ActivityInput) =>
    request<Activity>(`/projects/${projectId}/activities`, json('POST', input)),
  updateActivity: (id: string, input: ActivityInput) =>
    request<Activity>(`/activities/${id}`, json('PUT', input)),
  deleteActivity: (id: string) => request<void>(`/activities/${id}`, { method: 'DELETE' }),
}
