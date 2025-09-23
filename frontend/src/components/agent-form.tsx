'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Separator } from '@/components/ui/separator'
import { AgentTemplateSelector } from '@/components/agent-template-selector'
import { AgentFormData, Voice } from '@/types'
import { AgentTemplate } from '@/lib/agent-templates'
import { voiceApi } from '@/lib/api'
import { Save, Volume2, Mic, Settings, Sparkles } from 'lucide-react'

interface AgentFormProps {
  initialData?: Partial<AgentFormData>
  onSubmit: (data: AgentFormData) => Promise<void>
  isLoading?: boolean
}

const SCENARIO_TYPES = [
  { value: 'driver_checkin', label: 'Driver Check-in Agent' },
  { value: 'emergency_protocol', label: 'Emergency Protocol Agent' }
]

const VOICE_MODELS_BY_PROVIDER = {
  elevenlabs: [
    { value: 'eleven_turbo_v2', label: 'ElevenLabs Turbo v2' },
    { value: 'eleven_flash_v2', label: 'ElevenLabs Flash v2' },
    { value: 'eleven_turbo_v2_5', label: 'ElevenLabs Turbo v2.5' },
    { value: 'eleven_flash_v2_5', label: 'ElevenLabs Flash v2.5' },
    { value: 'eleven_multilingual_v2', label: 'ElevenLabs Multilingual v2' }
  ],
  cartesia: [
    { value: 'sonic-2', label: 'Cartesia Sonic 2' },
    { value: 'sonic-turbo', label: 'Cartesia Sonic Turbo' }
  ],
  openai: [
    { value: 'tts-1', label: 'OpenAI TTS-1' },
    { value: 'gpt-4o-mini-tts', label: 'OpenAI GPT-4o Mini TTS' }
  ],
  deepgram: [
    { value: 'sonic-2', label: 'Deepgram Sonic 2' }
  ]
}

// Helper functions
const getVoiceProvider = (voiceId: string): keyof typeof VOICE_MODELS_BY_PROVIDER => {
  if (voiceId.startsWith('11labs-')) return 'elevenlabs'
  if (voiceId.startsWith('cartesia-')) return 'cartesia'
  if (voiceId.startsWith('openai-')) return 'openai'
  if (voiceId.startsWith('deepgram-')) return 'deepgram'
  return 'elevenlabs' // default fallback
}

const getDefaultVoiceModel = (voiceId: string): string => {
  const provider = getVoiceProvider(voiceId)
  const models = VOICE_MODELS_BY_PROVIDER[provider]
  return models?.[0]?.value || 'eleven_turbo_v2'
}

export default function AgentForm({ initialData, onSubmit, isLoading = false }: AgentFormProps) {
  const [voices, setVoices] = useState<Voice[]>([])
  const [voicesLoading, setVoicesLoading] = useState(true)
  const [formData, setFormData] = useState<AgentFormData>({
    name: '',
    description: '',
    general_prompt: '',
    begin_message: '',
    voice_id: 'cartesia-Sarah',
    voice_model: 'sonic-2',
    voice_temperature: 0.8,
    voice_speed: 1.0,
    enable_backchannel: true,
    backchannel_frequency: 0.8,
    backchannel_words: ['yeah', 'uh-huh', 'mm-hmm'],
    interruption_sensitivity: 0.8,
    responsiveness: 0.9,
    scenario_type: 'driver_checkin',
    system_prompt: '',
    greeting_message: '',
    initial_message: '',
    fallback_message: '',
    end_call_message: '',
    enable_transcription: true,
    response_delay_ms: 300,
    temperature: 0.7,
    max_tokens: 200,
    ...initialData
  })

  // Fetch voices from API
  useEffect(() => {
    const fetchVoices = async () => {
      try {
        setVoicesLoading(true)
        const fetchedVoices = await voiceApi.list()
        setVoices(fetchedVoices)
      } catch (error) {
        console.error('Failed to fetch voices:', error)
        // Set fallback voices on error
        setVoices([
          { voice_id: 'cartesia-Sarah', voice_name: 'Sarah', provider: 'cartesia', gender: 'female' },
          { voice_id: '11labs-Adrian', voice_name: 'Adrian', provider: 'elevenlabs', gender: 'male' }
        ])
      } finally {
        setVoicesLoading(false)
      }
    }

    fetchVoices()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await onSubmit(formData)
  }

  const updateField = (field: keyof AgentFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const updateVoiceId = (voiceId: string) => {
    const defaultModel = getDefaultVoiceModel(voiceId)
    setFormData(prev => ({
      ...prev,
      voice_id: voiceId,
      voice_model: defaultModel
    }))
  }

  const updateBackchannelWords = (words: string) => {
    const wordArray = words.split(',').map(w => w.trim()).filter(w => w.length > 0)
    updateField('backchannel_words', wordArray)
  }

  const handleTemplateSelect = (template: AgentTemplate) => {
    // Convert string values to numbers for API compatibility
    const convertFrequency = (freq: string): number => {
      switch (freq) {
        case 'low': return 0.3
        case 'medium': return 0.5
        case 'high': return 0.8
        default: return 0.5
      }
    }

    const convertSensitivity = (sensitivity: string): number => {
      switch (sensitivity) {
        case 'low': return 0.3
        case 'medium': return 0.5
        case 'high': return 0.8
        case 'very_high': return 0.9
        default: return 0.8
      }
    }

    // Apply template data to form
    setFormData({
      ...formData,
      name: template.name,
      description: template.description,
      scenario_type: template.scenario_type,
      voice_id: template.voice_id,
      voice_model: template.voice_model,
      temperature: template.temperature,
      max_tokens: template.max_tokens,
      general_prompt: template.general_prompt,
      begin_message: template.begin_message,
      system_prompt: template.system_prompt,
      greeting_message: template.greeting_message,
      initial_message: template.initial_message,
      fallback_message: template.fallback_message,
      end_call_message: template.end_call_message,
      enable_backchannel: template.enable_backchannel,
      backchannel_frequency: convertFrequency(template.backchannel_frequency),
      interruption_sensitivity: convertSensitivity(template.interruption_sensitivity),
      enable_transcription: template.enable_transcription,
      response_delay_ms: template.response_delay_ms,
      backchannel_words: ['uh-huh', 'I see', 'got it', 'okay', 'mm-hmm']
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Template Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Quick Start with Templates
          </CardTitle>
          <CardDescription>
            Use pre-configured agent templates designed for specific logistics scenarios, or create a custom agent from scratch.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4">
            <AgentTemplateSelector
              onSelectTemplate={handleTemplateSelect}
              trigger={
                <Button
                  type="button"
                  size="lg"
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200 group border-0"
                >
                  <div className="flex items-center justify-center gap-3">
                    <Sparkles className="h-5 w-5 group-hover:scale-110 transition-transform" />
                    <span>Choose Pre-configured Template</span>
                  </div>
                </Button>
              }
            />

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-white px-3 py-1 text-slate-500 rounded-full border border-slate-200">
                  or configure manually below
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Basic Information
          </CardTitle>
          <CardDescription>
            Configure the basic settings for your voice agent
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Agent Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => updateField('name', e.target.value)}
                placeholder="e.g., Driver Check-in Agent"
                disabled={isLoading}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="scenario_type">Scenario Type *</Label>
              <Select value={formData.scenario_type} onValueChange={(value) => updateField('scenario_type', value)} disabled={isLoading}>
                <SelectTrigger>
                  <SelectValue placeholder="Select scenario type" />
                </SelectTrigger>
                <SelectContent>
                  {SCENARIO_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={formData.description}
              onChange={(e) => updateField('description', e.target.value)}
              placeholder="Brief description of the agent's purpose"
              disabled={isLoading}
            />
          </div>
        </CardContent>
      </Card>

      {/* Conversation Logic */}
      <Card>
        <CardHeader>
          <CardTitle>Conversation Logic</CardTitle>
          <CardDescription>
            Define how the agent will conduct conversations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="general_prompt">General Prompt *</Label>
            <Textarea
              id="general_prompt"
              value={formData.general_prompt}
              onChange={(e) => updateField('general_prompt', e.target.value)}
              placeholder="You are a professional dispatch agent calling drivers about their load status..."
              className="min-h-[120px]"
              disabled={isLoading}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="begin_message">Opening Message</Label>
            <Textarea
              id="begin_message"
              value={formData.begin_message}
              onChange={(e) => updateField('begin_message', e.target.value)}
              placeholder="Hi {{driver_name}}, this is Dispatch calling about load {{load_number}}..."
              className="min-h-[80px]"
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="system_prompt">System Prompt</Label>
            <Textarea
              id="system_prompt"
              value={formData.system_prompt}
              onChange={(e) => updateField('system_prompt', e.target.value)}
              placeholder="You are a professional dispatcher. Your goal is to..."
              className="min-h-[100px]"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="initial_message">Initial Message</Label>
              <Textarea
                id="initial_message"
                value={formData.initial_message}
                onChange={(e) => updateField('initial_message', e.target.value)}
                placeholder="Can you give me an update on your status?"
                className="min-h-[60px]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="fallback_message">Fallback Message</Label>
              <Textarea
                id="fallback_message"
                value={formData.fallback_message}
                onChange={(e) => updateField('fallback_message', e.target.value)}
                placeholder="I understand. Can you tell me more about your current situation?"
                className="min-h-[60px]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="greeting_message">Greeting Message</Label>
              <Input
                id="greeting_message"
                value={formData.greeting_message}
                onChange={(e) => updateField('greeting_message', e.target.value)}
                placeholder="Hi {driver_name}, this is dispatch..."
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="end_call_message">End Call Message</Label>
              <Input
                id="end_call_message"
                value={formData.end_call_message}
                onChange={(e) => updateField('end_call_message', e.target.value)}
                placeholder="Thank you for the update. Drive safely!"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Voice Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Volume2 className="h-5 w-5" />
            Voice Settings
          </CardTitle>
          <CardDescription>
            Configure the agent's voice characteristics
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="voice_id">Voice *</Label>
              <Select value={formData.voice_id} onValueChange={updateVoiceId} disabled={isLoading}>
                <SelectTrigger>
                  <SelectValue placeholder="Select voice" />
                </SelectTrigger>
                <SelectContent>
                  {voicesLoading ? (
                    <SelectItem value="loading" disabled>Loading voices...</SelectItem>
                  ) : voices.length === 0 ? (
                    <SelectItem value="no-voices" disabled>No voices available</SelectItem>
                  ) : (
                    voices.map((voice) => (
                      <SelectItem key={voice.voice_id} value={voice.voice_id}>
                        {voice.voice_name} ({voice.provider}) - {voice.gender}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="voice_model">Voice Model</Label>
              <Select value={formData.voice_model} onValueChange={(value) => updateField('voice_model', value)} disabled={isLoading}>
                <SelectTrigger>
                  <SelectValue placeholder="Select voice model" />
                </SelectTrigger>
                <SelectContent>
                  {VOICE_MODELS_BY_PROVIDER[getVoiceProvider(formData.voice_id)].map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Voice Temperature: {formData.voice_temperature}</Label>
              <Slider
                value={[formData.voice_temperature]}
                onValueChange={([value]) => updateField('voice_temperature', value)}
                max={2}
                min={0}
                step={0.1}
                className="w-full"
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                Controls voice expressiveness (0 = monotone, 2 = very expressive)
              </p>
            </div>

            <div className="space-y-2">
              <Label>Voice Speed: {formData.voice_speed}</Label>
              <Slider
                value={[formData.voice_speed]}
                onValueChange={([value]) => updateField('voice_speed', value)}
                max={2}
                min={0.5}
                step={0.1}
                className="w-full"
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                Controls speaking speed (0.5 = slow, 2 = fast)
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI & Response Settings */}
      <Card>
        <CardHeader>
          <CardTitle>AI & Response Settings</CardTitle>
          <CardDescription>
            Configure AI model behavior and response characteristics
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>AI Temperature: {formData.temperature}</Label>
              <Slider
                value={[formData.temperature || 0.7]}
                onValueChange={([value]) => updateField('temperature', value)}
                max={1}
                min={0}
                step={0.1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Controls AI creativity (0 = consistent, 1 = creative)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="max_tokens">Max Tokens</Label>
              <Input
                id="max_tokens"
                type="number"
                value={formData.max_tokens || 200}
                onChange={(e) => updateField('max_tokens', parseInt(e.target.value) || 200)}
                min={50}
                max={500}
              />
              <p className="text-xs text-muted-foreground">
                Maximum response length
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="response_delay_ms">Response Delay (ms)</Label>
              <Input
                id="response_delay_ms"
                type="number"
                value={formData.response_delay_ms || 300}
                onChange={(e) => updateField('response_delay_ms', parseInt(e.target.value) || 300)}
                min={0}
                max={2000}
              />
              <p className="text-xs text-muted-foreground">
                Delay before responding
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Call Transcription</Label>
              <p className="text-xs text-muted-foreground">
                Record and transcribe calls for analysis
              </p>
            </div>
            <Switch
              checked={formData.enable_transcription || true}
              onCheckedChange={(checked) => updateField('enable_transcription', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Advanced Features */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5" />
            Advanced Voice Features
          </CardTitle>
          <CardDescription>
            Configure human-like conversation behaviors
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Backchannel</Label>
              <p className="text-xs text-muted-foreground">
                Agent will make acknowledgment sounds like "uh-huh", "yeah"
              </p>
            </div>
            <Switch
              checked={formData.enable_backchannel}
              onCheckedChange={(checked) => updateField('enable_backchannel', checked)}
              disabled={isLoading}
            />
          </div>

          {formData.enable_backchannel && (
            <>
              <div className="space-y-2">
                <Label>Backchannel Frequency: {formData.backchannel_frequency}</Label>
                <Slider
                  value={[formData.backchannel_frequency]}
                  onValueChange={([value]) => updateField('backchannel_frequency', value)}
                  max={1}
                  min={0}
                  step={0.1}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  How often the agent makes backchannel responses
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="backchannel_words">Backchannel Words</Label>
                <Input
                  id="backchannel_words"
                  value={formData.backchannel_words.join(', ')}
                  onChange={(e) => updateBackchannelWords(e.target.value)}
                  placeholder="yeah, uh-huh, mm-hmm, I see"
                />
                <p className="text-xs text-muted-foreground">
                  Comma-separated list of words/sounds for backchannel responses
                </p>
              </div>
            </>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Interruption Sensitivity: {formData.interruption_sensitivity}</Label>
              <Slider
                value={[formData.interruption_sensitivity]}
                onValueChange={([value]) => updateField('interruption_sensitivity', value)}
                max={1}
                min={0}
                step={0.1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                How easily the user can interrupt the agent
              </p>
            </div>

            <div className="space-y-2">
              <Label>Responsiveness: {formData.responsiveness}</Label>
              <Slider
                value={[formData.responsiveness]}
                onValueChange={([value]) => updateField('responsiveness', value)}
                max={1}
                min={0}
                step={0.1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                How quickly the agent responds to user speech
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Submit Button */}
      <div className="flex justify-end">
        <Button type="submit" disabled={isLoading} size="lg" className="min-w-[140px] shadow-lg hover:shadow-xl">
          {isLoading ? (
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
              Saving...
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Save className="h-4 w-4" />
              Save Agent
            </div>
          )}
        </Button>
      </div>
    </form>
  )
}