'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { useCallHistory, useCallAnalytics } from '@/hooks/use-calls'
import type { CallList, CallAnalytics } from '@/types'
import { formatDistanceToNow, format } from 'date-fns'
import { 
  BarChart3, 
  Search, 
  Download,
  Eye,
  CheckCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  TrendingDown,
  Phone,
  Target,
  Activity
} from 'lucide-react'

export default function ResultsAnalyticsPage() {
  const { data: callHistoryData, isLoading: historyLoading } = useCallHistory() as { data: CallList | undefined, isLoading: boolean }
  const { data: analytics, isLoading: analyticsLoading } = useCallAnalytics(30) as { data: CallAnalytics | undefined, isLoading: boolean } // Last 30 days
  
  const [searchTerm, setSearchTerm] = useState('')
  const [outcomeFilter, setOutcomeFilter] = useState<string>('all')
  const [dateRange, setDateRange] = useState<string>('7') // days

  const callHistory = callHistoryData?.calls || []
  
  const filteredCalls = callHistory.filter(call => {
    const matchesSearch = !searchTerm || 
      call.driver_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      call.load_number.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesOutcome = outcomeFilter === 'all' || call.call_outcome === outcomeFilter
    
    const matchesDate = !dateRange || 
      (new Date(call.created_at) >= new Date(Date.now() - parseInt(dateRange) * 24 * 60 * 60 * 1000))
    
    return matchesSearch && matchesOutcome && matchesDate && call.status === 'completed'
  })

  const getOutcomeBadge = (outcome: string) => {
    switch (outcome) {
      case 'In-Transit Update':
        return <Badge className="bg-blue-100 text-blue-800"><Activity className="h-3 w-3 mr-1" />In-Transit</Badge>
      case 'Arrival Confirmation':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Arrived</Badge>
      case 'Emergency Escalation':
        return <Badge className="bg-red-100 text-red-800"><AlertTriangle className="h-3 w-3 mr-1" />Emergency</Badge>
      default:
        return <Badge variant="outline">{outcome}</Badge>
    }
  }

  const getDataQualityScore = (extractedData: Record<string, unknown> | null | undefined) => {
    if (!extractedData) return 0
    
    const fields = Object.values(extractedData).filter(value => 
      value !== null && value !== undefined && value !== ''
    )
    const totalFields = Object.keys(extractedData).length
    
    return totalFields > 0 ? Math.round((fields.length / totalFields) * 100) : 0
  }

  const getQualityBadge = (score: number) => {
    if (score >= 90) {
      return <Badge className="bg-green-100 text-green-800">Excellent ({score}%)</Badge>
    } else if (score >= 70) {
      return <Badge className="bg-yellow-100 text-yellow-800">Good ({score}%)</Badge>
    } else {
      return <Badge className="bg-red-100 text-red-800">Poor ({score}%)</Badge>
    }
  }

  if (historyLoading || analyticsLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Results & Analytics</h1>
            <p className="text-gray-600">Analyze call outcomes and data extraction performance</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Results & Analytics</h1>
          <p className="text-gray-600">Analyze call outcomes and data extraction performance</p>
        </div>
        <Button variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Export Data
        </Button>
      </div>

      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Phone className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Calls</p>
                <p className="text-2xl font-bold text-gray-900">{analytics?.total_calls || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics?.success_rate ? `${Math.round(analytics.success_rate)}%` : '0%'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Target className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Data Quality</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics?.success_rate ? `${Math.round(analytics.success_rate)}%` : '0%'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-orange-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Duration</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics?.average_duration_seconds ? `${Math.round(analytics.average_duration_seconds / 60)}m` : '0m'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Outcome Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Call Outcomes</CardTitle>
            <CardDescription>Distribution of call results</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics?.call_outcomes && Object.entries(analytics.call_outcomes).map(([outcome, count]) => (
                <div key={outcome} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getOutcomeBadge(outcome)}
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold">{count as number}</div>
                    <div className="text-sm text-gray-500">
                      {analytics.total_calls > 0 
                        ? `${Math.round(((count as number) / analytics.total_calls) * 100)}%`
                        : '0%'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data Quality Trends</CardTitle>
            <CardDescription>Data extraction performance over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <TrendingUp className="h-5 w-5 text-green-500" />
                  <div>
                    <div className="font-medium">Excellent Quality</div>
                    <div className="text-sm text-gray-600">90-100% data extracted</div>
                  </div>
                </div>
                <div className="text-lg font-semibold text-green-700">
                  {filteredCalls.filter(call => getDataQualityScore(call.conversation_metadata) >= 90).length}
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Activity className="h-5 w-5 text-yellow-500" />
                  <div>
                    <div className="font-medium">Good Quality</div>
                    <div className="text-sm text-gray-600">70-89% data extracted</div>
                  </div>
                </div>
                <div className="text-lg font-semibold text-yellow-700">
                  {filteredCalls.filter(call => {
                    const score = getDataQualityScore(call.conversation_metadata)
                    return score >= 70 && score < 90
                  }).length}
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <TrendingDown className="h-5 w-5 text-red-500" />
                  <div>
                    <div className="font-medium">Poor Quality</div>
                    <div className="text-sm text-gray-600">Below 70% data extracted</div>
                  </div>
                </div>
                <div className="text-lg font-semibold text-red-700">
                  {filteredCalls.filter(call => getDataQualityScore(call.conversation_metadata) < 70).length}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by driver name or load number..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex space-x-2">
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
              </select>
              <Button
                variant={outcomeFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setOutcomeFilter('all')}
              >
                All
              </Button>
              <Button
                variant={outcomeFilter === 'In-Transit Update' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setOutcomeFilter('In-Transit Update')}
              >
                In-Transit
              </Button>
              <Button
                variant={outcomeFilter === 'Arrival Confirmation' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setOutcomeFilter('Arrival Confirmation')}
              >
                Arrivals
              </Button>
              <Button
                variant={outcomeFilter === 'Emergency Escalation' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setOutcomeFilter('Emergency Escalation')}
              >
                Emergency
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Results */}
      <Card>
        <CardHeader>
          <CardTitle>Call Results</CardTitle>
          <CardDescription>
            Detailed view of call outcomes and extracted data
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredCalls.length === 0 ? (
            <div className="text-center py-12">
              <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h3>
              <p className="text-gray-600">
                {searchTerm || outcomeFilter !== 'all' 
                  ? 'Try adjusting your search or filters.'
                  : 'Complete some calls to see results here.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredCalls.map((call) => (
                <div key={call.id} className="border rounded-lg p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      <div>
                        <h3 className="font-medium text-lg">{call.driver_name}</h3>
                        <p className="text-sm text-gray-600">
                          Load #{call.load_number} • {format(new Date(call.created_at), 'MMM d, yyyy HH:mm')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {call.call_outcome && getOutcomeBadge(call.call_outcome)}
                      {getQualityBadge(getDataQualityScore(call.conversation_metadata))}
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/dashboard/results/${call.id}`}>
                          <Eye className="h-4 w-4 mr-1" />
                          View Details
                        </Link>
                      </Button>
                    </div>
                  </div>

                  {/* Key Extracted Data Preview */}
                  {call.conversation_metadata && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      {Object.entries(call.conversation_metadata).slice(0, 4).map(([key, value]) => (
                        <div key={key} className="bg-gray-50 p-3 rounded">
                          <div className="font-medium text-gray-700 capitalize">
                            {key.replace(/_/g, ' ')}
                          </div>
                          <div className="text-gray-900 mt-1">
                            {typeof value === 'boolean' 
                              ? (value ? 'Yes' : 'No')
                              : (value || 'N/A')}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Call Metrics */}
                  <div className="flex items-center justify-between mt-4 pt-4 border-t text-sm text-gray-600">
                    <div className="flex items-center space-x-6">
                      <span>Duration: {call.duration ? `${Math.floor(call.duration / 60)}:${(call.duration % 60).toString().padStart(2, '0')}` : 'N/A'}</span>
                      <span>Agent Config ID: {call.agent_config_id}</span>
                    </div>
                    <div>
                      {formatDistanceToNow(new Date(call.created_at))} ago
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
