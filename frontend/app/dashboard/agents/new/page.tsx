'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { useCreateAgentConfig } from '@/hooks/use-agents'
import { 
  Save, 
  ArrowLeft, 
  CheckCircle, 
  AlertTriangle, 
  Settings,
  Mic,
  MessageSquare,
  Zap,
  TestTube,
  Play
} from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'

// Validation schema
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
  }),
  voice_settings: z.object({
    speed: z.number().min(0.5).max(2.0),
    backchanneling: z.boolean(),
    filler_words: z.boolean(),
    interruption_sensitivity: z.number().min(0).max(1),
  }),
  data_extraction_points: z.array(z.string()).optional(),
})

type AgentConfigFormData = z.infer<typeof agentConfigSchema>

// Template configurations
const TEMPLATES = {
  check_in: {
    name: 'Driver Check-in Configuration',
    scenario_type: 'check_in' as const,
    description: 'End-to-end driver check-in with dynamic conversation flow',
    prompts: {
      opening: "Hi [DRIVER_NAME], this is Dispatch with a check call on load [LOAD_NUMBER]. Can you give me an update on your status?",
      follow_up: "Thank you for that update. Can you provide me with your current location and estimated time of arrival?",
      closing: "Perfect, I've got all the information I need. Please remember to send your proof of delivery when you're done. Drive safe!",
      emergency_trigger: "I understand this is urgent. Let me gather some important information to help you right away.",
    },
    voice_settings: {
      speed: 1.0,
      backchanneling: true,
      filler_words: true,
      interruption_sensitivity: 0.7,
    },
    data_extraction_points: [
      'call_outcome',
      'driver_status',
      'current_location',
      'eta',
      'delay_reason',
      'unloading_status',
      'pod_reminder_acknowledged'
    ]
  },
  emergency: {
    name: 'Emergency Protocol Configuration',
    scenario_type: 'emergency' as const,
    description: 'Immediate emergency response with safety prioritization',
    prompts: {
      opening: "Hi [DRIVER_NAME], this is Dispatch checking on load [LOAD_NUMBER]. How are things going out there?",
      follow_up: "I understand this is an emergency situation. First, are you and anyone else with you safe right now?",
      closing: "I'm connecting you with our emergency dispatcher right now. Please stay on the line while I transfer you.",
      emergency_trigger: "I hear this is an emergency. Let me help you right away. First, is everyone safe?",
    },
    voice_settings: {
      speed: 0.9,
      backchanneling: false,
      filler_words: false,
      interruption_sensitivity: 0.9,
    },
    data_extraction_points: [
      'call_outcome',
      'emergency_type',
      'safety_status',
      'injury_status',
      'emergency_location',
      'load_secure',
      'escalation_status'
    ]
  }
}

export default function NewAgentConfigPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const template = searchParams?.get('template') as keyof typeof TEMPLATES
  const createAgent = useCreateAgentConfig()
  const [currentStep, setCurrentStep] = useState(1)
  const [isTestMode, setIsTestMode] = useState(false)

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<AgentConfigFormData>({
    resolver: zodResolver(agentConfigSchema),
    defaultValues: template && TEMPLATES[template] ? TEMPLATES[template] : {
      name: '',
      scenario_type: 'check_in',
      description: '',
      prompts: {
        opening: '',
        follow_up: '',
        closing: '',
        emergency_trigger: '',
      },
      voice_settings: {
        speed: 1.0,
        backchanneling: true,
        filler_words: true,
        interruption_sensitivity: 0.7,
      },
      data_extraction_points: [],
    },
  })

  const scenarioType = watch('scenario_type')

  // Load template if specified
  useEffect(() => {
    if (template && TEMPLATES[template]) {
      const templateData = TEMPLATES[template]
      Object.entries(templateData).forEach(([key, value]) => {
        setValue(key as keyof AgentConfigFormData, value)
      })
    }
  }, [template, setValue])

  const onSubmit = async (data: AgentConfigFormData) => {
    try {
      await createAgent.mutateAsync({
        ...data,
        is_active: true,
        is_deployed: false,
      })
      toast.success('Agent configuration created successfully!')
      router.push('/dashboard/agents')
    } catch (error) {
      toast.error('Failed to create agent configuration')
      console.error('Error creating agent:', error)
    }
  }

  const handleTestConfiguration = () => {
    setIsTestMode(true)
    // In a real implementation, this would trigger a test call
    toast.success('Test mode activated - configuration preview available')
  }

  const getScenarioInfo = (type: string) => {
    switch (type) {
      case 'check_in':
        return {
          icon: <CheckCircle className="h-5 w-5 text-blue-500" />,
          title: 'Driver Check-in Scenario',
          description: 'Handle driver status updates with dynamic conversation flow based on their current situation.'
        }
      case 'emergency':
        return {
          icon: <AlertTriangle className="h-5 w-5 text-red-500" />,
          title: 'Emergency Protocol Scenario',
          description: 'Immediate emergency response prioritizing safety assessment and human escalation.'
        }
      default:
        return {
          icon: <Settings className="h-5 w-5 text-gray-500" />,
          title: 'Custom Scenario',
          description: 'Configure a custom conversation flow for your specific needs.'
        }
    }
  }

  const scenarioInfo = getScenarioInfo(scenarioType)

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
            <h1 className="text-2xl font-bold text-gray-900">Create Agent Configuration</h1>
            <p className="text-gray-600">Set up a new AI voice agent for logistics scenarios</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {template && (
            <Badge className="bg-blue-100 text-blue-800">
              Using {template.replace('_', ' ')} template
            </Badge>
          )}
        </div>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${currentStep >= 1 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'}`}>
                1
              </div>
              <span className={currentStep >= 1 ? 'text-blue-600 font-medium' : 'text-gray-600'}>Basic Info</span>
            </div>
            <div className="flex-1 h-px bg-gray-200 mx-4"></div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${currentStep >= 2 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'}`}>
                2
              </div>
              <span className={currentStep >= 2 ? 'text-blue-600 font-medium' : 'text-gray-600'}>Prompts</span>
            </div>
            <div className="flex-1 h-px bg-gray-200 mx-4"></div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${currentStep >= 3 ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'}`}>
                3
              </div>
              <span className={currentStep >= 3 ? 'text-blue-600 font-medium' : 'text-gray-600'}>Voice Settings</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Step 1: Basic Information */}
        {currentStep === 1 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="h-5 w-5 mr-2" />
                Basic Configuration
              </CardTitle>
              <CardDescription>
                Define the basic settings for your agent configuration
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
                  <Controller
                    name="scenario_type"
                    control={control}
                    render={({ field }) => (
                      <select
                        {...field}
                        className={`w-full px-3 py-2 border rounded-md ${errors.scenario_type ? 'border-red-500' : 'border-gray-300'}`}
                      >
                        <option value="check_in">Driver Check-in</option>
                        <option value="emergency">Emergency Protocol</option>
                      </select>
                    )}
                  />
                  {errors.scenario_type && (
                    <p className="text-sm text-red-600 mt-1">{errors.scenario_type.message}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description (Optional)</label>
                <Textarea
                  {...register('description')}
                  placeholder="Describe the purpose and use case for this configuration"
                  rows={3}
                />
              </div>

              {/* Scenario Info */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center space-x-3 mb-2">
                  {scenarioInfo.icon}
                  <h3 className="font-medium">{scenarioInfo.title}</h3>
                </div>
                <p className="text-sm text-gray-600">{scenarioInfo.description}</p>
              </div>

              <div className="flex justify-end">
                <Button 
                  type="button" 
                  onClick={() => setCurrentStep(2)}
                  disabled={!watch('name')}
                >
                  Next: Configure Prompts
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Prompts Configuration */}
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
                Voice Settings
              </CardTitle>
              <CardDescription>
                Configure how your agent sounds and behaves during calls
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Speech Speed: {watch('voice_settings.speed')}x
                  </label>
                  <Controller
                    name="voice_settings.speed"
                    control={control}
                    render={({ field }) => (
                      <input
                        type="range"
                        min="0.5"
                        max="2.0"
                        step="0.1"
                        {...field}
                        className="w-full"
                      />
                    )}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Slower</span>
                    <span>Faster</span>
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
                        className="w-full"
                      />
                    )}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Less Sensitive</span>
                    <span>More Sensitive</span>
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
                        {...field}
                        checked={field.value}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                    )}
                  />
                  <div>
                    <label className="text-sm font-medium">Enable Backchanneling</label>
                    <p className="text-xs text-gray-500">Agent says "mm-hmm", "right", etc. while listening</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Controller
                    name="voice_settings.filler_words"
                    control={control}
                    render={({ field }) => (
                      <input
                        type="checkbox"
                        {...field}
                        checked={field.value}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                    )}
                  />
                  <div>
                    <label className="text-sm font-medium">Use Filler Words</label>
                    <p className="text-xs text-gray-500">Agent uses "um", "uh", etc. for natural speech</p>
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
                <div className="flex space-x-2">
                  <Button 
                    type="button" 
                    variant="outline"
                    onClick={handleTestConfiguration}
                  >
                    <TestTube className="h-4 w-4 mr-2" />
                    Test Configuration
                  </Button>
                  <Button 
                    type="submit"
                    disabled={createAgent.isPending || !isValid}
                  >
                    {createAgent.isPending ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Creating...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Create Configuration
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </form>

      {/* Test Mode Preview */}
      {isTestMode && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center text-blue-800">
              <Play className="h-5 w-5 mr-2" />
              Configuration Preview
            </CardTitle>
            <CardDescription className="text-blue-600">
              This is how your agent will behave with the current settings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 bg-white rounded border">
                <h4 className="font-medium mb-2">Opening:</h4>
                <p className="text-sm text-gray-700">{watch('prompts.opening')}</p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <strong>Speed:</strong> {watch('voice_settings.speed')}x
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
  )
}
