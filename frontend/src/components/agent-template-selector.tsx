'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  AGENT_TEMPLATES,
  SCENARIO_DESCRIPTIONS,
  AgentTemplate
} from '@/lib/agent-templates'
import {
  Sparkles,
  Shield,
  CheckCircle,
  AlertTriangle,
  Phone,
  Users,
  Settings,
  Mic
} from 'lucide-react'

interface AgentTemplateSelectorProps {
  onSelectTemplate: (template: AgentTemplate) => void
  trigger?: React.ReactNode
}

export function AgentTemplateSelector({ onSelectTemplate, trigger }: AgentTemplateSelectorProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<AgentTemplate | null>(null)
  const [isOpen, setIsOpen] = useState(false)

  const handleSelectTemplate = (template: AgentTemplate) => {
    setSelectedTemplate(template)
    onSelectTemplate(template)
    setIsOpen(false)
  }

  const getScenarioIcon = (scenarioType: string) => {
    switch (scenarioType) {
      case 'driver_checkin':
        return <Users className="h-5 w-5" />
      case 'emergency_protocol':
        return <Shield className="h-5 w-5" />
      default:
        return <Settings className="h-5 w-5" />
    }
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

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" className="w-full">
            <Sparkles className="h-4 w-4 mr-2" />
            Use Template
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Agent Templates
          </DialogTitle>
          <DialogDescription>
            Choose from pre-configured agent templates designed for specific logistics scenarios.
            These templates follow best practices for realistic voice experiences.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[70vh]">
          <div className="space-y-6">
            {AGENT_TEMPLATES.map((template) => {
              const scenarioInfo = SCENARIO_DESCRIPTIONS[template.scenario_type]

              return (
                <Card key={template.id} className="border-2 hover:border-blue-300 hover:shadow-lg transition-all duration-200 group cursor-pointer bg-gradient-to-br from-white to-slate-50"
                  onClick={() => handleSelectTemplate(template)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <div className={`p-2 rounded-lg ${template.scenario_type === 'driver_checkin' ? 'bg-blue-100' : 'bg-red-100'}`}>
                            {getScenarioIcon(template.scenario_type)}
                          </div>
                          <div className="flex-1">
                            <CardTitle className="text-lg group-hover:text-blue-600 transition-colors">{template.name}</CardTitle>
                            <Badge
                              className={`${getScenarioColor(template.scenario_type)} mt-1`}
                              variant="secondary"
                            >
                              {scenarioInfo.title}
                            </Badge>
                          </div>
                        </div>
                        <CardDescription className="text-sm">
                          {template.description}
                        </CardDescription>
                      </div>
                      <div className="shrink-0 bg-gradient-to-r from-green-600 to-emerald-600 group-hover:from-green-700 group-hover:to-emerald-700 text-white font-medium px-4 py-2 rounded-lg shadow-md group-hover:shadow-lg transition-all duration-200 flex items-center gap-2 group-hover:scale-105">
                        <CheckCircle className="h-4 w-4 group-hover:scale-110 transition-transform" />
                        <span className="text-sm font-semibold">Select Template</span>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    {/* Scenario Features */}
                    <div>
                      <h4 className="font-medium text-sm mb-2 flex items-center gap-1">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        Key Features
                      </h4>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {scenarioInfo.features.map((feature, index) => (
                          <div key={index} className="flex items-center gap-1">
                            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                            {feature}
                          </div>
                        ))}
                      </div>
                    </div>

                    <Separator />

                    {/* Voice Settings */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                      <div>
                        <div className="font-medium flex items-center gap-1 mb-1">
                          <Mic className="h-3 w-3" />
                          Voice
                        </div>
                        <div className="text-muted-foreground">{template.voice_id}</div>
                      </div>
                      <div>
                        <div className="font-medium mb-1">Temperature</div>
                        <div className="text-muted-foreground">{template.temperature}</div>
                      </div>
                      <div>
                        <div className="font-medium mb-1">Backchannel</div>
                        <div className="text-muted-foreground capitalize">
                          {template.backchannel_frequency}
                        </div>
                      </div>
                      <div>
                        <div className="font-medium mb-1">Interruption</div>
                        <div className="text-muted-foreground capitalize">
                          {template.interruption_sensitivity}
                        </div>
                      </div>
                    </div>

                    <Separator />

                    {/* Expected Data Fields */}
                    <div>
                      <h4 className="font-medium text-sm mb-2 flex items-center gap-1">
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                        Extracted Data Fields
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {template.expected_data_fields.map((field) => (
                          <Badge key={field} variant="outline" className="text-xs">
                            {field.replace(/_/g, ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Expected Outcomes */}
                    <div>
                      <h4 className="font-medium text-sm mb-2">Expected Outcomes</h4>
                      <div className="flex flex-wrap gap-1">
                        {scenarioInfo.expected_outcomes.map((outcome) => (
                          <Badge key={outcome} variant="secondary" className="text-xs">
                            {outcome}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Emergency Keywords (for emergency protocol) */}
                    {template.scenario_type === 'emergency_protocol' && (
                      <div>
                        <h4 className="font-medium text-sm mb-2 flex items-center gap-1 text-red-600">
                          <Shield className="h-4 w-4" />
                          Emergency Keywords
                        </h4>
                        <div className="text-xs text-muted-foreground">
                          {template.advanced_settings.emergency_keywords.slice(0, 8).join(', ')}
                          {template.advanced_settings.emergency_keywords.length > 8 && '...'}
                        </div>
                      </div>
                    )}

                    {/* Click indicator */}
                    <div className="text-center pt-3 mt-3 border-t border-slate-100">
                      <div className="text-xs text-slate-400 group-hover:text-blue-500 transition-colors flex items-center justify-center gap-1">
                        <span>Click anywhere to select this template</span>
                        <div className="w-1.5 h-1.5 bg-slate-400 group-hover:bg-blue-500 rounded-full animate-pulse"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </ScrollArea>

        <div className="flex items-center justify-between pt-4 border-t">
          <div className="text-sm text-muted-foreground">
            Templates are pre-configured with optimal settings for realistic voice experiences
          </div>
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Cancel
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}