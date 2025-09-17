'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useAgentConfig, useDeleteAgentConfig, useDeployAgentConfig, useTestAgentConfig } from '@/hooks/use-agents'
import type { AgentConfiguration } from '@/types'
import { formatDistanceToNow, format } from 'date-fns'
import { 
  ArrowLeft,
  Edit,
  Trash2,
  Play,
  Pause,
  TestTube,
  Copy,
  Settings,
  MessageSquare,
  Mic,
  CheckCircle,
  AlertTriangle,
  Clock,
  Activity
} from 'lucide-react'
import toast from 'react-hot-toast'

export default function AgentConfigDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string
  
  const { data: config, isLoading } = useAgentConfig(parseInt(id)) as { data: AgentConfiguration | undefined, isLoading: boolean }
  const deleteAgent = useDeleteAgentConfig()
  const deployAgent = useDeployAgentConfig()
  const testAgent = useTestAgentConfig()
  
  const [showPrompts, setShowPrompts] = useState(true)
  const [showVoiceSettings, setShowVoiceSettings] = useState(true)

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this agent configuration? This action cannot be undone.')) {
      try {
        await deleteAgent.mutateAsync(parseInt(id))
        toast.success('Agent configuration deleted successfully')
        router.push('/dashboard/agents')
      } catch {
        toast.error('Failed to delete agent configuration')
      }
    }
  }

  const handleDeploy = async (shouldDeploy: boolean) => {
    try {
      await deployAgent.mutateAsync({ id: parseInt(id), deploy: shouldDeploy })
      toast.success(`Agent ${shouldDeploy ? 'deployed' : 'paused'} successfully`)
    } catch {
      toast.error(`Failed to ${shouldDeploy ? 'deploy' : 'pause'} agent`)
    }
  }

  const handleTest = async () => {
    try {
      // Use a default test phone number for testing
      const testPhone = '+15551234567'
      await testAgent.mutateAsync({ id: parseInt(id), testPhone })
      toast.success('Test call initiated successfully')
    } catch {
      toast.error('Failed to initiate test call')
    }
  }

  const handleDuplicate = () => {
    router.push(`/dashboard/agents/new?duplicate=${id}`)
  }

  const getStatusBadge = () => {
    if (!config) return null
    
    if (config.is_deployed && config.is_active) {
      return <Badge className="bg-green-100 text-green-800"><Activity className="h-3 w-3 mr-1" />Active</Badge>
    } else if (config.is_active) {
      return <Badge className="bg-yellow-100 text-yellow-800"><Clock className="h-3 w-3 mr-1" />Ready</Badge>
    } else {
      return <Badge className="bg-gray-100 text-gray-800">Draft</Badge>
    }
  }

  const getScenarioInfo = () => {
    if (!config) return null
    
    switch (config.scenario_type) {
      case 'check_in':
        return {
          icon: <CheckCircle className="h-5 w-5 text-blue-500" />,
          title: 'Driver Check-in Scenario',
          description: 'Handles driver status updates with dynamic conversation flow'
        }
      case 'emergency':
        return {
          icon: <AlertTriangle className="h-5 w-5 text-red-500" />,
          title: 'Emergency Protocol Scenario',
          description: 'Immediate emergency response with safety prioritization'
        }
      default:
        return {
          icon: <Settings className="h-5 w-5 text-gray-500" />,
          title: 'Custom Scenario',
          description: 'Custom conversation flow configuration'
        }
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (!config) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Configuration Not Found</h3>
          <p className="text-gray-600 mb-4">The requested agent configuration could not be found.</p>
          <Button asChild>
            <Link href="/dashboard/agents">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Configurations
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  const scenarioInfo = getScenarioInfo()

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/dashboard/agents">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Configurations
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{config.name}</h1>
            <p className="text-gray-600">Agent configuration details</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusBadge()}
        </div>
      </div>

      {/* Overview Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {scenarioInfo?.icon}
              <div>
                <CardTitle>{scenarioInfo?.title}</CardTitle>
                <CardDescription>{scenarioInfo?.description}</CardDescription>
              </div>
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm" onClick={handleTest} disabled={testAgent.isPending}>
                <TestTube className="h-4 w-4 mr-1" />
                Test
              </Button>
              <Button variant="outline" size="sm" onClick={handleDuplicate}>
                <Copy className="h-4 w-4 mr-1" />
                Duplicate
              </Button>
              <Button variant="outline" size="sm" asChild>
                <Link href={`/dashboard/agents/${id}/edit`}>
                  <Edit className="h-4 w-4 mr-1" />
                  Edit
                </Link>
              </Button>
              <Button
                variant={config.is_deployed ? "secondary" : "default"}
                size="sm"
                onClick={() => handleDeploy(!config.is_deployed)}
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
              <Button variant="outline" size="sm" onClick={handleDelete} disabled={deleteAgent.isPending}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Created</h4>
              <p className="text-sm text-gray-600">{format(new Date(config.created_at), 'MMM d, yyyy HH:mm')}</p>
              <p className="text-xs text-gray-500">{formatDistanceToNow(new Date(config.created_at))} ago</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Last Updated</h4>
              <p className="text-sm text-gray-600">{format(new Date(config.updated_at), 'MMM d, yyyy HH:mm')}</p>
              <p className="text-xs text-gray-500">{formatDistanceToNow(new Date(config.updated_at))} ago</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Status</h4>
              <div className="flex items-center space-x-2">
                {config.is_active ? (
                  <span className="text-sm text-green-600">Active</span>
                ) : (
                  <span className="text-sm text-gray-600">Inactive</span>
                )}
                {config.is_deployed && (
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Deployed</span>
                )}
              </div>
            </div>
          </div>
          
          {config.description && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-700 mb-2">Description</h4>
              <p className="text-sm text-gray-600">{config.description}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Conversation Prompts */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <CardTitle>Conversation Prompts</CardTitle>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setShowPrompts(!showPrompts)}
            >
              {showPrompts ? 'Hide' : 'Show'}
            </Button>
          </div>
        </CardHeader>
        {showPrompts && (
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Opening Prompt</h4>
              <div className="p-3 bg-gray-50 rounded border text-sm">
                {config.prompts?.opening || 'Not configured'}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Follow-up Prompt</h4>
              <div className="p-3 bg-gray-50 rounded border text-sm">
                {config.prompts?.follow_up || 'Not configured'}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Closing Prompt</h4>
              <div className="p-3 bg-gray-50 rounded border text-sm">
                {config.prompts?.closing || 'Not configured'}
              </div>
            </div>
            
            {config.prompts?.emergency_trigger && (
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Emergency Trigger Response</h4>
                <div className="p-3 bg-red-50 border border-red-200 rounded text-sm">
                  {config.prompts.emergency_trigger}
                </div>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Voice Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Mic className="h-5 w-5" />
              <CardTitle>Voice Settings</CardTitle>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setShowVoiceSettings(!showVoiceSettings)}
            >
              {showVoiceSettings ? 'Hide' : 'Show'}
            </Button>
          </div>
        </CardHeader>
        {showVoiceSettings && (
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Speech Speed</h4>
                <div className="flex items-center space-x-3">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full" 
                      style={{ width: `${((config.voice_settings?.voice_speed || 1) - 0.5) / 1.5 * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-mono">{config.voice_settings?.voice_speed || 1}x</span>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Interruption Sensitivity</h4>
                <div className="flex items-center space-x-3">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full" 
                      style={{ width: `${(config.voice_settings?.interruption_sensitivity || 0.7) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-mono">
                    {Math.round((config.voice_settings?.interruption_sensitivity || 0.7) * 100)}%
                  </span>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Backchanneling</h4>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${config.voice_settings?.backchanneling ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  <span className="text-sm">{config.voice_settings?.backchanneling ? 'Enabled' : 'Disabled'}</span>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Filler Words</h4>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${config.voice_settings?.filler_words ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  <span className="text-sm">{config.voice_settings?.filler_words ? 'Enabled' : 'Disabled'}</span>
                </div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Data Extraction Points */}
      {config.conversation_flow?.data_extraction_points && config.conversation_flow.data_extraction_points.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Data Extraction Points</CardTitle>
            <CardDescription>
              Fields that will be extracted from conversations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {config.conversation_flow.data_extraction_points.map((point, index) => (
                <Badge key={index} variant="outline" className="capitalize">
                  {point.replace(/_/g, ' ')}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Usage Statistics section removed - not implemented in backend */}
    </div>
  )
}
