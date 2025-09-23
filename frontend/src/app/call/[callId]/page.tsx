'use client'

import { useEffect, useState, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Phone,
  PhoneOff,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  AlertCircle,
  CheckCircle,
  Clock,
  User,
  Bot
} from 'lucide-react'
import { RetellWebClient } from 'retell-client-js-sdk'
import { callApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface CallDetails {
  id: string
  retell_call_id: string
  retell_access_token: string
  agent_id: string
  call_status: string
  driver_name?: string
  load_number?: string
  metadata?: any
}

interface TranscriptEntry {
  role: 'agent' | 'user'
  content: string
  timestamp: number
}

export default function AttendCallPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const callId = params.callId as string

  const [callDetails, setCallDetails] = useState<CallDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Call states
  const [isCallActive, setIsCallActive] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [callStatus, setCallStatus] = useState<string>('idle')
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [isMuted, setIsMuted] = useState(false)
  const [volume, setVolume] = useState(100)
  const [micPermission, setMicPermission] = useState<'granted' | 'denied' | 'prompt' | 'checking'>('checking')

  const retellClientRef = useRef<RetellWebClient | null>(null)

  // Check microphone permissions
  useEffect(() => {
    const checkMicPermission = async () => {
      try {
        const permissionStatus = await navigator.permissions.query({ name: 'microphone' as PermissionName })
        setMicPermission(permissionStatus.state as 'granted' | 'denied' | 'prompt')

        // Listen for permission changes
        permissionStatus.onchange = () => {
          setMicPermission(permissionStatus.state as 'granted' | 'denied' | 'prompt')
        }
      } catch (error) {
        console.warn('Could not check microphone permissions:', error)
        setMicPermission('prompt')
      }
    }

    checkMicPermission()
  }, [])

  // Fetch call details
  useEffect(() => {
    const fetchCallDetails = async () => {
      try {
        const details = await callApi.get(callId)
        setCallDetails(details)

        if (!details.retell_access_token) {
          throw new Error('No access token available for this call')
        }
      } catch (err: any) {
        console.error('Error fetching call details:', err)
        setError(err.message || 'Failed to load call details')
        toast({
          title: 'Error',
          description: 'Failed to load call details',
          variant: 'destructive'
        })
      } finally {
        setLoading(false)
      }
    }

    if (callId) {
      fetchCallDetails()
    }
  }, [callId, toast])

  // Initialize Retell client
  useEffect(() => {
    if (!callDetails?.retell_access_token) return

    const initializeClient = () => {
      try {
        const client = new RetellWebClient()
        retellClientRef.current = client

        // Set up event listeners
        client.on('call_started', () => {
          console.log('Call started')
          setIsCallActive(true)
          setIsConnecting(false)
          setCallStatus('connected')
          toast({
            title: 'Call Started',
            description: 'Connected successfully',
            variant: 'success'
          })
        })

        client.on('call_ended', () => {
          console.log('Call ended')
          setIsCallActive(false)
          setIsConnecting(false)
          setCallStatus('ended')
          toast({
            title: 'Call Ended',
            description: 'The call has been terminated',
            variant: 'default'
          })

          // Redirect to results page after a short delay
          setTimeout(() => {
            router.push(`/results?call_id=${callId}`)
          }, 2000)
        })

        client.on('agent_start_talking', () => {
          console.log('Agent started talking')
        })

        client.on('agent_stop_talking', () => {
          console.log('Agent stopped talking')
        })

        client.on('update', (update) => {
          console.log('Call update:', update)

          // Handle transcript updates
          if (update.transcript) {
            const lastTranscript = update.transcript[update.transcript.length - 1]
            if (lastTranscript) {
              setTranscript(prev => {
                const newEntry: TranscriptEntry = {
                  role: lastTranscript.role,
                  content: lastTranscript.content,
                  timestamp: Date.now()
                }

                // Avoid duplicates by checking if the last entry is the same
                const lastEntry = prev[prev.length - 1]
                if (lastEntry && lastEntry.content === newEntry.content && lastEntry.role === newEntry.role) {
                  return prev
                }

                return [...prev, newEntry].slice(-20) // Keep last 20 entries
              })
            }
          }
        })

        client.on('error', (error) => {
          console.error('Retell client error:', error)
          setError(error.message || 'Call error occurred')
          setIsCallActive(false)
          setIsConnecting(false)
          setCallStatus('error')
          toast({
            title: 'Call Error',
            description: error.message || 'An error occurred during the call',
            variant: 'destructive'
          })
        })

      } catch (err: any) {
        console.error('Error initializing Retell client:', err)
        setError('Failed to initialize call client')
      }
    }

    initializeClient()

    return () => {
      if (retellClientRef.current) {
        retellClientRef.current.stopCall()
      }
    }
  }, [callDetails, callId, router, toast])

  const requestMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop()) // Stop the stream, we just needed permission
      setMicPermission('granted')
      return true
    } catch (error) {
      console.error('Microphone permission denied:', error)
      setMicPermission('denied')
      toast({
        title: 'Microphone Permission Required',
        description: 'Please allow microphone access to use voice calls. Check your browser settings and try again.',
        variant: 'destructive'
      })
      return false
    }
  }

  const startCall = async () => {
    if (!retellClientRef.current || !callDetails?.retell_access_token) return

    // Check and request microphone permission if needed
    if (micPermission !== 'granted') {
      const permissionGranted = await requestMicrophonePermission()
      if (!permissionGranted) {
        return
      }
    }

    try {
      setIsConnecting(true)
      setCallStatus('connecting')
      setError(null)

      await retellClientRef.current.startCall({
        accessToken: callDetails.retell_access_token,
        sampleRate: 24000,
        captureDeviceId: 'default',
        playbackDeviceId: 'default'
      })

    } catch (err: any) {
      console.error('Error starting call:', err)
      let errorMessage = err.message || 'Failed to start call'

      // Check for specific microphone-related errors
      if (err.message?.includes('microphone') || err.message?.includes('audio') || err.message?.includes('permission')) {
        errorMessage = 'Microphone access denied. Please allow microphone permission and try again.'
        setMicPermission('denied')
      }

      setError(errorMessage)
      setIsConnecting(false)
      setCallStatus('error')
      toast({
        title: 'Connection Failed',
        description: errorMessage,
        variant: 'destructive'
      })
    }
  }

  const endCall = async () => {
    if (!retellClientRef.current) return

    try {
      retellClientRef.current.stopCall()
    } catch (err: any) {
      console.error('Error ending call:', err)
    }
  }

  const toggleMute = () => {
    setIsMuted(!isMuted)
    // Note: Retell SDK doesn't expose mute functionality directly
    // This would need to be implemented via audio context manipulation
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-green-500'
      case 'connecting': return 'bg-yellow-500'
      case 'error': return 'bg-red-500'
      case 'ended': return 'bg-gray-500'
      default: return 'bg-gray-400'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="h-4 w-4" />
      case 'connecting': return <Clock className="h-4 w-4" />
      case 'error': return <AlertCircle className="h-4 w-4" />
      default: return <Phone className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <Card className="w-96">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <span className="ml-3">Loading call details...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error && !callDetails) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <Card className="w-96">
          <CardContent className="pt-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <Button
              variant="outline"
              onClick={() => router.push('/calls')}
              className="mt-4 w-full"
            >
              Back to Calls
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">Web Call</h1>
          <p className="text-xl text-slate-600">
            {callDetails?.driver_name && callDetails?.load_number
              ? `Call with ${callDetails.driver_name} about load ${callDetails.load_number}`
              : 'Voice agent call session'
            }
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Call Controls */}
          <div className="space-y-6">
            {/* Call Status Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Phone className="h-5 w-5" />
                  Call Status
                  <Badge
                    className={`ml-auto ${getStatusColor(callStatus)} text-white`}
                    variant="secondary"
                  >
                    <span className="flex items-center gap-1">
                      {getStatusIcon(callStatus)}
                      {callStatus.charAt(0).toUpperCase() + callStatus.slice(1)}
                    </span>
                  </Badge>
                </CardTitle>
                <CardDescription>
                  {isCallActive
                    ? 'Call is active and connected'
                    : isConnecting
                    ? 'Connecting to call...'
                    : 'Ready to start call'
                  }
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Microphone Permission Status */}
                {micPermission === 'denied' && (
                  <Alert variant="destructive">
                    <MicOff className="h-4 w-4" />
                    <AlertDescription>
                      Microphone access is required for voice calls. Please allow microphone permission in your browser settings and refresh the page.
                    </AlertDescription>
                  </Alert>
                )}

                {micPermission === 'prompt' && (
                  <Alert>
                    <Mic className="h-4 w-4" />
                    <AlertDescription className="flex items-center justify-between">
                      <span>Click "Test Microphone" to allow microphone access when prompted by your browser.</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={requestMicrophonePermission}
                        className="ml-2"
                      >
                        <Mic className="h-3 w-3 mr-1" />
                        Test Microphone
                      </Button>
                    </AlertDescription>
                  </Alert>
                )}

                {micPermission === 'granted' && (
                  <Alert className="border-green-200 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800">
                      Microphone access granted. Ready to start voice call.
                    </AlertDescription>
                  </Alert>
                )}

                {/* Error Display */}
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {/* Call Controls */}
                <div className="flex gap-2">
                  {!isCallActive && !isConnecting ? (
                    <Button
                      onClick={startCall}
                      className="flex-1"
                      size="lg"
                    >
                      <Phone className="h-4 w-4 mr-2" />
                      Start Call
                    </Button>
                  ) : (
                    <Button
                      variant="destructive"
                      onClick={endCall}
                      className="flex-1"
                      size="lg"
                      disabled={isConnecting}
                    >
                      <PhoneOff className="h-4 w-4 mr-2" />
                      {isConnecting ? 'Connecting...' : 'End Call'}
                    </Button>
                  )}

                  <Button
                    variant="outline"
                    onClick={toggleMute}
                    disabled={!isCallActive}
                    size="lg"
                  >
                    {isMuted ? (
                      <MicOff className="h-4 w-4" />
                    ) : (
                      <Mic className="h-4 w-4" />
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    disabled={!isCallActive}
                    size="lg"
                  >
                    <Volume2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Call Info */}
            {callDetails && (
              <Card>
                <CardHeader>
                  <CardTitle>Call Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Call ID:</span>
                      <p className="text-muted-foreground font-mono">{callDetails.id}</p>
                    </div>
                    {callDetails.driver_name && (
                      <div>
                        <span className="font-medium">Driver Name:</span>
                        <p className="text-muted-foreground">{callDetails.driver_name}</p>
                      </div>
                    )}
                    {callDetails.load_number && (
                      <div>
                        <span className="font-medium">Load Number:</span>
                        <p className="text-muted-foreground">{callDetails.load_number}</p>
                      </div>
                    )}
                    <div>
                      <span className="font-medium">Agent ID:</span>
                      <p className="text-muted-foreground font-mono">{callDetails.agent_id}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Live Transcript */}
          <Card>
            <CardHeader>
              <CardTitle>Live Transcript</CardTitle>
              <CardDescription>
                Real-time conversation transcript
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96 w-full border rounded p-4">
                {transcript.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    {isCallActive ? 'Waiting for conversation...' : 'Start the call to see transcript'}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {transcript.map((entry, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <div className={`p-2 rounded-full ${
                          entry.role === 'agent'
                            ? 'bg-blue-100 text-blue-600'
                            : 'bg-green-100 text-green-600'
                        }`}>
                          {entry.role === 'agent' ? (
                            <Bot className="h-4 w-4" />
                          ) : (
                            <User className="h-4 w-4" />
                          )}
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm">
                              {entry.role === 'agent' ? 'AI Agent' : 'User'}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(entry.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <p className="text-sm">{entry.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}