'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CallFormData, Agent, Load } from '@/types'
import { Phone, User, Truck, AlertCircle } from 'lucide-react'
import { useWebCall } from '@/hooks/useWebCall'
import { useToast } from '@/hooks/use-toast'

interface CallFormProps {
  agents: Agent[]
  loads: Load[]
  isLoading?: boolean
}

export default function CallForm({ agents, loads, isLoading = false }: CallFormProps) {
  const router = useRouter()
  const { toast } = useToast()
  const { callState, createCall, clearError } = useWebCall()

  const [formData, setFormData] = useState<CallFormData>({
    agent_id: '',
    driver_name: '',
    load_number: ''
  })

  const [selectedLoad, setSelectedLoad] = useState<Load | null>(null)
  const [errors, setErrors] = useState<Partial<CallFormData>>({})

  const updateField = (field: keyof CallFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const handleLoadSelect = (loadNumber: string) => {
    const load = loads.find(l => l.load_number === loadNumber)
    if (load) {
      setSelectedLoad(load)
      setFormData(prev => ({
        ...prev,
        load_number: loadNumber,
        driver_name: load.assigned_driver_name || ''
      }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Partial<CallFormData> = {}

    if (!formData.agent_id) newErrors.agent_id = 'Please select an agent'
    if (!formData.driver_name.trim()) newErrors.driver_name = 'Driver name is required'
    if (!formData.load_number.trim()) newErrors.load_number = 'Load number is required'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    console.log('CallForm: Submit button clicked')
    console.log('CallForm: Form data:', formData)

    if (!validateForm()) {
      console.log('CallForm: Form validation failed')
      return
    }

    // Clear any previous errors
    if (callState.error) {
      clearError()
    }

    // Prepare call config for backend
    const callConfig = {
      agent_id: formData.agent_id,
      metadata: {
        driver_name: formData.driver_name,
        load_number: formData.load_number
      },
      dynamic_variables: {
        driver_name: formData.driver_name || 'Driver',
        load_number: formData.load_number || 'N/A'
      }
    }

    try {
      console.log('CallForm: Creating web call with config:', callConfig)
      const response = await createCall(callConfig)

      if (response && response.call_id) {
        console.log('CallForm: Call created successfully, redirecting to attend page')
        toast({
          title: 'Call Created',
          description: 'Redirecting to attend call...',
          variant: 'default'
        })

        // Redirect to attend call page
        router.push(`/call/${response.call_id}`)
      } else {
        throw new Error('No call ID received from backend')
      }
    } catch (error) {
      console.error('CallForm: Error creating call:', error)
      toast({
        title: 'Call Creation Failed',
        description: error instanceof Error ? error.message : 'Failed to create call',
        variant: 'destructive'
      })
    }
  }

  const selectedAgent = agents.find(a => a.id === formData.agent_id)

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Agent Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Select Agent
          </CardTitle>
          <CardDescription>
            Choose which voice agent will make the call
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="agent_id">Voice Agent *</Label>
            <Select value={formData.agent_id} onValueChange={(value) => updateField('agent_id', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select an agent" />
              </SelectTrigger>
              <SelectContent>
                {agents
                  .filter(agent => agent.is_active)
                  .map((agent) => (
                    <SelectItem key={agent.id} value={agent.id}>
                      <div className="flex flex-col">
                        <span>{agent.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {agent.scenario_type === 'driver_checkin' ? 'Driver Check-in' : 'Emergency Protocol'}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            {errors.agent_id && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {errors.agent_id}
              </p>
            )}
          </div>

          {selectedAgent && (
            <div className="mt-4 p-3 bg-muted rounded-lg">
              <h4 className="text-sm font-medium mb-1">{selectedAgent.name}</h4>
              <p className="text-xs text-muted-foreground">{selectedAgent.description}</p>
              <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                <span>Voice: {selectedAgent.voice_id}</span>
                <span>Type: {selectedAgent.scenario_type === 'driver_checkin' ? 'Driver Check-in' : 'Emergency Protocol'}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Load Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Truck className="h-5 w-5" />
            Load Information
          </CardTitle>
          <CardDescription>
            Enter the load number for this call
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="load_number">Load Number *</Label>
            <Input
              id="load_number"
              value={formData.load_number}
              onChange={(e) => updateField('load_number', e.target.value)}
              placeholder="e.g., 7891-B"
              required
            />
            {errors.load_number && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {errors.load_number}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Driver Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Driver Information
          </CardTitle>
          <CardDescription>
            Enter the driver's name for this call
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="driver_name">Driver Name *</Label>
            <Input
              id="driver_name"
              value={formData.driver_name}
              onChange={(e) => updateField('driver_name', e.target.value)}
              placeholder="e.g., Mike Johnson"
              required
            />
            {errors.driver_name && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {errors.driver_name}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Submit Section */}
      <Card>
        <CardContent className="pt-6">
          {/* Call Error Display */}
          {callState.error && (
            <div className="mb-4">
              <div className="text-sm text-destructive flex items-center gap-1 p-3 bg-destructive/10 rounded-lg">
                <AlertCircle className="h-4 w-4" />
                <span>{callState.error}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearError}
                  className="ml-auto h-6 px-2"
                >
                  ×
                </Button>
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h3 className="font-medium">Ready to Start Web Call</h3>
              <p className="text-sm text-muted-foreground">
                The agent will simulate a call with {formData.driver_name || 'the driver'} about load {formData.load_number || '[Load Number]'}
              </p>
            </div>

            <Button
              type="submit"
              disabled={callState.isCreating || !formData.agent_id || !formData.driver_name || !formData.load_number}
              className="min-w-[140px]"
              size="lg"
            >
              {callState.isCreating ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
                  Starting Call...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Start Web Call
                </div>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </form>
  )
}