'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useCallDetail, useCallTranscript, useCancelCall } from '@/hooks/use-calls'
import type { CallDetail, Transcript } from '@/types'
import { format } from 'date-fns'
import { 
  ArrowLeft,
  Phone,
  PhoneOff,
  Clock,
  User,
  Truck,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Download,
  FileText,
  BarChart3,
  ExternalLink,
  Globe
} from 'lucide-react'

export default function CallDetailPage() {
  const params = useParams()
  const id = params?.id as string
  
  const { data: call, isLoading } = useCallDetail(parseInt(id)) as { data: CallDetail | undefined, isLoading: boolean }
  const { data: transcript } = useCallTranscript(parseInt(id)) as { data: Transcript | undefined }
  const cancelCall = useCancelCall()
  
  const [showTranscript, setShowTranscript] = useState(true)
  const [showStructuredData, setShowStructuredData] = useState(true)

  const handleCancelCall = async () => {
    if (call?.status === 'in_progress' && confirm('Are you sure you want to cancel this call?')) {
      await cancelCall.mutateAsync(parseInt(id))
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'initiated':
        return <Badge className="bg-blue-100 text-blue-800"><Clock className="h-3 w-3 mr-1" />Initiated</Badge>
      case 'in_progress':
        return <Badge className="bg-yellow-100 text-yellow-800"><Phone className="h-3 w-3 mr-1" />In Progress</Badge>
      case 'completed':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Completed</Badge>
      case 'failed':
        return <Badge className="bg-red-100 text-red-800"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>
      case 'cancelled':
        return <Badge className="bg-gray-100 text-gray-800"><PhoneOff className="h-3 w-3 mr-1" />Cancelled</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getOutcomeBadge = (outcome: string) => {
    switch (outcome) {
      case 'In-Transit Update':
        return <Badge className="bg-blue-100 text-blue-800">In-Transit Update</Badge>
      case 'Arrival Confirmation':
        return <Badge className="bg-green-100 text-green-800">Arrival Confirmation</Badge>
      case 'Emergency Escalation':
        return <Badge className="bg-red-100 text-red-800">Emergency Escalation</Badge>
      default:
        return <Badge variant="outline">{outcome}</Badge>
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getDataQualityScore = (data: Record<string, unknown> | null | undefined) => {
    if (!data) return 0
    const fields = Object.values(data).filter(value => 
      value !== null && value !== undefined && value !== ''
    )
    const totalFields = Object.keys(data).length
    return totalFields > 0 ? Math.round((fields.length / totalFields) * 100) : 0
  }

  const exportCallData = () => {
    if (!call) return
    
    const exportData = {
      call_details: {
        id: call.id,
        driver_name: call.driver_name,
        phone_number: call.phone_number,
        load_number: call.load_number,
        status: call.status,
        call_outcome: call.call_outcome,
        duration: call.duration,
        created_at: call.created_at,
        completed_at: call.end_time
      },
      structured_data: call.structured_data,
      transcript: transcript
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `call-${call.id}-${call.driver_name.replace(/\s+/g, '-')}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (!call) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Call Not Found</h3>
          <p className="text-gray-600 mb-4">The requested call could not be found.</p>
          <Button asChild>
            <Link href="/dashboard/calls">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Calls
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/dashboard/calls">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Calls
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Call Details</h1>
            <p className="text-gray-600">Call with {call.driver_name}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusBadge(call.status)}
          <Button variant="outline" size="sm" onClick={exportCallData}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          {call.status === 'in_progress' && (
            <Button variant="outline" size="sm" onClick={handleCancelCall}>
              <PhoneOff className="h-4 w-4 mr-2" />
              Cancel Call
            </Button>
          )}
        </div>
      </div>

      {/* Call Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Phone className="h-5 w-5 mr-2" />
              Call Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <User className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-600">Driver</p>
                    <p className="font-medium">{call.driver_name}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <Phone className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-600">Phone Number</p>
                    <p className="font-medium">{call.phone_number}</p>
                  </div>
                </div>
                
                {call.web_call_url && (
                  <div className="flex items-center space-x-3">
                    <Globe className="h-5 w-5 text-blue-400" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-600">Web Call</p>
                      <div className="flex items-center space-x-2">
                        <p className="font-medium text-blue-600 truncate">{call.web_call_url}</p>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => window.open(call.web_call_url, '_blank')}
                          className="shrink-0"
                        >
                          <ExternalLink className="h-3 w-3 mr-1" />
                          Open Call
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="flex items-center space-x-3">
                  <Truck className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-600">Load Number</p>
                    <p className="font-medium">#{call.load_number}</p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600">Call Started</p>
                  <p className="font-medium">{format(new Date(call.created_at), 'MMM d, yyyy HH:mm:ss')}</p>
                </div>
                
                {call.end_time && (
                  <div>
                    <p className="text-sm text-gray-600">Call Ended</p>
                    <p className="font-medium">{format(new Date(call.end_time), 'MMM d, yyyy HH:mm:ss')}</p>
                  </div>
                )}
                
                {call.duration && (
                  <div>
                    <p className="text-sm text-gray-600">Duration</p>
                    <p className="font-medium">{formatDuration(call.duration)}</p>
                  </div>
                )}
                
                {call.agent_config_name && (
                  <div>
                    <p className="text-sm text-gray-600">Agent Configuration</p>
                    <p className="font-medium">{call.agent_config_name}</p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Call Outcome</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {call.call_outcome ? (
              <>
                {getOutcomeBadge(call.call_outcome)}
                <div className="text-sm text-gray-600">
                  {call.call_outcome === 'Emergency Escalation' && (
                    <div className="flex items-center space-x-2 text-red-600">
                      <AlertTriangle className="h-4 w-4" />
                      <span>Emergency protocol activated</span>
                    </div>
                  )}
                  {call.call_outcome === 'In-Transit Update' && (
                    <div className="flex items-center space-x-2 text-blue-600">
                      <Truck className="h-4 w-4" />
                      <span>Driver status updated</span>
                    </div>
                  )}
                  {call.call_outcome === 'Arrival Confirmation' && (
                    <div className="flex items-center space-x-2 text-green-600">
                      <CheckCircle className="h-4 w-4" />
                      <span>Arrival confirmed</span>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <p className="text-sm text-gray-500">
                {call.status === 'in_progress' ? 'Call in progress...' : 'No outcome recorded'}
              </p>
            )}
            
            {call.structured_data && (
              <div className="pt-4 border-t">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Data Quality</span>
                  <span className="text-sm text-gray-600">
                    {getDataQualityScore(call.structured_data)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      getDataQualityScore(call.structured_data) >= 90 
                        ? 'bg-green-500' 
                        : getDataQualityScore(call.structured_data) >= 70 
                        ? 'bg-yellow-500' 
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${getDataQualityScore(call.structured_data)}%` }}
                  ></div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Structured Data */}
      {call.structured_data && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <CardTitle>Extracted Data</CardTitle>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowStructuredData(!showStructuredData)}
              >
                {showStructuredData ? 'Hide' : 'Show'}
              </Button>
            </div>
            <CardDescription>
              Structured information extracted from the conversation
            </CardDescription>
          </CardHeader>
          {showStructuredData && (
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(call.structured_data).map(([key, value]) => (
                  <div key={key} className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-700 capitalize mb-1">
                      {key.replace(/_/g, ' ')}
                    </h4>
                    <p className="text-sm text-gray-900">
                      {typeof value === 'boolean' 
                        ? (value ? 'Yes' : 'No')
                        : value || 'N/A'}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Transcript */}
      {(transcript || call.raw_transcript) && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <CardTitle>Call Transcript</CardTitle>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowTranscript(!showTranscript)}
              >
                {showTranscript ? 'Hide' : 'Show'}
              </Button>
            </div>
            <CardDescription>
              Complete conversation transcript
            </CardDescription>
          </CardHeader>
          {showTranscript && (
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {transcript && transcript.turns && transcript.turns.length > 0 ? (
                  // Structured transcript with turns
                  transcript.turns.map((turn: { speaker: string; message: string; timestamp?: string; confidence_score?: number; emergency_trigger_detected?: boolean }, index: number) => (
                    <div key={index} className={`flex ${turn.speaker === 'agent' ? 'justify-start' : 'justify-end'}`}>
                      <div className={`max-w-3xl p-3 rounded-lg ${
                        turn.speaker === 'agent' 
                          ? 'bg-blue-50 border-l-4 border-blue-500' 
                          : 'bg-gray-50 border-l-4 border-gray-500'
                      }`}>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-xs font-medium text-gray-600 capitalize">
                            {turn.speaker === 'agent' ? 'AI Agent' : 'Driver'}
                          </span>
                          {turn.timestamp && (
                            <span className="text-xs text-gray-500">
                              {format(new Date(turn.timestamp), 'HH:mm:ss')}
                            </span>
                          )}
                          {turn.confidence_score && (
                            <span className="text-xs text-gray-500">
                              ({Math.round(turn.confidence_score * 100)}% confidence)
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-900">{turn.message}</p>
                        {turn.emergency_trigger_detected && (
                          <div className="mt-2 flex items-center space-x-1 text-red-600">
                            <AlertTriangle className="h-3 w-3" />
                            <span className="text-xs">Emergency trigger detected</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                ) : call.raw_transcript ? (
                  // Raw transcript as formatted text
                  <div className="bg-gray-50 rounded-lg p-4">
                    <pre className="text-sm text-gray-900 whitespace-pre-wrap font-mono leading-relaxed">
                      {call.raw_transcript}
                    </pre>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 text-center py-8">
                    {call.status === 'in_progress' ? 'Transcript will appear as the call progresses...' : 'No transcript available'}
                  </p>
                )}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Call Metrics */}
      {call.status === 'completed' && (
        <Card>
          <CardHeader>
            <CardTitle>Call Metrics</CardTitle>
            <CardDescription>
              Performance and quality metrics for this call
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{formatDuration(call.duration || 0)}</div>
                <div className="text-sm text-gray-600">Call Duration</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {transcript?.turns ? transcript.turns.length : 0}
                </div>
                <div className="text-sm text-gray-600">Conversation Turns</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {call.structured_data ? getDataQualityScore(call.structured_data) : 0}%
                </div>
                <div className="text-sm text-gray-600">Data Quality</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {call.call_outcome ? '✓' : '✗'}
                </div>
                <div className="text-sm text-gray-600">Outcome Detected</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
