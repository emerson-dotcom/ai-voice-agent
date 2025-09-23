// Type definitions for AI Voice Agent

export interface Agent {
  id: string;
  name: string;
  description?: string;
  retell_llm_id?: string;
  retell_agent_id?: string;
  general_prompt: string;
  begin_message?: string;
  voice_id: string;
  voice_model?: string;
  voice_temperature: number;
  voice_speed: number;
  enable_backchannel: boolean;
  backchannel_frequency: number;
  backchannel_words: string[];
  interruption_sensitivity: number;
  responsiveness: number;
  scenario_type: 'driver_checkin' | 'emergency_protocol';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Call {
  id: string;
  retell_call_id?: string;
  retell_access_token?: string;
  agent_id: string;
  agent_version: number;
  driver_name?: string;
  driver_phone?: string;
  load_number?: string;
  call_status: 'registered' | 'ongoing' | 'ended' | 'error';
  start_timestamp?: string;
  end_timestamp?: string;
  duration_ms?: number;
  transcript?: string;
  transcript_object?: any;
  recording_url?: string;
  public_log_url?: string;
  disconnection_reason?: string;
  call_analysis?: any;
  retell_llm_dynamic_variables?: Record<string, any>;
  collected_dynamic_variables?: Record<string, any>;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CallResult {
  id: string;
  call_id: string;
  call_outcome?: 'in_transit_update' | 'arrival_confirmation' | 'emergency_escalation';

  // Driver Check-in Fields
  driver_status?: 'driving' | 'delayed' | 'arrived' | 'unloading';
  current_location?: string;
  eta?: string;
  delay_reason?: string;
  unloading_status?: string;
  pod_reminder_acknowledged?: boolean;

  // Emergency Protocol Fields
  emergency_type?: 'accident' | 'breakdown' | 'medical' | 'other';
  safety_status?: string;
  injury_status?: string;
  emergency_location?: string;
  load_secure?: boolean;
  escalation_status?: string;

  custom_analysis_data?: Record<string, any>;
  confidence_score?: number;
  extracted_at: string;
  extraction_method: string;
}

export interface Load {
  id: string;
  load_number: string;
  origin_location?: string;
  destination_location?: string;
  pickup_date?: string;
  delivery_date?: string;
  assigned_driver_name?: string;
  assigned_driver_phone?: string;
  current_status: string;
  last_updated: string;
  created_at: string;
}

export interface Voice {
  voice_id: string;
  voice_name: string;
  provider: 'elevenlabs' | 'openai' | 'deepgram';
  accent?: string;
  gender: 'male' | 'female';
  age?: string;
  preview_audio_url?: string;
}

// Form types
export interface AgentFormData {
  name: string;
  description?: string;
  general_prompt: string;
  begin_message?: string;
  voice_id: string;
  voice_model?: string;
  voice_temperature: number;
  voice_speed: number;
  enable_backchannel: boolean;
  backchannel_frequency: number;
  backchannel_words: string[];
  interruption_sensitivity: number;
  responsiveness: number;
  scenario_type: 'driver_checkin' | 'emergency_protocol';
  system_prompt?: string;
  greeting_message?: string;
  initial_message?: string;
  fallback_message?: string;
  end_call_message?: string;
  enable_transcription?: boolean;
  response_delay_ms?: number;
  temperature?: number;
  max_tokens?: number;
}

export interface CallFormData {
  agent_id: string;
  driver_name: string;
  load_number: string;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  count: number;
  page: number;
  limit: number;
  total_pages: number;
}