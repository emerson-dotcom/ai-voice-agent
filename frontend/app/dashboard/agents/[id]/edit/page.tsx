'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { useAgentConfig, useUpdateAgentConfig } from '@/hooks/use-agents'
import type { AgentConfiguration } from '@/types'
import { 
  Save, 
  ArrowLeft, 
  CheckCircle, 
  AlertTriangle, 
  Settings,
  Mic,
  MessageSquare,
  TestTube,
  Play
} from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'

// Validation schema (same as new agent)
const agentConfigSchema = z.object({
  name: z.string().min(1, 'Configuration name is required'),
  scenario_type: z.enum(['check_in', 'emergency'], {
    required_error: 'Please select a scenario type'
  }),
  description: z.string().optional(),
  prompts: z.object({
    opening: z.string().min(10, 'Opening prompt must be at least 10 characters'),
    follow_up: z.string().min(10, 'Follow-up prompt must be at least 10 characters'),
    closing: z.string().min(10, 'Closing prompt must be at least 10 characters'),
    emergency_trigger: z.string().optional(),
    probing_questions: z.array(z.string()).optional(),
  }),
  voice_settings: z.object({
    voice_speed: z.number().min(0.5).max(2.0),
    voice_temperature: z.number().min(0).max(2.0).optional(),
    responsiveness: z.number().min(0).max(2.0).optional(),
    backchanneling: z.boolean(),
    filler_words: z.boolean(),
    interruption_sensitivity: z.number().min(0).max(1),
  }),
  conversation_flow: z.object({
    max_turns: z.number().min(5).max(50).optional(),
    timeout_seconds: z.number().min(30).max(300).optional(),
    retry_attempts: z.number().min(1).max(5).optional(),
    emergency_keywords: z.array(z.string()).optional(),
    data_extraction_points: z.array(z.string()).optional(),
  }),
  is_active: z.boolean().optional(),
})

type AgentConfigFormData = z.infer<typeof agentConfigSchema>

export default function EditAgentConfigPage() {
  const router = useRouter()
  const params = useParams()
  const configId = parseInt(params?.id as string)
  
  const { data: agentConfig, isLoading: loadingConfig } = useAgentConfig(configId)
  const config = agentConfig as AgentConfiguration | undefined
  const updateAgent = useUpdateAgentConfig()
  const [currentStep, setCurrentStep] = useState(1)
  const [isTestMode, setIsTestMode] = useState(false)

  const {
    register,
    handleSubmit,
    control,
    watch,
    reset,
    formState: { errors },
  } = useForm<AgentConfigFormData>({
    resolver: zodResolver(agentConfigSchema),
  })

  const scenarioType = watch('scenario_type')

  // Load existing configuration data
  useEffect(() => {
    if (config) {
      reset({
        name: config.name,
        scenario_type: config.scenario_type,
        description: config.description || '',
        prompts: config.prompts,
        voice_settings: config.voice_settings,
        conversation_flow: config.conversation_flow,
        is_active: config.is_active,
      })
    }
  }, [config, reset])

  const onSubmit = async (data: AgentConfigFormData) => {
    try {
      // Set data extraction points based on scenario type
      const dataExtractionPoints = data.scenario_type === 'check_in' 
        ? ['call_outcome', 'driver_status', 'current_location', 'eta', 'delay_reason', 'unloading_status', 'pod_reminder_acknowledged']
        : ['call_outcome', 'emergency_type', 'safety_status', 'injury_status', 'emergency_location', 'load_secure', 'escalation_status']
      
      const submitData = {
        ...data,
        conversation_flow: {
          ...data.conversation_flow,
          data_extraction_points: dataExtractionPoints,
        },
        is_active: data.is_active ?? true,
      }
      
      await updateAgent.mutateAsync({
        id: configId,
        data: submitData
      })
      toast.success('Agent configuration updated successfully!')
      router.push('/dashboard/agents')
    } catch (error) {
      toast.error('Failed to update agent configuration')
      console.error('Error updating agent:', error)
    }
  }

  const handleTestConfiguration = () => {
    setIsTestMode(true)
    // In a real implementation, this would trigger a test call
    toast.success('Test mode activated - configuration preview available')
  }

  if (loadingConfig) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading configuration...</p>
        </div>
      </div>
    )
  }

  if (!config) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Configuration Not Found</h2>
          <p className="text-gray-600 mb-4">The agent configuration you&apos;re looking for doesn&apos;t exist.</p>
          <Link href="/dashboard/agents">
            <Button>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Configurations
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/dashboard/agents">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back
                </Button>
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Edit Agent Configuration</h1>
                <p className="text-gray-600">Modify your AI voice agent settings and conversation flow</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleTestConfiguration}
                className="flex items-center"
              >
                <TestTube className="h-4 w-4 mr-2" />
                Test Config
              </Button>
              <Badge 
                variant={config?.is_active ? 'default' : 'secondary'}
                className="px-3 py-1"
              >
                {config?.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
          </div>
        </div>

        {/* Progress Steps */}
        <Card className="mb-6">
          <CardContent className="py-6">
            <div className="flex items-center justify-between">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    currentStep >= step 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {currentStep > step ? <CheckCircle className="h-4 w-4" /> : step}
                  </div>
                  <div className="ml-3 text-sm">
                    <p className={`font-medium ${currentStep >= step ? 'text-blue-600' : 'text-gray-500'}`}>
                      {step === 1 && 'Basic Settings'}
                      {step === 2 && 'Conversation Design'}
                      {step === 3 && 'Voice Configuration'}
                    </p>
                  </div>
                  {step < 3 && (
                    <div className={`w-16 h-0.5 ml-4 ${
                      currentStep > step ? 'bg-blue-600' : 'bg-gray-200'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <form 
          onSubmit={handleSubmit(onSubmit)} 
          onKeyDown={(e) => {
            // Prevent form submission on Enter key except for submit buttons
            if (e.key === 'Enter' && (e.target as HTMLElement).getAttribute('type') !== 'submit') {
              e.preventDefault()
            }
          }}
          className="space-y-6"
        >
          {/* Step 1: Basic Information */}
          {currentStep === 1 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="h-5 w-5 mr-2" />
                  Basic Configuration
                </CardTitle>
                <CardDescription>
                  Update the basic settings for your agent configuration
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">Configuration Name</label>
                    <Input
                      {...register('name')}
                      placeholder="Enter a descriptive name"
                      className={errors.name ? 'border-red-500' : ''}
                    />
                    {errors.name && (
                      <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Scenario Type</label>
                    <select
                      {...register('scenario_type')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="check_in">Driver Check-in</option>
                      <option value="emergency">Emergency Protocol</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <Textarea
                    {...register('description')}
                    placeholder="Brief description of this configuration's purpose"
                    rows={3}
                  />
                </div>

                <div className="flex items-center">
                  <Controller
                    name="is_active"
                    control={control}
                    render={({ field }) => (
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={field.value}
                          onChange={field.onChange}
                          className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                        />
                        <span className="ml-2 text-sm text-gray-700">Active Configuration</span>
                      </label>
                    )}
                  />
                </div>

                <div className="flex justify-end">
                  <Button
                    type="button"
                    onClick={() => setCurrentStep(2)}
                    disabled={!watch('name')}
                    className="flex items-center"
                  >
                    Next: Configure Prompts
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 2: Conversation Prompts */}
          {currentStep === 2 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MessageSquare className="h-5 w-5 mr-2" />
                  Conversation Prompts
                </CardTitle>
                <CardDescription>
                  Define how your agent will communicate with drivers
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Opening Prompt</label>
                  <Textarea
                    {...register('prompts.opening')}
                    placeholder="The first thing your agent will say when the call connects..."
                    rows={3}
                    className={errors.prompts?.opening ? 'border-red-500' : ''}
                  />
                  {errors.prompts?.opening && (
                    <p className="text-sm text-red-600 mt-1">{errors.prompts.opening.message}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    Use [DRIVER_NAME] and [LOAD_NUMBER] as placeholders
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Follow-up Prompt</label>
                  <Textarea
                    {...register('prompts.follow_up')}
                    placeholder="How the agent will ask for more information..."
                    rows={3}
                    className={errors.prompts?.follow_up ? 'border-red-500' : ''}
                  />
                  {errors.prompts?.follow_up && (
                    <p className="text-sm text-red-600 mt-1">{errors.prompts.follow_up.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Closing Prompt</label>
                  <Textarea
                    {...register('prompts.closing')}
                    placeholder="How the agent will end the conversation..."
                    rows={3}
                    className={errors.prompts?.closing ? 'border-red-500' : ''}
                  />
                  {errors.prompts?.closing && (
                    <p className="text-sm text-red-600 mt-1">{errors.prompts.closing.message}</p>
                  )}
                </div>

                {scenarioType === 'emergency' && (
                  <div>
                    <label className="block text-sm font-medium mb-2">Emergency Trigger Response</label>
                    <Textarea
                      {...register('prompts.emergency_trigger')}
                      placeholder="What the agent says when an emergency is detected..."
                      rows={3}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      This prompt activates when emergency keywords are detected
                    </p>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium mb-2">Data Extraction Points</label>
                  <p className="text-sm text-gray-600 mb-3">
                    The following data points will be automatically extracted from conversations:
                  </p>
                  <div className="space-y-2">
                    {scenarioType === 'check_in' ? (
                      <div className="grid grid-cols-2 gap-2">
                        {['call_outcome', 'driver_status', 'current_location', 'eta', 'delay_reason', 'unloading_status', 'pod_reminder_acknowledged'].map((point) => (
                          <div key={point} className="flex items-center">
                            <input type="checkbox" id={point} className="mr-2" defaultChecked disabled />
                            <label htmlFor={point} className="text-sm capitalize text-gray-700">
                              {point.replace('_', ' ')}
                            </label>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-2">
                        {['call_outcome', 'emergency_type', 'safety_status', 'injury_status', 'emergency_location', 'load_secure', 'escalation_status'].map((point) => (
                          <div key={point} className="flex items-center">
                            <input type="checkbox" id={point} className="mr-2" defaultChecked disabled />
                            <label htmlFor={point} className="text-sm capitalize text-gray-700">
                              {point.replace('_', ' ')}
                            </label>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    These extraction points are automatically configured based on the scenario type
                  </p>
                </div>

                <div className="flex justify-between">
                  <Button 
                    type="button" 
                    variant="outline"
                    onClick={() => setCurrentStep(1)}
                  >
                    Previous
                  </Button>
                  <Button 
                    type="button" 
                    onClick={() => setCurrentStep(3)}
                    disabled={!watch('prompts.opening') || !watch('prompts.follow_up') || !watch('prompts.closing')}
                  >
                    Next: Voice Settings
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 3: Voice Settings */}
          {currentStep === 3 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Mic className="h-5 w-5 mr-2" />
                  Voice Configuration
                </CardTitle>
                <CardDescription>
                  Configure how your agent sounds and behaves during calls
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Speech Speed: {watch('voice_settings.voice_speed')}x
                    </label>
                    <Controller
                      name="voice_settings.voice_speed"
                      control={control}
                      render={({ field }) => (
                        <input
                          type="range"
                          min="0.5"
                          max="2.0"
                          step="0.1"
                          {...field}
                          onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          className="w-full"
                        />
                      )}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Slow (0.5x)</span>
                      <span>Fast (2.0x)</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Interruption Sensitivity: {Math.round(watch('voice_settings.interruption_sensitivity') * 100)}%
                    </label>
                    <Controller
                      name="voice_settings.interruption_sensitivity"
                      control={control}
                      render={({ field }) => (
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          {...field}
                          onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          className="w-full"
                        />
                      )}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Low</span>
                      <span>High</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center space-x-3">
                    <Controller
                      name="voice_settings.backchanneling"
                      control={control}
                      render={({ field }) => (
                        <input
                          type="checkbox"
                          checked={field.value}
                          onChange={field.onChange}
                          className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                        />
                      )}
                    />
                    <div>
                      <label className="font-medium text-sm">Enable Backchanneling</label>
                      <p className="text-xs text-gray-500">Agent says &quot;uh-huh&quot;, &quot;mm-hmm&quot; while listening</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <Controller
                      name="voice_settings.filler_words"
                      control={control}
                      render={({ field }) => (
                        <input
                          type="checkbox"
                          checked={field.value}
                          onChange={field.onChange}
                          className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                        />
                      )}
                    />
                    <div>
                      <label className="font-medium text-sm">Use Filler Words</label>
                      <p className="text-xs text-gray-500">Agent uses &quot;um&quot;, &quot;uh&quot; for natural speech</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Voice Temperature: {watch('voice_settings.voice_temperature') || 0.7}
                    </label>
                    <Controller
                      name="voice_settings.voice_temperature"
                      control={control}
                      render={({ field }) => (
                        <input
                          type="range"
                          min="0"
                          max="2"
                          step="0.1"
                          value={field.value || 0.7}
                          onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          className="w-full"
                        />
                      )}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Conservative</span>
                      <span>Creative</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Responsiveness: {watch('voice_settings.responsiveness') || 1.0}x
                    </label>
                    <Controller
                      name="voice_settings.responsiveness"
                      control={control}
                      render={({ field }) => (
                        <input
                          type="range"
                          min="0"
                          max="2"
                          step="0.1"
                          value={field.value || 1.0}
                          onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          className="w-full"
                        />
                      )}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Slow</span>
                      <span>Fast</span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Conversation Flow Settings</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <label className="block font-medium mb-1">Max Turns</label>
                      <Input
                        type="number"
                        {...register('conversation_flow.max_turns', { valueAsNumber: true })}
                        min="5"
                        max="50"
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block font-medium mb-1">Timeout (seconds)</label>
                      <Input
                        type="number"
                        {...register('conversation_flow.timeout_seconds', { valueAsNumber: true })}
                        min="30"
                        max="300"
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block font-medium mb-1">Retry Attempts</label>
                      <Input
                        type="number"
                        {...register('conversation_flow.retry_attempts', { valueAsNumber: true })}
                        min="1"
                        max="5"
                        className="w-full"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex justify-between">
                  <Button 
                    type="button" 
                    variant="outline"
                    onClick={() => setCurrentStep(2)}
                  >
                    Previous
                  </Button>
                  <Button 
                    type="submit"
                    disabled={updateAgent.isPending}
                    className="flex items-center"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {updateAgent.isPending ? 'Updating...' : 'Update Configuration'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

        </form>

        {/* Test Mode Preview */}
        {isTestMode && (
          <Card className="mt-6 border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="flex items-center text-blue-800">
                <Play className="h-5 w-5 mr-2" />
                Configuration Preview
              </CardTitle>
              <CardDescription>
                Preview of your updated agent configuration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Opening:</h4>
                  <p className="text-sm text-gray-700">{watch('prompts.opening')}</p>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <strong>Speed:</strong> {watch('voice_settings.voice_speed')}x
                  </div>
                  <div>
                    <strong>Backchanneling:</strong> {watch('voice_settings.backchanneling') ? 'Enabled' : 'Disabled'}
                  </div>
                  <div>
                    <strong>Filler Words:</strong> {watch('voice_settings.filler_words') ? 'Enabled' : 'Disabled'}
                  </div>
                  <div>
                    <strong>Interruption Sensitivity:</strong> {Math.round(watch('voice_settings.interruption_sensitivity') * 100)}%
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
