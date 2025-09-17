'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useCallDetail, useCallTranscript } from '@/hooks/use-calls'
import { 
  ArrowLeft, 
  Download, 
  Clock,
  User,
  MessageSquare,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  MapPin,
  Calendar,
  FileText,
  Volume2,
  Activity
} from 'lucide-react'
import Link from 'next/link'
import { format } from 'date-fns'
import type { CheckInData, EmergencyData, CallDetail, Transcript } from '@/types'

export default function CallResultDetailPage() {
  const params = useParams()
  const callId = parseInt(params?.id as string)
  
  const { data: callDetail, isLoading: loadingCall } = useCallDetail(callId) as { data: CallDetail | undefined, isLoading: boolean }
  const { data: transcript, isLoading: loadingTranscript } = useCallTranscript(callId) as { data: Transcript | undefined, isLoading: boolean }
  
  const [activeTab, setActiveTab] = useState<'overview' | 'transcript' | 'data'>('overview')

  const handleExport = () => {
    if (!callDetail) return
    
    const exportData = {
      call_id: callDetail.id,
      driver_name: callDetail.driver_name,
      phone_number: callDetail.phone_number,
      load_number: callDetail.load_number,
      status: callDetail.status,
      duration: callDetail.duration,
      start_time: callDetail.start_time,
      end_time: callDetail.end_time,
      structured_data: callDetail.structured_data,
      transcript: transcript,
      exported_at: new Date().toISOString(),
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `call-${callId}-results.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'in_progress': return 'bg-blue-100 text-blue-800'
      case 'cancelled': return 'bg-gray-100 text-gray-800'
      default: return 'bg-yellow-100 text-yellow-800'
    }
  }

  const getOutcomeColor = (outcome: string) => {
    switch (outcome) {
      case 'In-Transit Update': return 'bg-blue-100 text-blue-800'
      case 'Arrival Confirmation': return 'bg-green-100 text-green-800'
      case 'Emergency Escalation': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (loadingCall) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading call details...</p>
        </div>
      </div>
    )
  }

  if (!callDetail) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Call Not Found</h2>
          <p className="text-gray-600 mb-4">The call results you&apos;re looking for don&apos;t exist.</p>
          <Link href="/dashboard/results">
            <Button>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Results
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  const structuredData = callDetail.structured_data as CheckInData | EmergencyData | undefined

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/dashboard/results">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back
                </Button>
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Call Results</h1>
                <p className="text-gray-600">Detailed analysis and transcript for call #{callId}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                onClick={handleExport}
                variant="outline"
                className="flex items-center"
              >
                <Download className="h-4 w-4 mr-2" />
                Export Results
              </Button>
              <Badge className={getStatusColor(callDetail.status)}>
                {callDetail.status.replace('_', ' ').toUpperCase()}
              </Badge>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Clock className="h-8 w-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Duration</p>
                  <p className="text-2xl font-bold text-gray-900">{formatDuration(callDetail.duration)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Quality Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {callDetail.conversation_quality_score ? `${Math.round(callDetail.conversation_quality_score * 100)}%` : 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Activity className="h-8 w-8 text-purple-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Confidence</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {callDetail.extraction_confidence ? `${Math.round(callDetail.extraction_confidence * 100)}%` : 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <MessageSquare className="h-8 w-8 text-orange-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Turns</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {transcript?.turns?.length || 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Call Info */}
          <div className="lg:col-span-1">
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <User className="h-5 w-5 mr-2" />
                  Call Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Driver</span>
                  <span className="text-sm text-gray-900">{callDetail.driver_name}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Phone</span>
                  <span className="text-sm text-gray-900">{callDetail.phone_number}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Load #</span>
                  <span className="text-sm text-gray-900">{callDetail.load_number}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Agent</span>
                  <span className="text-sm text-gray-900">{callDetail.agent_config_name || 'N/A'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Scenario</span>
                  <Badge variant="outline">
                    {callDetail.scenario_type === 'check_in' ? 'Check-in' : 'Emergency'}
                  </Badge>
                </div>
                {callDetail.start_time && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">Started</span>
                    <span className="text-sm text-gray-900">
                      {format(new Date(callDetail.start_time), 'MMM d, yyyy h:mm a')}
                    </span>
                  </div>
                )}
                {callDetail.end_time && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">Ended</span>
                    <span className="text-sm text-gray-900">
                      {format(new Date(callDetail.end_time), 'MMM d, yyyy h:mm a')}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Call Outcome */}
            {callDetail.call_outcome && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <CheckCircle className="h-5 w-5 mr-2" />
                    Call Outcome
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge className={getOutcomeColor(callDetail.call_outcome)}>
                    {callDetail.call_outcome}
                  </Badge>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column - Detailed Results */}
          <div className="lg:col-span-2">
            {/* Tab Navigation */}
            <div className="mb-6">
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8">
                  <button
                    onClick={() => setActiveTab('overview')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'overview'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <BarChart3 className="h-4 w-4 inline mr-2" />
                    Overview
                  </button>
                  <button
                    onClick={() => setActiveTab('transcript')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'transcript'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <MessageSquare className="h-4 w-4 inline mr-2" />
                    Transcript
                  </button>
                  <button
                    onClick={() => setActiveTab('data')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'data'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <FileText className="h-4 w-4 inline mr-2" />
                    Extracted Data
                  </button>
                </nav>
              </div>
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
              <Card>
                <CardHeader>
                  <CardTitle>Call Summary</CardTitle>
                  <CardDescription>
                    Overview of call performance and key metrics
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {callDetail.error_message && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-4">
                      <div className="flex">
                        <AlertTriangle className="h-5 w-5 text-red-400" />
                        <div className="ml-3">
                          <h3 className="text-sm font-medium text-red-800">Call Error</h3>
                          <p className="mt-1 text-sm text-red-700">{callDetail.error_message}</p>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Performance Metrics</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Quality Score</span>
                          <span className="text-sm font-medium">
                            {callDetail.conversation_quality_score 
                              ? `${Math.round(callDetail.conversation_quality_score * 100)}%`
                              : 'Not available'
                            }
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Extraction Confidence</span>
                          <span className="text-sm font-medium">
                            {callDetail.extraction_confidence 
                              ? `${Math.round(callDetail.extraction_confidence * 100)}%`
                              : 'Not available'
                            }
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Call Duration</span>
                          <span className="text-sm font-medium">{formatDuration(callDetail.duration)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Call Timeline</h4>
                      <div className="space-y-2">
                        {callDetail.start_time && (
                          <div className="flex items-center text-sm">
                            <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                            <span className="text-gray-600">Started:</span>
                            <span className="ml-2 font-medium">
                              {format(new Date(callDetail.start_time), 'h:mm a')}
                            </span>
                          </div>
                        )}
                        {callDetail.end_time && (
                          <div className="flex items-center text-sm">
                            <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                            <span className="text-gray-600">Ended:</span>
                            <span className="ml-2 font-medium">
                              {format(new Date(callDetail.end_time), 'h:mm a')}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === 'transcript' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Volume2 className="h-5 w-5 mr-2" />
                    Conversation Transcript
                  </CardTitle>
                  <CardDescription>
                    Complete conversation between AI agent and driver
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loadingTranscript ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="mt-2 text-sm text-gray-600">Loading transcript...</p>
                    </div>
                  ) : transcript?.turns && transcript.turns.length > 0 ? (
                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      {transcript.turns.map((turn, index) => (
                        <div key={index} className={`flex ${turn.speaker === 'agent' ? 'justify-start' : 'justify-end'}`}>
                          <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            turn.speaker === 'agent'
                              ? 'bg-blue-100 text-blue-900'
                              : 'bg-gray-100 text-gray-900'
                          }`}>
                            <div className="flex items-center mb-1">
                              <span className="text-xs font-medium">
                                {turn.speaker === 'agent' ? 'AI Agent' : 'Driver'}
                              </span>
                              <span className="text-xs text-gray-500 ml-2">
                                {format(new Date(turn.timestamp), 'h:mm:ss a')}
                              </span>
                            </div>
                            <p className="text-sm">{turn.message}</p>
                            {turn.emergency_trigger_detected && (
                              <div className="mt-2 flex items-center text-xs text-red-600">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                Emergency detected
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <MessageSquare className="h-8 w-8 mx-auto mb-2" />
                      <p>No transcript available for this call</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {activeTab === 'data' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <FileText className="h-5 w-5 mr-2" />
                    Extracted Structured Data
                  </CardTitle>
                  <CardDescription>
                    Key information extracted from the conversation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {structuredData ? (
                    <div className="space-y-4">
                      {callDetail.scenario_type === 'check_in' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Driver Status</h4>
                            <Badge variant="outline">
                              {(structuredData as CheckInData).driver_status || 'Unknown'}
                            </Badge>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Call Outcome</h4>
                            <Badge className={getOutcomeColor((structuredData as CheckInData).call_outcome || '')}>
                              {(structuredData as CheckInData).call_outcome || 'Unknown'}
                            </Badge>
                          </div>
                          {(structuredData as CheckInData).current_location && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">Current Location</h4>
                              <div className="flex items-center text-sm text-gray-700">
                                <MapPin className="h-4 w-4 mr-1" />
                                {(structuredData as CheckInData).current_location}
                              </div>
                            </div>
                          )}
                          {(structuredData as CheckInData).eta && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">ETA</h4>
                              <p className="text-sm text-gray-700">{(structuredData as CheckInData).eta}</p>
                            </div>
                          )}
                          {(structuredData as CheckInData).delay_reason && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">Delay Reason</h4>
                              <p className="text-sm text-gray-700">{(structuredData as CheckInData).delay_reason}</p>
                            </div>
                          )}
                        </div>
                      )}

                      {callDetail.scenario_type === 'emergency' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Emergency Type</h4>
                            <Badge variant="outline" className="text-red-600 border-red-300">
                              {(structuredData as EmergencyData).emergency_type || 'Unknown'}
                            </Badge>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Safety Status</h4>
                            <p className="text-sm text-gray-700">
                              {(structuredData as EmergencyData).safety_status || 'Unknown'}
                            </p>
                          </div>
                          {(structuredData as EmergencyData).emergency_location && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">Emergency Location</h4>
                              <div className="flex items-center text-sm text-gray-700">
                                <MapPin className="h-4 w-4 mr-1" />
                                {(structuredData as EmergencyData).emergency_location}
                              </div>
                            </div>
                          )}
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Load Secure</h4>
                            <Badge variant={
                              (structuredData as EmergencyData).load_secure ? 'default' : 'secondary'
                            }>
                              {(structuredData as EmergencyData).load_secure ? 'Yes' : 'No'}
                            </Badge>
                          </div>
                        </div>
                      )}

                      {/* Raw Data */}
                      <div className="mt-6 pt-4 border-t">
                        <h4 className="font-medium text-gray-900 mb-2">Raw Extracted Data</h4>
                        <pre className="bg-gray-50 p-4 rounded-md text-xs overflow-x-auto">
                          {JSON.stringify(structuredData, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <FileText className="h-8 w-8 mx-auto mb-2" />
                      <p>No structured data extracted from this call</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
