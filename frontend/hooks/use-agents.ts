import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AgentConfiguration, AgentConfigList } from '@/types'
import toast from 'react-hot-toast'

export function useAgentConfigs(filters?: {
  page?: number
  per_page?: number
  scenario_type?: string
  is_active?: boolean
}) {
  return useQuery({
    queryKey: ['agents', filters],
    queryFn: () => api.getAgentConfigs(filters),
  })
}

export function useAgentConfig(id: number) {
  return useQuery({
    queryKey: ['agents', id],
    queryFn: () => api.getAgentConfig(id),
    enabled: !!id,
  })
}

export function useCreateAgentConfig() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: any) => api.createAgentConfig(data),
    onSuccess: (data) => {
      toast.success(`Agent configuration "${data.name}" created successfully`)
      
      // Invalidate and refetch agents list
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
    onError: (error: Error) => {
      toast.error(`Failed to create agent configuration: ${error.message}`)
    },
  })
}

export function useUpdateAgentConfig() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => 
      api.updateAgentConfig(id, data),
    onSuccess: (data) => {
      toast.success(`Agent configuration "${data.name}" updated successfully`)
      
      // Update the specific agent in cache
      queryClient.setQueryData(['agents', data.id], data)
      
      // Invalidate agents list to reflect changes
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
    onError: (error: Error) => {
      toast.error(`Failed to update agent configuration: ${error.message}`)
    },
  })
}

export function useDeleteAgentConfig() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => api.deleteAgentConfig(id),
    onSuccess: () => {
      toast.success('Agent configuration deleted successfully')
      
      // Invalidate agents list
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete agent configuration: ${error.message}`)
    },
  })
}

export function useDeployAgentConfig() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => api.deployAgentConfig(id),
    onSuccess: (data) => {
      toast.success(`Agent configuration "${data.name}" deployed successfully`)
      
      // Update the specific agent in cache
      queryClient.setQueryData(['agents', data.id], data)
      
      // Invalidate agents list
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
    onError: (error: Error) => {
      toast.error(`Failed to deploy agent configuration: ${error.message}`)
    },
  })
}

export function useTestAgentConfig() {
  return useMutation({
    mutationFn: ({ id, testPhone }: { id: number; testPhone: string }) => 
      api.testAgentConfig(id, testPhone),
    onSuccess: (data) => {
      toast.success('Test call initiated successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to initiate test call: ${error.message}`)
    },
  })
}
