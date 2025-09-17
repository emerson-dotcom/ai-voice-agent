'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useAgentConfigs, useDeleteAgentConfig, useDeployAgentConfig } from '@/hooks/use-agents'
import { formatDistanceToNow } from 'date-fns'
import { 
  Settings, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Pause, 
  Eye,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'

export default function AgentConfigurationPage() {
  const { data: agentData, isLoading } = useAgentConfigs()
  const deleteAgent = useDeleteAgentConfig()
  const deployAgent = useDeployAgentConfig()
  const [selectedScenario, setSelectedScenario] = useState<string>('all')

  const agentConfigs = agentData?.configs || []
  
  const filteredConfigs = selectedScenario === 'all' 
    ? agentConfigs 
    : agentConfigs.filter(config => config.scenario_type === selectedScenario)

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this agent configuration?')) {
      await deleteAgent.mutateAsync(id)
    }
  }

  const handleDeploy = async (id: number, shouldDeploy: boolean) => {
    await deployAgent.mutateAsync({ id, deploy: shouldDeploy })
  }

  const getStatusBadge = (config: { is_deployed: boolean; is_active: boolean }) => {
    if (config.is_deployed && config.is_active) {
      return <Badge className="bg-green-100 text-green-800">Active</Badge>
    } else if (config.is_active) {
      return <Badge className="bg-yellow-100 text-yellow-800">Ready</Badge>
    } else {
      return <Badge className="bg-gray-100 text-gray-800">Draft</Badge>
    }
  }

  const getScenarioIcon = (scenarioType: string) => {
    switch (scenarioType) {
      case 'check_in':
        return <CheckCircle className="h-4 w-4 text-blue-500" />
      case 'emergency':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      default:
        return <Settings className="h-4 w-4 text-gray-500" />
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Agent Configuration</h1>
            <p className="text-gray-600">Configure AI voice agents for different logistics scenarios</p>
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
          <h1 className="text-2xl font-bold text-gray-900">Agent Configuration</h1>
          <p className="text-gray-600">Configure AI voice agents for different logistics scenarios</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/agents/new">
            <Plus className="h-4 w-4 mr-2" />
            New Configuration
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex space-x-4">
            <Button
              variant={selectedScenario === 'all' ? 'default' : 'outline'}
              onClick={() => setSelectedScenario('all')}
              size="sm"
            >
              All Scenarios
            </Button>
            <Button
              variant={selectedScenario === 'check_in' ? 'default' : 'outline'}
              onClick={() => setSelectedScenario('check_in')}
              size="sm"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Driver Check-in
            </Button>
            <Button
              variant={selectedScenario === 'emergency' ? 'default' : 'outline'}
              onClick={() => setSelectedScenario('emergency')}
              size="sm"
            >
              <AlertTriangle className="h-4 w-4 mr-2" />
              Emergency Protocol
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Agent Configurations Grid */}
      {filteredConfigs.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Agent Configurations</h3>
              <p className="text-gray-600 mb-4">
                Get started by creating your first agent configuration for logistics scenarios.
              </p>
              <Button asChild>
                <Link href="/dashboard/agents/new">
                  <Plus className="h-4 w-4 mr-2" />
                  Create First Configuration
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredConfigs.map((config) => (
            <Card key={config.id} className="relative">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getScenarioIcon(config.scenario_type)}
                    <CardTitle className="text-lg">{config.name}</CardTitle>
                  </div>
                  {getStatusBadge(config)}
                </div>
                <CardDescription className="capitalize">
                  {config.scenario_type.replace('_', ' ')} Scenario
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {/* Configuration Details */}
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Voice Speed:</span>
                    <span>{config.voice_settings?.voice_speed || 1}x</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Backchanneling:</span>
                    <span>{config.voice_settings?.backchanneling ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Created:</span>
                    <span>{formatDistanceToNow(new Date(config.created_at))} ago</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-4 border-t">
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      asChild
                    >
                      <Link href={`/dashboard/agents/${config.id}`}>
                        <Eye className="h-4 w-4" />
                      </Link>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      asChild
                    >
                      <Link href={`/dashboard/agents/${config.id}/edit`}>
                        <Edit className="h-4 w-4" />
                      </Link>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(config.id)}
                      disabled={deleteAgent.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <Button
                    variant={config.is_deployed ? "secondary" : "default"}
                    size="sm"
                    onClick={() => handleDeploy(config.id, !config.is_deployed)}
                    disabled={deployAgent.isPending}
                  >
                    {config.is_deployed ? (
                      <>
                        <Pause className="h-4 w-4 mr-1" />
                        Pause
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-1" />
                        Deploy
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Quick Start Templates */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Start Templates</CardTitle>
          <CardDescription>
            Pre-configured templates for common logistics scenarios
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div className="flex items-center space-x-3 mb-2">
                <CheckCircle className="h-5 w-5 text-blue-500" />
                <h3 className="font-medium">Driver Check-in Template</h3>
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Pre-configured for end-to-end driver status updates with dynamic conversation flow.
              </p>
              <Button variant="outline" size="sm" asChild>
                <Link href="/dashboard/agents/new?template=check_in">
                  Use Template
                </Link>
              </Button>
            </div>
            
            <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div className="flex items-center space-x-3 mb-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <h3 className="font-medium">Emergency Protocol Template</h3>
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Pre-configured for immediate emergency response with safety prioritization.
              </p>
              <Button variant="outline" size="sm" asChild>
                <Link href="/dashboard/agents/new?template=emergency">
                  Use Template
                </Link>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
