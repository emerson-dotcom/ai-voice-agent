'use client'

import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useActiveCalls, useCallAnalytics } from '@/hooks/use-calls'
import { useAgentConfigs } from '@/hooks/use-agents'
import { formatDuration, getStatusColor } from '@/lib/utils'
import { 
  Phone, 
  Settings, 
  BarChart3, 
  Plus, 
  TrendingUp, 
  Clock,
  CheckCircle,
  AlertCircle,
  Users
} from 'lucide-react'

export default function DashboardPage() {
  const { data: activeCalls = [], isLoading: callsLoading } = useActiveCalls()
  const { data: analytics, isLoading: analyticsLoading } = useCallAnalytics(7)
  const { data: agentData, isLoading: agentsLoading } = useAgentConfigs()

  const agentConfigs = agentData?.configs || []
  const activeAgents = agentConfigs.filter(config => config.is_active && config.is_deployed)

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Welcome to AI Voice Agent</h1>
        <p className="text-gray-600 mt-2">
          Manage your logistics voice communications with intelligent AI agents
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Calls</CardTitle>
            <Phone className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCalls.length}</div>
            <p className="text-xs text-muted-foreground">
              {activeCalls.length > 0 ? 'In progress now' : 'No active calls'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeAgents.length}</div>
            <p className="text-xs text-muted-foreground">
              {agentConfigs.length} total configured
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.success_rate ? `${analytics.success_rate}%` : '--'}
            </div>
            <p className="text-xs text-muted-foreground">
              Last 7 days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.average_duration_seconds 
                ? formatDuration(Math.round(analytics.average_duration_seconds))
                : '--'
              }
            </div>
            <p className="text-xs text-muted-foreground">
              Per call average
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Calls */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Active Calls</CardTitle>
                <CardDescription>
                  Currently in-progress voice calls
                </CardDescription>
              </div>
              <Button asChild>
                <Link href="/dashboard/calls/new">
                  <Plus className="h-4 w-4 mr-2" />
                  New Call
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {callsLoading ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : activeCalls.length > 0 ? (
              <div className="space-y-3">
                {activeCalls.slice(0, 5).map((call) => (
                  <div key={call.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium">{call.driver_name}</p>
                      <p className="text-sm text-gray-600">Load {call.load_number}</p>
                    </div>
                    <div className="text-right">
                      <Badge className={getStatusColor(call.status)}>
                        {call.status.replace('_', ' ').toUpperCase()}
                      </Badge>
                      {call.duration && (
                        <p className="text-xs text-gray-500 mt-1">
                          {formatDuration(call.duration)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                {activeCalls.length > 5 && (
                  <div className="text-center pt-2">
                    <Button variant="outline" size="sm" asChild>
                      <Link href="/dashboard/calls">
                        View All ({activeCalls.length})
                      </Link>
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Phone className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No active calls</p>
                <Button className="mt-4" asChild>
                  <Link href="/dashboard/calls/new">Start a Call</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Analytics */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Call Analytics</CardTitle>
                <CardDescription>
                  Performance metrics for the last 7 days
                </CardDescription>
              </div>
              <Button variant="outline" asChild>
                <Link href="/dashboard/results">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  View Details
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {analyticsLoading ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : analytics ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <CheckCircle className="h-6 w-6 text-green-600 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-green-900">{analytics.completed_calls}</p>
                    <p className="text-sm text-green-700">Completed</p>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded-lg">
                    <AlertCircle className="h-6 w-6 text-red-600 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-red-900">{analytics.failed_calls}</p>
                    <p className="text-sm text-red-700">Failed</p>
                  </div>
                </div>

                {analytics.call_outcomes && Object.keys(analytics.call_outcomes).length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Call Outcomes</h4>
                    <div className="space-y-2">
                      {Object.entries(analytics.call_outcomes).map(([outcome, count]) => (
                        <div key={outcome} className="flex justify-between">
                          <span className="text-sm">{outcome}</span>
                          <span className="text-sm font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No analytics data available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks to get started with your voice agents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button asChild className="h-20 flex-col space-y-2">
              <Link href="/dashboard/agents/new">
                <Settings className="h-6 w-6" />
                <span>Configure New Agent</span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-20 flex-col space-y-2">
              <Link href="/dashboard/calls/new">
                <Phone className="h-6 w-6" />
                <span>Start Voice Call</span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-20 flex-col space-y-2">
              <Link href="/dashboard/results">
                <BarChart3 className="h-6 w-6" />
                <span>View Analytics</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
