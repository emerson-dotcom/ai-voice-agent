'use client'

import { useState, useCallback } from 'react'
import { apiRequest, API_ENDPOINTS } from '@/lib/api'

interface WebCallConfig {
  agent_id: string
  metadata?: Record<string, any>
  dynamic_variables?: Record<string, any>
}

interface WebCallResponse {
  call_id: string
  retell_call_id: string
  access_token: string
  agent_id: string
  call_status: string
}

interface CallState {
  isCreating: boolean
  error: string | null
}

interface UseWebCallReturn {
  callState: CallState
  createCall: (config: WebCallConfig) => Promise<WebCallResponse | null>
  clearError: () => void
}

export function useWebCall(): UseWebCallReturn {
  const [callState, setCallState] = useState<CallState>({
    isCreating: false,
    error: null
  })

  const createCall = useCallback(async (config: WebCallConfig): Promise<WebCallResponse | null> => {
    try {
      setCallState(prev => ({
        ...prev,
        isCreating: true,
        error: null
      }))

      const response = await apiRequest<WebCallResponse>(API_ENDPOINTS.RETELL_CALL_WEB, {
        method: 'POST',
        body: JSON.stringify(config)
      })

      setCallState(prev => ({
        ...prev,
        isCreating: false
      }))

      return response

    } catch (error) {
      setCallState(prev => ({
        ...prev,
        isCreating: false,
        error: error instanceof Error ? error.message : 'Failed to create call'
      }))
      return null
    }
  }, [])

  const clearError = useCallback(() => {
    setCallState(prev => ({
      ...prev,
      error: null
    }))
  }, [])

  return {
    callState,
    createCall,
    clearError
  }
}