/**
 * Custom hook for handling async operations with loading, error, and success states.
 * Provides consistent error handling and state management across the application.
 */

import { useState, useCallback } from 'react'
import { ApiError, handleApiError, handleApiSuccess } from '@/lib/api-client'

export interface AsyncOperationState<T> {
  data: T | null
  loading: boolean
  error: ApiError | null
  success: boolean
}

export interface AsyncOperationResult<T> extends AsyncOperationState<T> {
  execute: (operation: () => Promise<{ data?: T; error?: ApiError; success: boolean }>) => Promise<void>
  reset: () => void
  setData: (data: T) => void
}

export function useAsyncOperation<T = any>(
  options: {
    onSuccess?: (data: T) => void
    onError?: (error: ApiError) => void
    showToast?: boolean
    successMessage?: string
  } = {}
): AsyncOperationResult<T> {
  const {
    onSuccess,
    onError,
    showToast = true,
    successMessage
  } = options

  const [state, setState] = useState<AsyncOperationState<T>>({
    data: null,
    loading: false,
    error: null,
    success: false
  })

  const execute = useCallback(async (
    operation: () => Promise<{ data?: T; error?: ApiError; success: boolean }>
  ) => {
    setState(prev => ({
      ...prev,
      loading: true,
      error: null,
      success: false
    }))

    try {
      const result = await operation()

      if (result.success && result.data !== undefined) {
        setState({
          data: result.data,
          loading: false,
          error: null,
          success: true
        })

        if (showToast && successMessage) {
          handleApiSuccess(successMessage)
        }

        onSuccess?.(result.data)
      } else if (result.error) {
        setState({
          data: null,
          loading: false,
          error: result.error,
          success: false
        })

        if (showToast) {
          handleApiError(result.error)
        }

        onError?.(result.error)
      }
    } catch (error) {
      const apiError: ApiError = {
        error: true,
        message: error instanceof Error ? error.message : 'An unexpected error occurred',
        type: 'UnknownError'
      }

      setState({
        data: null,
        loading: false,
        error: apiError,
        success: false
      })

      if (showToast) {
        handleApiError(apiError)
      }

      onError?.(apiError)
    }
  }, [onSuccess, onError, showToast, successMessage])

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      success: false
    })
  }, [])

  const setData = useCallback((data: T) => {
    setState(prev => ({
      ...prev,
      data,
      success: true
    }))
  }, [])

  return {
    ...state,
    execute,
    reset,
    setData
  }
}

// Specialized hook for mutations (create, update, delete)
export function useMutation<TData = any, TVariables = any>(
  options: {
    onSuccess?: (data: TData, variables: TVariables) => void
    onError?: (error: ApiError, variables: TVariables) => void
    showToast?: boolean
    successMessage?: string | ((data: TData, variables: TVariables) => string)
  } = {}
) {
  const {
    onSuccess,
    onError,
    showToast = true,
    successMessage
  } = options

  const [state, setState] = useState<AsyncOperationState<TData>>({
    data: null,
    loading: false,
    error: null,
    success: false
  })

  const mutate = useCallback(async (
    variables: TVariables,
    operation: (variables: TVariables) => Promise<{ data?: TData; error?: ApiError; success: boolean }>
  ) => {
    setState(prev => ({
      ...prev,
      loading: true,
      error: null,
      success: false
    }))

    try {
      const result = await operation(variables)

      if (result.success && result.data !== undefined) {
        setState({
          data: result.data,
          loading: false,
          error: null,
          success: true
        })

        if (showToast && successMessage) {
          const message = typeof successMessage === 'function'
            ? successMessage(result.data, variables)
            : successMessage
          handleApiSuccess(message)
        }

        onSuccess?.(result.data, variables)
      } else if (result.error) {
        setState({
          data: null,
          loading: false,
          error: result.error,
          success: false
        })

        if (showToast) {
          handleApiError(result.error)
        }

        onError?.(result.error, variables)
      }
    } catch (error) {
      const apiError: ApiError = {
        error: true,
        message: error instanceof Error ? error.message : 'An unexpected error occurred',
        type: 'UnknownError'
      }

      setState({
        data: null,
        loading: false,
        error: apiError,
        success: false
      })

      if (showToast) {
        handleApiError(apiError)
      }

      onError?.(apiError, variables)
    }
  }, [onSuccess, onError, showToast, successMessage])

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      success: false
    })
  }, [])

  return {
    ...state,
    mutate,
    reset
  }
}

export default useAsyncOperation