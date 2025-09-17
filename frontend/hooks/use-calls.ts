import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useSocketEvent } from './use-socket'
import type { Call, CallDetail, CallList, CallStatusUpdate } from '@/types'
import toast from 'react-hot-toast'

export function useCalls(filters?: {
  page?: number
  per_page?: number
  status_filter?: string
  driver_name?: string
  load_number?: string
}) {
  return useQuery<CallList>({
    queryKey: ['calls', filters],
    queryFn: () => api.getCalls(filters),
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function useActiveCalls() {
  const queryClient = useQueryClient()
  
  const query = useQuery<Call[]>({
    queryKey: ['calls', 'active'],
    queryFn: () => api.getActiveCalls(),
    refetchInterval: 10000, // Refetch every 10 seconds for active calls
  })

  // Listen for real-time updates
  useSocketEvent<CallStatusUpdate>('call_status_update', (data) => {
    // Update the active calls cache
    queryClient.setQueryData(['calls', 'active'], (oldData: Call[] | undefined) => {
      if (!oldData) return oldData
      
      return oldData.map(call => 
        call.id === data.call_id 
          ? { ...call, status: data.status, duration: data.duration }
          : call
      )
    })
    
    // Also invalidate the main calls list
    queryClient.invalidateQueries({ queryKey: ['calls'] })
  })

  return query
}

export function useCallDetail(callId: number) {
  return useQuery({
    queryKey: ['calls', callId],
    queryFn: () => api.getCallDetails(callId),
    enabled: !!callId,
  })
}

export function useCallTranscript(callId: number) {
  return useQuery({
    queryKey: ['calls', callId, 'transcript'],
    queryFn: () => api.getCallTranscript(callId),
    enabled: !!callId,
  })
}

export function useInitiateCall() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: {
      driver_name: string
      phone_number?: string
      load_number: string
      agent_config_id: number
      call_type?: 'phone_call' | 'web_call'
    }) => api.initializeCall(data),
    onSuccess: (data) => {
      toast.success(`Call initiated successfully for ${data.driver_name}`)
      
      // Invalidate and refetch calls
      queryClient.invalidateQueries({ queryKey: ['calls'] })
      queryClient.invalidateQueries({ queryKey: ['calls', 'active'] })
    },
    onError: (error: Error) => {
      toast.error(`Failed to initiate call: ${error.message}`)
    },
  })
}

export function useCancelCall() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (callId: number) => api.cancelCall(callId),
    onSuccess: (data) => {
      toast.success(`Call cancelled successfully`)
      
      // Update the specific call in cache
      queryClient.setQueryData(['calls', data.id], data)
      
      // Invalidate calls lists
      queryClient.invalidateQueries({ queryKey: ['calls'] })
      queryClient.invalidateQueries({ queryKey: ['calls', 'active'] })
    },
    onError: (error: Error) => {
      toast.error(`Failed to cancel call: ${error.message}`)
    },
  })
}

export function useRetryCall() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (callId: number) => api.retryCall(callId),
    onSuccess: (data) => {
      toast.success(`Call retry initiated successfully`)
      
      // Update the specific call in cache
      queryClient.setQueryData(['calls', data.id], data)
      
      // Invalidate calls lists
      queryClient.invalidateQueries({ queryKey: ['calls'] })
      queryClient.invalidateQueries({ queryKey: ['calls', 'active'] })
    },
    onError: (error: Error) => {
      toast.error(`Failed to retry call: ${error.message}`)
    },
  })
}

export function useCallHistory(filters?: {
  page?: number
  per_page?: number
  status_filter?: string
  driver_name?: string
  load_number?: string
  date_from?: string
  date_to?: string
}) {
  return useQuery<CallList>({
    queryKey: ['calls', 'history', filters],
    queryFn: () => api.getCalls(filters),
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes
  })
}

export function useCallAnalytics(days: number = 7) {
  return useQuery({
    queryKey: ['analytics', 'calls', days],
    queryFn: () => api.getAnalytics(days),
    staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
  })
}
