'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { RetellWebClient, RetellCallConfig, RetellCallResponse } from '@/lib/retell-web-client'

interface CallState {
  isConnected: boolean
  isCallActive: boolean
  callId: string | null
  status: 'idle' | 'connecting' | 'connected' | 'ended' | 'error'
  error: string | null
  audioLevel: number
  transcript: TranscriptEntry[]
  audioDevices: { microphone: boolean; speakers: boolean } | null
}

interface TranscriptEntry {
  text: string
  speaker: 'agent' | 'user'
  timestamp: number
}

interface UseRetellCallReturn {
  callState: CallState
  startCall: (config: RetellCallConfig) => Promise<RetellCallResponse | null>
  endCall: () => Promise<void>
  checkAudioDevices: () => Promise<void>
  clearError: () => void
}

export function useRetellCall(): UseRetellCallReturn {
  const clientRef = useRef<RetellWebClient | null>(null)
  const [callState, setCallState] = useState<CallState>({
    isConnected: false,
    isCallActive: false,
    callId: null,
    status: 'idle',
    error: null,
    audioLevel: 0,
    transcript: [],
    audioDevices: null
  })

  // Initialize Retell client
  useEffect(() => {
    if (!clientRef.current) {
      clientRef.current = new RetellWebClient()

      // Set up event listeners
      const client = clientRef.current

      client.on('call_started', (data: RetellCallResponse) => {
        setCallState(prev => ({
          ...prev,
          isConnected: true,
          isCallActive: true,
          callId: data.call_id,
          status: 'connected',
          error: null
        }))
      })

      client.on('call_ended', (data: any) => {
        setCallState(prev => ({
          ...prev,
          isConnected: false,
          isCallActive: false,
          status: 'ended'
        }))
      })

      client.on('error', (data: any) => {
        setCallState(prev => ({
          ...prev,
          status: 'error',
          error: data.message || 'An error occurred',
          isConnected: false,
          isCallActive: false
        }))
      })

      client.on('audio_level', (data: any) => {
        setCallState(prev => ({
          ...prev,
          audioLevel: data.level || 0
        }))
      })

      client.on('transcript', (data: any) => {
        setCallState(prev => ({
          ...prev,
          transcript: [...prev.transcript, {
            text: data.text,
            speaker: data.speaker,
            timestamp: data.timestamp
          }].slice(-50) // Keep last 50 transcript entries
        }))
      })
    }

    return () => {
      if (clientRef.current) {
        // Cleanup will be handled by the client
      }
    }
  }, [])

  const startCall = useCallback(async (config: RetellCallConfig): Promise<RetellCallResponse | null> => {
    if (!clientRef.current) return null

    try {
      setCallState(prev => ({
        ...prev,
        status: 'connecting',
        error: null,
        transcript: []
      }))

      const response = await clientRef.current.startCall(config)
      return response

    } catch (error) {
      setCallState(prev => ({
        ...prev,
        status: 'error',
        error: error instanceof Error ? error.message : 'Failed to start call'
      }))
      return null
    }
  }, [])

  const endCall = useCallback(async (): Promise<void> => {
    if (!clientRef.current || !callState.isCallActive) return

    try {
      await clientRef.current.endCall()

    } catch (error) {
      setCallState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to end call'
      }))
    }
  }, [callState.isCallActive])

  const checkAudioDevices = useCallback(async (): Promise<void> => {
    if (!clientRef.current) return

    try {
      const devices = await clientRef.current.checkAudioDevices()
      setCallState(prev => ({
        ...prev,
        audioDevices: devices
      }))
    } catch (error) {
      setCallState(prev => ({
        ...prev,
        audioDevices: { microphone: false, speakers: false }
      }))
    }
  }, [])

  const clearError = useCallback(() => {
    setCallState(prev => ({
      ...prev,
      error: null,
      status: prev.status === 'error' ? 'idle' : prev.status
    }))
  }, [])

  // Check audio devices on mount
  useEffect(() => {
    checkAudioDevices()
  }, [checkAudioDevices])

  return {
    callState,
    startCall,
    endCall,
    checkAudioDevices,
    clearError
  }
}