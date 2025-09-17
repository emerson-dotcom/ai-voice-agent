'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useInitiateCall } from '@/hooks/use-calls'
import { useAgentConfigs } from '@/hooks/use-agents'
import { 
  Phone, 
  ArrowLeft, 
  User,
  Truck,
  Settings,
  Play,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'
import type { AgentConfiguration, Call } from '@/types'

// Validation schema for new call
const newCallSchema = z.object({
  driver_name: z.string().min(1, 'Driver name is required').max(100),
  phone_number: z.string().optional(),
  load_number: z.string().min(1, 'Load number is required').max(50),
  agent_config_id: z.number().min(1, 'Please select an agent configuration'),
  call_type: z.enum(['phone_call', 'web_call']),
  notes: z.string().optional(),
}).refine((data) => {
  // Phone number is required for phone calls
  if (data.call_type === 'phone_call') {
    return data.phone_number && data.phone_number.length >= 10
  }
  return true
}, {
  message: "Phone number is required for phone calls and must be at least 10 digits",
  path: ["phone_number"]
}).refine((data) => {
  // Validate phone number format if provided
  if (data.phone_number && data.phone_number.length > 0) {
    const phoneRegex = /^\+?[\d\s\-\(\)]+$/
    return phoneRegex.test(data.phone_number)
  }
  return true
}, {
  message: "Invalid phone number format",
  path: ["phone_number"]
})

type NewCallFormData = z.infer<typeof newCallSchema>

export default function NewCallPage() {
  const router = useRouter()
  const initiateCall = useInitiateCall()
  const { data: agentData, isLoading: loadingAgents } = useAgentConfigs({ is_active: true })
  
  const [selectedAgent, setSelectedAgent] = useState<AgentConfiguration | null>(null)
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const [callType, setCallType] = useState<'phone_call' | 'web_call'>('phone_call')

  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<NewCallFormData>({
    resolver: zodResolver(newCallSchema),
    defaultValues: {
      driver_name: '',
      phone_number: '',
      load_number: '',
      agent_config_id: 0,
      call_type: 'phone_call',
      notes: '',
    },
  })

  const agentConfigs = useMemo(() => agentData?.configs || [], [agentData?.configs])
  const watchedAgentId = watch('agent_config_id')

  // Update selected agent when agent_config_id changes
  useEffect(() => {
    const agent = agentConfigs.find(a => a.id === watchedAgentId)
    setSelectedAgent(agent || null)
  }, [watchedAgentId, agentConfigs])

  const onSubmit = async (data: NewCallFormData) => {
    try {
      const result = await initiateCall.mutateAsync({
        driver_name: data.driver_name,
        phone_number: data.phone_number,
        load_number: data.load_number,
        agent_config_id: data.agent_config_id,
        call_type: data.call_type,
      }) as Call
      
      toast.success(`${data.call_type === 'web_call' ? 'Web call' : 'Call'} initiated successfully for ${data.driver_name}`)
      
      // If it's a web call, automatically open the webcall URL
      if (data.call_type === 'web_call' && result.conversation_metadata?.web_call_url) {
        // Extract the token from the web_call_url
        const webCallUrl = result.conversation_metadata.web_call_url
        const tokenMatch = webCallUrl.match(/\/webcall\/([^\/]+)/)
        
        if (tokenMatch && tokenMatch[1]) {
          const token = tokenMatch[1]
          // Open the webcall in a new tab
          window.open(`/webcall/${token}`, '_blank')
          toast.success('Web call opened in new tab!')
        } else {
          // Fallback: open the full URL
          window.open(webCallUrl, '_blank')
          toast.success('Web call opened in new tab!')
        }
      }
      
      // Navigate to call details page
      router.push(`/dashboard/calls/${result.id}`)
    } catch (error) {
      toast.error('Failed to initiate call')
      console.error('Error initiating call:', error)
    }
  }

  const handlePreview = () => {
    if (selectedAgent) {
      setIsPreviewMode(!isPreviewMode)
    }
  }

  const formatPhoneNumber = (value: string) => {
    // Remove all non-digits
    const digits = value.replace(/\D/g, '')
    
    // Format as (XXX) XXX-XXXX
    if (digits.length >= 6) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`
    } else if (digits.length >= 3) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
    }
    return digits
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/dashboard/calls">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back
                </Button>
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Initiate New Call</h1>
                <p className="text-gray-600">Start a new voice call with AI agent assistance</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              {selectedAgent && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={handlePreview}
                  className="flex items-center"
                >
                  <Settings className="h-4 w-4 mr-2" />
                  {isPreviewMode ? 'Hide Preview' : 'Preview Agent'}
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Driver Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <User className="h-5 w-5 mr-2" />
                    Driver Information
                  </CardTitle>
                  <CardDescription>
                    Enter the driver&apos;s contact details and load information
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium mb-2">Driver Name *</label>
                      <Input
                        {...register('driver_name')}
                        placeholder="Enter driver's full name"
                        className={errors.driver_name ? 'border-red-500' : ''}
                      />
                      {errors.driver_name && (
                        <p className="text-sm text-red-600 mt-1">{errors.driver_name.message}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Phone Number {watch('call_type') === 'phone_call' ? '*' : '(Optional for web calls)'}
                      </label>
                      <Controller
                        name="phone_number"
                        control={control}
                        render={({ field }) => (
                          <Input
                            {...field}
                            placeholder="(555) 123-4567"
                            onChange={(e) => {
                              const formatted = formatPhoneNumber(e.target.value)
                              field.onChange(formatted)
                            }}
                            className={errors.phone_number ? 'border-red-500' : ''}
                            disabled={watch('call_type') === 'web_call'}
                          />
                        )}
                      />
                      {errors.phone_number && (
                        <p className="text-sm text-red-600 mt-1">{errors.phone_number.message}</p>
                      )}
                      {watch('call_type') === 'web_call' && (
                        <p className="text-sm text-gray-500 mt-1">
                          Phone number is optional for web calls - a web link will be generated instead
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Call Type Selection */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Call Type *</label>
                    <Controller
                      name="call_type"
                      control={control}
                      render={({ field }) => (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div
                            className={`p-4 border rounded-lg cursor-pointer transition-all ${
                              field.value === 'phone_call'
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                            onClick={() => field.onChange('phone_call')}
                          >
                            <div className="flex items-center space-x-3">
                              <input
                                type="radio"
                                checked={field.value === 'phone_call'}
                                onChange={() => field.onChange('phone_call')}
                                className="text-blue-600"
                              />
                              <div>
                                <h4 className="font-medium text-gray-900">Phone Call</h4>
                                <p className="text-sm text-gray-600">Call the driver directly via phone</p>
                              </div>
                            </div>
                          </div>
                          <div
                            className={`p-4 border rounded-lg cursor-pointer transition-all ${
                              field.value === 'web_call'
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                            onClick={() => field.onChange('web_call')}
                          >
                            <div className="flex items-center space-x-3">
                              <input
                                type="radio"
                                checked={field.value === 'web_call'}
                                onChange={() => field.onChange('web_call')}
                                className="text-blue-600"
                              />
                              <div>
                                <h4 className="font-medium text-gray-900">Web Call</h4>
                                <p className="text-sm text-gray-600">Generate a web call link for the driver</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    />
                    {errors.call_type && (
                      <p className="text-sm text-red-600 mt-1">{errors.call_type.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Load Number *</label>
                    <div className="relative">
                      <Truck className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        {...register('load_number')}
                        placeholder="Enter load/shipment number"
                        className={`pl-10 ${errors.load_number ? 'border-red-500' : ''}`}
                      />
                    </div>
                    {errors.load_number && (
                      <p className="text-sm text-red-600 mt-1">{errors.load_number.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Additional Notes</label>
                    <textarea
                      {...register('notes')}
                      placeholder="Any special instructions or notes for this call..."
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Agent Configuration Selection */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Settings className="h-5 w-5 mr-2" />
                    Agent Configuration
                  </CardTitle>
                  <CardDescription>
                    Select the AI agent configuration for this call
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loadingAgents ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="mt-2 text-sm text-gray-600">Loading configurations...</p>
                    </div>
                  ) : agentConfigs.length === 0 ? (
                    <div className="text-center py-8">
                      <AlertCircle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                      <p className="text-sm text-gray-600 mb-4">No active agent configurations found</p>
                      <Link href="/dashboard/agents/new">
                        <Button size="sm">Create Configuration</Button>
                      </Link>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <Controller
                        name="agent_config_id"
                        control={control}
                        render={({ field }) => (
                          <div className="space-y-2">
                            {agentConfigs.map((config) => (
                              <div
                                key={config.id}
                                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                                  field.value === config.id
                                    ? 'border-blue-500 bg-blue-50'
                                    : 'border-gray-200 hover:border-gray-300'
                                }`}
                                onClick={() => field.onChange(config.id)}
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center space-x-3">
                                    <input
                                      type="radio"
                                      checked={field.value === config.id}
                                      onChange={() => field.onChange(config.id)}
                                      className="text-blue-600"
                                    />
                                    <div>
                                      <h4 className="font-medium text-gray-900">{config.name}</h4>
                                      <p className="text-sm text-gray-600">{config.description}</p>
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <Badge 
                                      variant={config.scenario_type === 'check_in' ? 'default' : 'secondary'}
                                    >
                                      {config.scenario_type === 'check_in' ? 'Check-in' : 'Emergency'}
                                    </Badge>
                                    {config.is_deployed && (
                                      <Badge variant="outline" className="text-green-600 border-green-300">
                                        <CheckCircle className="h-3 w-3 mr-1" />
                                        Deployed
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      />
                      {errors.agent_config_id && (
                        <p className="text-sm text-red-600">{errors.agent_config_id.message}</p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Submit Button */}
              <div className="flex justify-end space-x-3">
                <Link href="/dashboard/calls">
                  <Button variant="outline">Cancel</Button>
                </Link>
                <Button
                  type="submit"
                  disabled={initiateCall.isPending || !selectedAgent}
                  className="flex items-center"
                >
                  <Phone className="h-4 w-4 mr-2" />
                  {initiateCall.isPending ? 'Initiating...' : 'Start Call'}
                </Button>
              </div>
            </form>
          </div>

          {/* Agent Preview Sidebar */}
          <div className="lg:col-span-1">
            {selectedAgent && (
              <div className="sticky top-8">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Play className="h-5 w-5 mr-2" />
                      Selected Agent
                    </CardTitle>
                    <CardDescription>
                      {selectedAgent.name}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">Configuration Details</h4>
                      <div className="text-sm space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Scenario:</span>
                          <Badge variant={selectedAgent.scenario_type === 'check_in' ? 'default' : 'secondary'}>
                            {selectedAgent.scenario_type === 'check_in' ? 'Check-in' : 'Emergency'}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Status:</span>
                          <span className={selectedAgent.is_active ? 'text-green-600' : 'text-gray-500'}>
                            {selectedAgent.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Version:</span>
                          <span>v{selectedAgent.version}</span>
                        </div>
                      </div>
                    </div>

                    {isPreviewMode && (
                      <div className="space-y-4 pt-4 border-t">
                        <div>
                          <h4 className="font-medium mb-2">Voice Settings</h4>
                          <div className="text-sm space-y-1">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Speed:</span>
                              <span>{selectedAgent.voice_settings.voice_speed}x</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Backchanneling:</span>
                              <span>{selectedAgent.voice_settings.backchanneling ? 'On' : 'Off'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Interruption:</span>
                              <span>{Math.round(selectedAgent.voice_settings.interruption_sensitivity * 100)}%</span>
                            </div>
                          </div>
                        </div>

                        <div>
                          <h4 className="font-medium mb-2">Opening Prompt</h4>
                          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                            {selectedAgent.prompts.opening}
                          </p>
                        </div>

                        <div>
                          <h4 className="font-medium mb-2">Flow Settings</h4>
                          <div className="text-sm space-y-1">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Max Turns:</span>
                              <span>{selectedAgent.conversation_flow.max_turns}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Timeout:</span>
                              <span>{selectedAgent.conversation_flow.timeout_seconds}s</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="pt-4 border-t">
                      <div className="flex items-center text-sm text-gray-600">
                        <Clock className="h-4 w-4 mr-2" />
                        Updated {new Date(selectedAgent.updated_at).toLocaleDateString()}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
