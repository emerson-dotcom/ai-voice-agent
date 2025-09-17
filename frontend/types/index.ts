// User types
export interface User {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

// Agent configuration types
export interface VoiceSettings {
  backchanneling: boolean
  filler_words: boolean
  interruption_sensitivity: number
  voice_speed: number
  voice_temperature: number
  responsiveness: number
}

export interface ConversationPrompts {
  opening: string
  follow_up: string
  closing: string
  emergency_trigger?: string
  probing_questions: string[]
}

export interface ConversationFlow {
  max_turns: number
  timeout_seconds: number
  retry_attempts: number
  emergency_keywords: string[]
  data_extraction_points: string[]
}

export interface AgentConfiguration {
  id: number
  name: string
  description?: string
  scenario_type: 'check_in' | 'emergency'
  prompts: ConversationPrompts
  voice_settings: VoiceSettings
  conversation_flow: ConversationFlow
  retell_agent_id?: string
  is_active: boolean
  is_deployed: boolean
  version: number
  created_by?: number
  created_at: string
  updated_at: string
}

// Call types
export type CallStatus = 'initiated' | 'in_progress' | 'completed' | 'failed' | 'cancelled'
export type CallType = 'web_call' | 'phone_call'
export type CallOutcome = 'In-Transit Update' | 'Arrival Confirmation' | 'Emergency Escalation'
export type DriverStatus = 'Driving' | 'Delayed' | 'Arrived' | 'Unloading'
export type EmergencyType = 'Accident' | 'Breakdown' | 'Medical' | 'Other'

export interface Call {
  id: number
  retell_call_id?: string
  driver_name: string
  phone_number: string
  load_number: string
  agent_config_id: number
  status: CallStatus
  call_type?: CallType
  call_outcome?: CallOutcome
  duration?: number
  start_time?: string
  end_time?: string
  extraction_confidence?: number
  conversation_quality_score?: number
  error_message?: string
  conversation_metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface CallDetail extends Call {
  raw_transcript?: string
  structured_data?: Record<string, any>
  conversation_metadata?: Record<string, any>
  agent_config_name?: string
  scenario_type?: string
  web_call_url?: string  // Add web call URL property
}

// Structured data types
export interface CheckInData {
  call_outcome: CallOutcome
  driver_status: DriverStatus
  current_location?: string
  eta?: string
  delay_reason?: string
  unloading_status?: string
  pod_reminder_acknowledged: boolean
}

export interface EmergencyData {
  call_outcome: CallOutcome
  emergency_type: EmergencyType
  safety_status?: string
  injury_status?: string
  emergency_location?: string
  load_secure: boolean
  escalation_status: string
}

// Conversation types
export interface ConversationTurn {
  turn_number: number
  speaker: 'agent' | 'driver'
  message: string
  timestamp: string
  confidence_score?: number
  intent_detected?: string
  entities_extracted?: Record<string, any>
  emergency_trigger_detected: boolean
  emergency_keywords?: string[]
}

export interface Transcript {
  call_id: number
  driver_name: string
  load_number: string
  total_duration?: number
  turns: ConversationTurn[]
  structured_data?: Record<string, any>
  extraction_confidence?: number
}

// API response types
export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  per_page: number
  has_next: boolean
  has_prev: boolean
}

export interface AgentConfigList {
  configs: AgentConfiguration[]
  total: number
  page: number
  per_page: number
  has_next: boolean
  has_prev: boolean
}

export interface CallList {
  calls: Call[]
  total: number
  page: number
  per_page: number
  has_next: boolean
  has_prev: boolean
}

// Socket.IO event types
export interface CallStatusUpdate {
  call_id: number
  status: CallStatus
  duration?: number
  message?: string
  timestamp: string
}

export interface ConversationUpdate {
  call_id: number
  turn_number: number
  speaker: 'agent' | 'driver'
  message: string
  timestamp: string
  emergency_detected: boolean
  emergency_keywords: string[]
}

export interface EmergencyAlert {
  call_id: number
  driver_name: string
  load_number: string
  phone_number: string
  emergency_keywords: string[]
  message: string
  detected_at: string
}

// Analytics types
export interface CallAnalytics {
  period_days: number
  total_calls: number
  completed_calls: number
  failed_calls: number
  success_rate: number
  average_duration_seconds: number
  call_outcomes: Record<string, number>
  generated_at: string
}

// Form state types
export interface FormState<T> {
  data: T
  errors: Record<string, string>
  isSubmitting: boolean
  isValid: boolean
}

// UI state types
export interface UIState {
  sidebarOpen: boolean
  currentPage: string
  notifications: Notification[]
}

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  read: boolean
}
