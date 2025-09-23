'use client'

import { useState, useEffect } from 'react'
import { useWebCall } from '@/hooks/useWebCall'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Phone,
  AlertCircle,
  Clock
} from 'lucide-react'

interface CallManagerProps {
  agentId?: string
  driverInfo?: {
    name: string
    loadNumber: string
  }
  onCallEnd?: (callId: string) => void
}

export function CallManager({ agentId, driverInfo, onCallEnd }: CallManagerProps) {
  const { callState, createCall, clearError } = useWebCall()
  const [isCreatingCall, setIsCreatingCall] = useState(false)

  const handleStartCall = async () => {
    if (!agentId) {
      alert('Please select an agent first')
      return
    }

    setIsCreatingCall(true)

    const callConfig = {
      agent_id: agentId,
      metadata: {
        driver_name: driverInfo?.name,
        load_number: driverInfo?.loadNumber
      },
      dynamic_variables: {
        driver_name: driverInfo?.name || 'Driver',
        load_number: driverInfo?.loadNumber || 'N/A'
      }
    }

    try {
      const response = await createCall(callConfig)
      if (response && response.call_id) {
        // Redirect to attend call page
        window.location.href = `/call/${response.call_id}`
      }
    } catch (error) {
      console.error('Error creating call:', error)
    } finally {
      setIsCreatingCall(false)
    }
  }

  const getStatusColor = (isCreating: boolean, hasError: boolean) => {
    if (hasError) return 'bg-red-500'
    if (isCreating) return 'bg-yellow-500'
    return 'bg-gray-400'
  }

  const getStatusIcon = (isCreating: boolean, hasError: boolean) => {
    if (hasError) return <AlertCircle className="h-4 w-4" />
    if (isCreating) return <Clock className="h-4 w-4" />
    return <Phone className="h-4 w-4" />
  }

  const getStatusText = (isCreating: boolean, hasError: boolean) => {
    if (hasError) return 'Error'
    if (isCreating) return 'Creating Call'
    return 'Ready'
  }

  return (
    <div className="space-y-6">
      {/* Call Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="h-5 w-5" />
            Call Control
            <Badge
              className={`ml-auto ${getStatusColor(isCreatingCall || callState.isCreating, !!callState.error)} text-white`}
              variant="secondary"
            >
              <span className="flex items-center gap-1">
                {getStatusIcon(isCreatingCall || callState.isCreating, !!callState.error)}
                {getStatusText(isCreatingCall || callState.isCreating, !!callState.error)}
              </span>
            </Badge>
          </CardTitle>
          <CardDescription>
            {isCreatingCall || callState.isCreating
              ? 'Creating web call...'
              : 'Ready to start web call'
            }
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Error Display */}
          {callState.error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="flex items-center justify-between">
                {callState.error}
                <Button variant="ghost" size="sm" onClick={clearError}>
                  Dismiss
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Single Start Call Button */}
          <div className="flex gap-2">
            <Button
              onClick={handleStartCall}
              disabled={isCreatingCall || callState.isCreating || !agentId}
              className="flex-1"
              size="lg"
            >
              <Phone className="h-4 w-4 mr-2" />
              {isCreatingCall || callState.isCreating ? 'Creating Call...' : 'Start Web Call'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Driver Info Display */}
      {driverInfo && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Call Details</CardTitle>
            <CardDescription>
              Information for this web call
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 text-sm">
              <div>
                <span className="font-medium">Driver Name:</span>
                <p className="text-muted-foreground">{driverInfo.name}</p>
              </div>
              <div>
                <span className="font-medium">Load Number:</span>
                <p className="text-muted-foreground">{driverInfo.loadNumber}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

    </div>
  )
}