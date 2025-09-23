'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Call, CallResult } from '@/types'
import {
  Clock,
  Phone,
  User,
  Truck,
  MapPin,
  Calendar,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Download,
  Play,
  FileText,
  BarChart3
} from 'lucide-react'

interface CallResultsProps {
  call: Call & {
    call_results?: CallResult;
    agents?: { name: string; scenario_type: string };
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'ended': return 'default'
    case 'ongoing': return 'secondary'
    case 'error': return 'destructive'
    default: return 'outline'
  }
}

const getOutcomeColor = (outcome: string) => {
  switch (outcome) {
    case 'in_transit_update': return 'default'
    case 'arrival_confirmation': return 'default'
    case 'emergency_escalation': return 'destructive'
    default: return 'outline'
  }
}

const formatDuration = (durationMs?: number) => {
  if (!durationMs) return 'N/A'
  const seconds = Math.floor(durationMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export default function CallResults({ call }: CallResultsProps) {
  const [selectedTranscriptIndex, setSelectedTranscriptIndex] = useState<number | null>(null)

  // Handle both structured transcript and plain text transcript
  let transcriptArray = call.transcript_object || []

  // If we have plain text transcript but no structured transcript, create simple structure
  if (!transcriptArray.length && call.transcript) {
    // Parse simple transcript format like "Agent: ... \nAgent: ..."
    const lines = call.transcript.split('\n').filter(line => line.trim())
    transcriptArray = lines.map((line, index) => {
      const [role, ...textParts] = line.split(': ')
      return {
        role: role.toLowerCase() === 'agent' ? 'agent' : 'user',
        content: textParts.join(': '),
        timestamp: index, // Simple sequential timestamp
        words: textParts.join(': ').split(' ').map((word, i) => ({
          word,
          start: i,
          end: i + 1
        }))
      }
    })
  }

  const results = call.call_results

  return (
    <div className="space-y-6">
      {/* Call Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Phone className="h-5 w-5" />
                Call Details
              </CardTitle>
              <CardDescription>
                Call ID: {call.id}
              </CardDescription>
            </div>
            <Badge variant={getStatusColor(call.call_status)}>
              {call.call_status.charAt(0).toUpperCase() + call.call_status.slice(1)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">
                  {call.driver_name || call.metadata?.driver_name || 'Unknown Driver'}
                </p>
                <p className="text-xs text-muted-foreground">Driver</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Truck className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">
                  {call.load_number || call.metadata?.load_number || 'N/A'}
                </p>
                <p className="text-xs text-muted-foreground">Load Number</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">{formatDuration(call.duration_ms)}</p>
                <p className="text-xs text-muted-foreground">Duration</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">
                  {call.start_timestamp ? new Date(call.start_timestamp).toLocaleString() : 'N/A'}
                </p>
                <p className="text-xs text-muted-foreground">Started</p>
              </div>
            </div>
          </div>

          {call.agents && (
            <div className="mt-4 p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4" />
                <span className="font-medium">{call.agents.name}</span>
                <Badge variant="outline" className="text-xs">
                  {call.agents.scenario_type === 'driver_checkin' ? 'Driver Check-in' : 'Emergency Protocol'}
                </Badge>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="results" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="results" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Results
          </TabsTrigger>
          <TabsTrigger value="transcript" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Transcript
          </TabsTrigger>
          <TabsTrigger value="analysis" className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="recording" className="flex items-center gap-2">
            <Play className="h-4 w-4" />
            Recording
          </TabsTrigger>
        </TabsList>

        {/* Structured Results */}
        <TabsContent value="results" className="space-y-4">
          {results ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Call Outcome */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Call Outcome</CardTitle>
                </CardHeader>
                <CardContent>
                  {results.call_outcome && (
                    <div className="flex items-center gap-2 mb-4">
                      <Badge variant={getOutcomeColor(results.call_outcome)}>
                        {results.call_outcome.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Badge>
                      {results.confidence_score && (
                        <span className="text-sm text-muted-foreground">
                          {Math.round(results.confidence_score * 100)}% confidence
                        </span>
                      )}
                    </div>
                  )}

                  <div className="space-y-3">
                    {/* Driver Check-in Results */}
                    {results.call_outcome !== 'emergency_escalation' && (
                      <>
                        {results.driver_status && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Driver Status</label>
                            <p className="text-sm">{results.driver_status.charAt(0).toUpperCase() + results.driver_status.slice(1)}</p>
                          </div>
                        )}

                        {results.current_location && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Current Location</label>
                            <p className="text-sm flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {results.current_location}
                            </p>
                          </div>
                        )}

                        {results.eta && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">ETA</label>
                            <p className="text-sm">{results.eta}</p>
                          </div>
                        )}

                        {results.delay_reason && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Delay Reason</label>
                            <p className="text-sm">{results.delay_reason}</p>
                          </div>
                        )}

                        {results.unloading_status && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Unloading Status</label>
                            <p className="text-sm">{results.unloading_status}</p>
                          </div>
                        )}

                        {results.pod_reminder_acknowledged !== null && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">POD Reminder</label>
                            <p className="text-sm flex items-center gap-1">
                              {results.pod_reminder_acknowledged ? (
                                <><CheckCircle className="h-3 w-3 text-green-500" /> Acknowledged</>
                              ) : (
                                <><XCircle className="h-3 w-3 text-red-500" /> Not Acknowledged</>
                              )}
                            </p>
                          </div>
                        )}
                      </>
                    )}

                    {/* Emergency Results */}
                    {results.call_outcome === 'emergency_escalation' && (
                      <>
                        {results.emergency_type && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Emergency Type</label>
                            <p className="text-sm flex items-center gap-1">
                              <AlertTriangle className="h-3 w-3 text-red-500" />
                              {results.emergency_type.charAt(0).toUpperCase() + results.emergency_type.slice(1)}
                            </p>
                          </div>
                        )}

                        {results.safety_status && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Safety Status</label>
                            <p className="text-sm">{results.safety_status}</p>
                          </div>
                        )}

                        {results.injury_status && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Injury Status</label>
                            <p className="text-sm">{results.injury_status}</p>
                          </div>
                        )}

                        {results.emergency_location && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Emergency Location</label>
                            <p className="text-sm flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {results.emergency_location}
                            </p>
                          </div>
                        )}

                        {results.load_secure !== null && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Load Secure</label>
                            <p className="text-sm flex items-center gap-1">
                              {results.load_secure ? (
                                <><CheckCircle className="h-3 w-3 text-green-500" /> Secure</>
                              ) : (
                                <><XCircle className="h-3 w-3 text-red-500" /> Not Secure</>
                              )}
                            </p>
                          </div>
                        )}

                        {results.escalation_status && (
                          <div>
                            <label className="text-sm font-medium text-muted-foreground">Escalation Status</label>
                            <p className="text-sm">{results.escalation_status}</p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Additional Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Additional Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Extraction Method</label>
                      <p className="text-sm">{results.extraction_method || 'N/A'}</p>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Extracted At</label>
                      <p className="text-sm">
                        {new Date(results.extracted_at).toLocaleString()}
                      </p>
                    </div>

                    {results.custom_analysis_data && Object.keys(results.custom_analysis_data).length > 0 && (
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Custom Analysis</label>
                        <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-auto">
                          {JSON.stringify(results.custom_analysis_data, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : call.call_analysis ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Fallback: Show Retell Analysis as Results */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Call Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {call.call_analysis.call_summary && (
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Summary</label>
                        <p className="text-sm mt-1">{call.call_analysis.call_summary}</p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      {call.call_analysis.call_successful !== undefined && (
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Call Success</label>
                          <p className="text-sm flex items-center gap-1 mt-1">
                            {call.call_analysis.call_successful ? (
                              <><CheckCircle className="h-3 w-3 text-green-500" /> Successful</>
                            ) : (
                              <><XCircle className="h-3 w-3 text-red-500" /> Unsuccessful</>
                            )}
                          </p>
                        </div>
                      )}

                      {call.call_analysis.user_sentiment && (
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">User Sentiment</label>
                          <Badge variant="outline" className="mt-1">
                            {call.call_analysis.user_sentiment}
                          </Badge>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Call Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 gap-3">
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Duration</label>
                        <p className="text-sm mt-1">{formatDuration(call.duration_ms)}</p>
                      </div>

                      {call.disconnection_reason && (
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">End Reason</label>
                          <Badge variant="outline" className="mt-1">
                            {call.disconnection_reason.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </Badge>
                        </div>
                      )}

                      {call.call_analysis.in_voicemail !== undefined && (
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Voicemail Detected</label>
                          <p className="text-sm mt-1">
                            {call.call_analysis.in_voicemail ? 'Yes' : 'No'}
                          </p>
                        </div>
                      )}

                      {call.call_analysis.custom_analysis_data && Object.keys(call.call_analysis.custom_analysis_data).length > 0 && (
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Additional Data</label>
                          <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-auto max-h-32">
                            {JSON.stringify(call.call_analysis.custom_analysis_data, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-muted-foreground">
                  <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                  <p>No call results available yet.</p>
                  <p className="text-sm">Results will appear here after the call is analyzed.</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Transcript */}
        <TabsContent value="transcript">
          <Card>
            <CardHeader>
              <CardTitle>Call Transcript</CardTitle>
              <CardDescription>
                Complete conversation transcript with timestamps
              </CardDescription>
            </CardHeader>
            <CardContent>
              {transcriptArray.length > 0 ? (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {transcriptArray.map((utterance: any, index: number) => (
                    <div
                      key={index}
                      className="flex gap-3 p-3 rounded-lg hover:bg-muted/50 cursor-pointer"
                      onClick={() => setSelectedTranscriptIndex(selectedTranscriptIndex === index ? null : index)}
                    >
                      <div className="flex-shrink-0">
                        <Badge variant={utterance.role === 'agent' ? 'default' : 'secondary'}>
                          {utterance.role === 'agent' ? 'Agent' : 'User'}
                        </Badge>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm">{utterance.content}</p>
                        {selectedTranscriptIndex === index && utterance.words && (
                          <div className="mt-2 text-xs text-muted-foreground">
                            <p>Word-level timestamps:</p>
                            <div className="mt-1 space-x-1">
                              {utterance.words.map((word: any, wordIndex: number) => (
                                <span key={wordIndex} className="inline-block">
                                  {word.word}
                                  <span className="text-xs ml-1 text-muted-foreground">
                                    ({word.start?.toFixed(1)}s)
                                  </span>
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : call.transcript ? (
                <div className="bg-muted p-4 rounded-lg">
                  <pre className="whitespace-pre-wrap text-sm">{call.transcript}</pre>
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  <FileText className="h-12 w-12 mx-auto mb-2" />
                  <p>No transcript available for this call.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analysis */}
        <TabsContent value="analysis">
          <Card>
            <CardHeader>
              <CardTitle>Call Analysis</CardTitle>
              <CardDescription>
                AI-generated analysis of the call
              </CardDescription>
            </CardHeader>
            <CardContent>
              {call.call_analysis ? (
                <div className="space-y-4">
                  {call.call_analysis.call_summary && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Summary</label>
                      <p className="text-sm mt-1">{call.call_analysis.call_summary}</p>
                    </div>
                  )}

                  {call.call_analysis.user_sentiment && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">User Sentiment</label>
                      <Badge variant="outline" className="ml-2">
                        {call.call_analysis.user_sentiment}
                      </Badge>
                    </div>
                  )}

                  {call.call_analysis.call_successful !== undefined && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Call Successful</label>
                      <p className="text-sm flex items-center gap-1 mt-1">
                        {call.call_analysis.call_successful ? (
                          <><CheckCircle className="h-3 w-3 text-green-500" /> Yes</>
                        ) : (
                          <><XCircle className="h-3 w-3 text-red-500" /> No</>
                        )}
                      </p>
                    </div>
                  )}

                  {call.call_analysis.in_voicemail !== undefined && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Voicemail</label>
                      <p className="text-sm mt-1">
                        {call.call_analysis.in_voicemail ? 'Yes' : 'No'}
                      </p>
                    </div>
                  )}

                  {/* Recording Section */}
                  {call.recording_url && (
                    <div className="border-t pt-4 mt-4">
                      <label className="text-sm font-medium text-muted-foreground">Call Recording</label>
                      <div className="mt-2 space-y-2">
                        <audio controls className="w-full">
                          <source src={call.recording_url} type="audio/wav" />
                          Your browser does not support the audio element.
                        </audio>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(call.recording_url, '_blank')}
                          >
                            <Download className="h-3 w-3 mr-1" />
                            Download
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Disconnection Reason */}
                  {call.disconnection_reason && (
                    <div className="border-t pt-4 mt-4">
                      <label className="text-sm font-medium text-muted-foreground">Disconnection Reason</label>
                      <Badge variant="outline" className="ml-2">
                        {call.disconnection_reason.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Badge>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  <CheckCircle className="h-12 w-12 mx-auto mb-2" />
                  <p>No analysis available for this call.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recording */}
        <TabsContent value="recording">
          <Card>
            <CardHeader>
              <CardTitle>Call Recording</CardTitle>
              <CardDescription>
                Audio recording and related files
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {call.recording_url && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Main Recording</label>
                    <div className="mt-2">
                      <audio controls className="w-full">
                        <source src={call.recording_url} type="audio/wav" />
                        Your browser does not support the audio element.
                      </audio>
                    </div>
                    <Button variant="outline" size="sm" className="mt-2" asChild>
                      <a href={call.recording_url} download>
                        <Download className="h-3 w-3 mr-1" />
                        Download
                      </a>
                    </Button>
                  </div>
                )}

                {call.public_log_url && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Public Log</label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Detailed log of the call for debugging and analysis
                    </p>
                    <Button variant="outline" size="sm" className="mt-2" asChild>
                      <a href={call.public_log_url} target="_blank" rel="noopener noreferrer">
                        <FileText className="h-3 w-3 mr-1" />
                        View Log
                      </a>
                    </Button>
                  </div>
                )}

                {!call.recording_url && !call.public_log_url && (
                  <div className="text-center text-muted-foreground py-8">
                    <Play className="h-12 w-12 mx-auto mb-2" />
                    <p>No recording available for this call.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}