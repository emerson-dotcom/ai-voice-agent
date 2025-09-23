'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import CallResults from '@/components/call-results'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { BarChart3, ArrowLeft, RefreshCw, Phone, Download, Loader2 } from 'lucide-react'
import { Call, Agent } from '@/types'
import { AuthGuard } from '@/components/AuthGuard'
import { Header } from '@/components/Header'
import { agentApi, callApi, retellApi } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { useToast } from '@/hooks/use-toast'

export default function ResultsPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { toast } = useToast()
  const callId = searchParams?.get('call_id')

  const [calls, setCalls] = useState<Call[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedCall, setSelectedCall] = useState<Call | null>(null)
  const [loading, setLoading] = useState(true)
  const [fetchingCallData, setFetchingCallData] = useState<string | null>(null)

  useEffect(() => {
    fetchCalls()
    fetchAgents()

    // If call_id is provided, select that call
    if (callId) {
      fetchSpecificCall(callId)
    }
  }, [callId])

  const fetchCalls = async () => {
    try {
      console.log('Fetching calls from API...')
      const data = await callApi.list()
      console.log(`Fetched ${data.length} calls:`, data.map(c => ({ id: c.id, status: c.call_status, transcript: !!c.transcript })))
      setCalls(data)

      // If no specific call selected, select the most recent one
      if (!callId && data.length > 0) {
        setSelectedCall(data[0])
      }
    } catch (error) {
      console.error('Error fetching calls:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchAgents = async () => {
    try {
      const data = await agentApi.list()
      setAgents(data)
    } catch (error) {
      console.error('Error fetching agents:', error)
    }
  }

  const fetchSpecificCall = async (callId: string) => {
    try {
      const call = await callApi.get(callId)
      setSelectedCall(call)
    } catch (error) {
      console.error('Error fetching specific call:', error)
    }
  }

  const getAgent = (agentId: string) => {
    return agents.find(agent => agent.id === agentId)
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const formatDuration = (durationMs: number): string => {
    const seconds = Math.floor(durationMs / 1000)
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const attendCall = (call: Call) => {
    if (call.retell_access_token && (call.call_status === 'registered' || call.call_status === 'ongoing')) {
      router.push(`/call/${call.id}`)
    } else {
      toast({
        title: 'Cannot Attend Call',
        description: 'This call is not available for attendance or has already ended.',
        variant: 'destructive'
      })
    }
  }

  const fetchCallData = async (call: Call) => {
    if (!call.retell_call_id) {
      toast({
        title: 'No Retell Call ID',
        description: 'This call does not have a Retell call ID to fetch data from.',
        variant: 'destructive'
      })
      return
    }

    setFetchingCallData(call.id)
    try {
      // Call our backend endpoint to fetch data from Retell
      const retellData = await retellApi.getCallData(call.retell_call_id)

      toast({
        title: 'Call Data Retrieved',
        description: `Data fetched from ${retellData.source || 'Retell API'} for call ${call.retell_call_id}`,
        variant: 'default'
      })

      // Update the selected call with the new data
      setSelectedCall({ ...call, ...retellData })

      // Force refresh the calls list to show updated data
      console.log('Refreshing calls list after data fetch...')
      // Small delay to ensure database update is committed
      setTimeout(async () => {
        await fetchCalls()
      }, 500)

      // Also update the call in the current calls list if it exists
      setCalls(prevCalls =>
        prevCalls.map(c =>
          c.id === call.id
            ? { ...c, ...retellData, updated: true }
            : c
        )
      )

    } catch (error) {
      console.error('Error fetching call data:', error)
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to fetch call data',
        variant: 'destructive'
      })
    } finally {
      setFetchingCallData(null)
    }
  }

  return (
    <AuthGuard>
      <Header />
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-4">
              Call Results & Analytics
            </h1>
            <p className="text-xl text-slate-600">
              Review call transcripts, structured data extraction, and performance analytics
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={fetchCalls}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" onClick={() => window.history.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">Loading call results...</p>
          </div>
        ) : calls.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-semibold mb-2">No Call Results Found</h3>
              <p className="text-muted-foreground mb-4">
                Start some test calls to see results and analytics here
              </p>
              <Button onClick={() => window.location.href = '/calls'}>
                Start New Call
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Call List Sidebar */}
            <div className="xl:col-span-1">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Calls</CardTitle>
                  <CardDescription>
                    Select a call to view detailed results
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="space-y-0">
                    {calls.map((call) => {
                      const agent = getAgent(call.agent_id)
                      return (
                        <div
                          key={call.id}
                          className={`p-4 border-b transition-colors ${
                            selectedCall?.id === call.id ? 'bg-muted' : ''
                          }`}
                        >
                          <div className="space-y-3">
                            <div
                              className="cursor-pointer hover:bg-muted/30 p-2 rounded"
                              onClick={() => setSelectedCall(call)}
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-sm">
                                  {call.driver_name || 'Unknown Driver'}
                                </span>
                                <Badge
                                  className={getStatusColor(call.call_status)}
                                  variant="secondary"
                                >
                                  {call.call_status}
                                </Badge>
                              </div>
                              <div className="text-xs text-muted-foreground mt-2">
                                <p>Load: {call.load_number}</p>
                                <p>Agent: {agent?.name || 'Unknown'}</p>
                                {call.duration_ms && (
                                  <p>Duration: {formatDuration(call.duration_ms)}</p>
                                )}
                                <p>
                                  {new Date(call.created_at).toLocaleDateString()} {' '}
                                  {new Date(call.created_at).toLocaleTimeString()}
                                </p>
                              </div>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  attendCall(call)
                                }}
                                disabled={!call.retell_access_token || !['registered', 'ongoing'].includes(call.call_status)}
                                className="flex-1"
                              >
                                <Phone className="h-3 w-3 mr-1" />
                                Attend
                              </Button>

                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  fetchCallData(call)
                                }}
                                disabled={!call.retell_call_id || fetchingCallData === call.id}
                                className="flex-1"
                              >
                                {fetchingCallData === call.id ? (
                                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                ) : (
                                  <Download className="h-3 w-3 mr-1" />
                                )}
                                {fetchingCallData === call.id ? 'Loading...' : 'Get Data'}
                              </Button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Call Results Detail */}
            <div className="xl:col-span-3">
              {selectedCall ? (
                <CallResults
                  call={selectedCall}
                />
              ) : (
                <Card>
                  <CardContent className="text-center py-12">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-semibold mb-2">Select a Call</h3>
                    <p className="text-muted-foreground">
                      Choose a call from the list to view detailed results and analytics
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
    </AuthGuard>
  )
}