'use client'

import { useState, useEffect } from 'react'
import AgentForm from '@/components/agent-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Settings, Plus, Edit, Trash2, User, AlertCircle, Loader2 } from 'lucide-react'
import { Agent } from '@/types'
import { AuthGuard } from '@/components/AuthGuard'
import { Header } from '@/components/Header'
import { agentApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function AgentsPage() {
  const { toast } = useToast()
  const [agents, setAgents] = useState<Agent[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [formLoading, setFormLoading] = useState(false)
  const [deletingAgentId, setDeletingAgentId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const extractErrorMessage = (error: any): { title: string; description: string } => {
    let title = "Error"
    let description = "An unexpected error occurred"

    if (error?.message) {
      // Check if it's an API error with status code
      if (error.message.includes('API Error')) {
        const match = error.message.match(/API Error (\d+): (.+)/)
        if (match) {
          const [, , errorBody] = match
          try {
            const parsed = JSON.parse(errorBody)
            description = parsed.detail || errorBody
          } catch {
            description = errorBody
          }
        } else {
          description = error.message.replace('API Error', '').replace(/^\d+:\s*/, '')
        }
      } else {
        description = error.message
      }
    }

    return { title, description }
  }

  useEffect(() => {
    console.log('Agents page mounted, checking auth state...')

    // Debug: Check auth state
    const checkAuth = async () => {
      const { supabase } = await import('@/lib/supabase')
      const { data: { session }, error } = await supabase.auth.getSession()
      console.log('Auth check - Session:', !!session, 'Error:', error)
      console.log('Session details:', session ? {
        user: !!session.user,
        access_token: !!session.access_token,
        expires_at: session.expires_at
      } : 'No session')
    }

    checkAuth().then(() => {
      console.log('Starting fetchAgents...')
      fetchAgents()
    })
  }, [])

  const fetchAgents = async () => {
    try {
      console.log('fetchAgents - Starting API call to:', 'agents list endpoint')
      const data = await agentApi.list()
      console.log('fetchAgents - Success, got agents:', data?.length || 0)
      setAgents(data)
    } catch (error) {
      console.error('fetchAgents - Error:', error)
      console.error('Error details:', {
        message: error.message,
        stack: error.stack
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAgent = () => {
    setEditingAgent(null)
    setShowForm(true)
  }

  const handleEditAgent = (agent: Agent) => {
    setEditingAgent(agent)
    setShowForm(true)
  }

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return

    setDeletingAgentId(agentId)
    try {
      await agentApi.delete(agentId)
      await fetchAgents()

      toast({
        title: "Success",
        description: "Agent deleted successfully",
        variant: "success"
      })
    } catch (error: any) {
      console.error('Error deleting agent:', error)

      const { title, description } = extractErrorMessage(error)
      toast({
        title,
        description,
        variant: "destructive"
      })
    } finally {
      setDeletingAgentId(null)
    }
  }

  const handleFormSubmit = async (data: any) => {
    setFormLoading(true)
    setError(null)
    try {
      if (editingAgent) {
        // Update existing agent
        await agentApi.update(editingAgent.id, data)
        toast({
          title: "Success",
          description: "Agent updated successfully",
          variant: "success"
        })
      } else {
        // Create new agent
        await agentApi.create(data)
        toast({
          title: "Success",
          description: "Agent created successfully",
          variant: "success"
        })
      }
      handleFormSuccess()
    } catch (error: any) {
      console.error('Error saving agent:', error)

      const { title, description } = extractErrorMessage(error)
      toast({
        title,
        description,
        variant: "destructive"
      })
      setError(description)
    } finally {
      setFormLoading(false)
    }
  }

  const handleFormSuccess = () => {
    setShowForm(false)
    setEditingAgent(null)
    setError(null)
    fetchAgents()
  }

  const getScenarioColor = (scenarioType: string) => {
    switch (scenarioType) {
      case 'driver_checkin':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'emergency_protocol':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getStatusColor = (isActive: boolean) => {
    return isActive
      ? 'bg-green-100 text-green-800 border-green-200'
      : 'bg-gray-100 text-gray-800 border-gray-200'
  }

  if (showForm) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-6">
            <Button
              variant="outline"
              onClick={() => setShowForm(false)}
              className="mb-4 shadow-sm hover:shadow-md"
            >
              ← Back to Agents
            </Button>
            <h1 className="text-4xl font-bold text-slate-900">
              {editingAgent ? 'Edit Agent' : 'Create New Agent'}
            </h1>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <AgentForm
            initialData={editingAgent ? {
              name: editingAgent.name,
              description: editingAgent.description,
              general_prompt: editingAgent.general_prompt,
              begin_message: editingAgent.begin_message,
              voice_id: editingAgent.voice_id,
              voice_model: editingAgent.voice_model,
              voice_temperature: editingAgent.voice_temperature,
              voice_speed: editingAgent.voice_speed,
              enable_backchannel: editingAgent.enable_backchannel,
              backchannel_frequency: editingAgent.backchannel_frequency,
              backchannel_words: editingAgent.backchannel_words,
              interruption_sensitivity: editingAgent.interruption_sensitivity,
              responsiveness: editingAgent.responsiveness,
              scenario_type: editingAgent.scenario_type as 'driver_checkin' | 'emergency_protocol'
            } : undefined}
            onSubmit={handleFormSubmit}
            isLoading={formLoading}
          />
        </div>
      </div>
    )
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
              Voice Agents
            </h1>
            <p className="text-xl text-slate-600">
              Configure and manage AI voice agents for logistics operations
            </p>
          </div>
          <Button onClick={handleCreateAgent} size="lg" className="shadow-lg hover:shadow-xl">
            <Plus className="h-5 w-5 mr-2" />
            Create Agent
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">Loading agents...</p>
          </div>
        ) : agents.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-semibold mb-2">No Agents Found</h3>
              <p className="text-muted-foreground mb-4">
                Create your first voice agent to get started
              </p>
              <Button onClick={handleCreateAgent} size="lg" className="shadow-lg hover:shadow-xl">
                <Plus className="h-4 w-4 mr-2" />
                Create First Agent
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent) => (
              <Card key={agent.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{agent.name}</CardTitle>
                      <CardDescription className="mt-1">
                        {agent.description}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="icon-sm"
                        onClick={() => handleEditAgent(agent)}
                        className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 border-blue-200 hover:border-blue-300"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="icon-sm"
                        onClick={() => handleDeleteAgent(agent.id)}
                        disabled={deletingAgentId === agent.id}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200 hover:border-red-300"
                      >
                        {deletingAgentId === agent.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* Status Badges */}
                    <div className="flex gap-2">
                      <Badge
                        className={getStatusColor(agent.is_active)}
                        variant="secondary"
                      >
                        {agent.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                      <Badge
                        className={getScenarioColor(agent.scenario_type)}
                        variant="secondary"
                      >
                        {agent.scenario_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Badge>
                    </div>

                    {/* Integration Status */}
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Retell LLM:</span>
                        <span className={agent.retell_llm_id ? 'text-green-600' : 'text-gray-500'}>
                          {agent.retell_llm_id ? 'Connected' : 'Not Created'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Retell Agent:</span>
                        <span className={agent.retell_agent_id ? 'text-green-600' : 'text-gray-500'}>
                          {agent.retell_agent_id ? 'Connected' : 'Not Created'}
                        </span>
                      </div>
                    </div>

                    {/* Created Date */}
                    <div className="text-xs text-muted-foreground pt-2 border-t">
                      Created: {new Date(agent.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Quick Setup Guide */}
        {agents.length > 0 && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Quick Setup Guide
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Driver Check-in Agents</h4>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• Handle routine driver status calls</li>
                    <li>• Extract location, ETA, and delay information</li>
                    <li>• Natural conversation flow with backchannel responses</li>
                    <li>• Automatic emergency detection and escalation</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Emergency Protocol Agents</h4>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• Specialized for emergency detection</li>
                    <li>• Immediate escalation to human dispatchers</li>
                    <li>• Critical information gathering</li>
                    <li>• High responsiveness and interruption sensitivity</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
    </AuthGuard>
  )
}