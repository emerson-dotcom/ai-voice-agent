import { z } from 'zod'

// Voice settings schema
export const voiceSettingsSchema = z.object({
  backchanneling: z.boolean(),
  filler_words: z.boolean(),
  interruption_sensitivity: z.number().min(0).max(1),
  voice_speed: z.number().min(0.5).max(2),
  voice_temperature: z.number().min(0).max(2),
  responsiveness: z.number().min(0).max(2),
})

// Conversation prompts schema
export const conversationPromptsSchema = z.object({
  opening: z.string().min(10, 'Opening prompt must be at least 10 characters').max(1000, 'Opening prompt must be less than 1000 characters'),
  follow_up: z.string().min(10, 'Follow-up prompt must be at least 10 characters').max(1000, 'Follow-up prompt must be less than 1000 characters'),
  closing: z.string().min(10, 'Closing prompt must be at least 10 characters').max(500, 'Closing prompt must be less than 500 characters'),
  emergency_trigger: z.string().max(1000, 'Emergency trigger must be less than 1000 characters').optional(),
  probing_questions: z.array(z.string()).default([]),
})

// Conversation flow schema
export const conversationFlowSchema = z.object({
  max_turns: z.number().min(5).max(50),
  timeout_seconds: z.number().min(30).max(300),
  retry_attempts: z.number().min(1).max(5),
  emergency_keywords: z.array(z.string()).default([
    'emergency', 'accident', 'blowout', 'medical', 'breakdown', 'crash', 'injured'
  ]),
  data_extraction_points: z.array(z.string()).default([]),
})

// Agent configuration schema
export const agentConfigSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters').max(100, 'Name must be less than 100 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional(),
  scenario_type: z.enum(['check_in', 'emergency']),
  prompts: conversationPromptsSchema,
  voice_settings: voiceSettingsSchema,
  conversation_flow: conversationFlowSchema,
})

// Call initiation schema
export const callInitiationSchema = z.object({
  driver_name: z.string().min(2, 'Driver name must be at least 2 characters').max(100, 'Driver name must be less than 100 characters'),
  phone_number: z.string().regex(/^\+?[1-9]\d{1,14}$/, 'Please enter a valid phone number'),
  load_number: z.string().min(3, 'Load number must be at least 3 characters').max(50, 'Load number must be less than 50 characters'),
  agent_config_id: z.number().min(1, 'Please select an agent configuration'),
})

// Login schema
export const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

// Registration schema
export const registrationSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string().min(6, 'Please confirm your password'),
  fullName: z.string().min(2, 'Full name must be at least 2 characters').max(100, 'Full name must be less than 100 characters').optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

// Search/filter schemas
export const callFilterSchema = z.object({
  status_filter: z.string().optional(),
  driver_name: z.string().optional(),
  load_number: z.string().optional(),
  page: z.number().min(1).optional(),
  per_page: z.number().min(1).max(100).optional(),
})

export const agentFilterSchema = z.object({
  scenario_type: z.string().optional(),
  is_active: z.boolean().optional(),
  page: z.number().min(1).optional(),
  per_page: z.number().min(1).max(100).optional(),
})

// Type exports
export type VoiceSettingsFormData = z.infer<typeof voiceSettingsSchema>
export type ConversationPromptsFormData = z.infer<typeof conversationPromptsSchema>
export type ConversationFlowFormData = z.infer<typeof conversationFlowSchema>
export type AgentConfigFormData = z.infer<typeof agentConfigSchema>
export type CallInitiationFormData = z.infer<typeof callInitiationSchema>
export type LoginFormData = z.infer<typeof loginSchema>
export type RegistrationFormData = z.infer<typeof registrationSchema>
export type CallFilterFormData = z.infer<typeof callFilterSchema>
export type AgentFilterFormData = z.infer<typeof agentFilterSchema>
