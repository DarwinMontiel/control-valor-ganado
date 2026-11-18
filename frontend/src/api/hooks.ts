import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from './client'
import type { ActivityInput, ProjectInput } from './types'

const projectsKey = ['projects'] as const
const projectKey = (id: string) => ['projects', id] as const

export const useProjects = (search: string) =>
  useQuery({ queryKey: [...projectsKey, { search }], queryFn: () => api.listProjects(search) })

export const useProject = (id: string) =>
  useQuery({ queryKey: projectKey(id), queryFn: () => api.getProject(id) })

/**
 * Cualquier cambio invalida la lista y el detalle: los indicadores consolidados del proyecto
 * dependen de todas sus actividades y los recalcula el backend.
 */
function useInvalidateProjects() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: projectsKey })
}

export function useCreateProject() {
  const invalidate = useInvalidateProjects()
  return useMutation({ mutationFn: api.createProject, onSuccess: invalidate })
}

export function useUpdateProject(id: string) {
  const invalidate = useInvalidateProjects()
  return useMutation({
    mutationFn: (input: ProjectInput) => api.updateProject(id, input),
    onSuccess: invalidate,
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.deleteProject,
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: projectKey(id) })
      return queryClient.invalidateQueries({ queryKey: projectsKey })
    },
  })
}

export function useSaveActivity(projectId: string) {
  const invalidate = useInvalidateProjects()
  return useMutation({
    mutationFn: ({ id, input }: { id: string | null; input: ActivityInput }) =>
      id ? api.updateActivity(id, input) : api.createActivity(projectId, input),
    onSuccess: invalidate,
  })
}

export function useDeleteActivity() {
  const invalidate = useInvalidateProjects()
  return useMutation({ mutationFn: api.deleteActivity, onSuccess: invalidate })
}
