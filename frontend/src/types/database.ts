/**
 * Database type definitions for Supabase tables.
 * Generated based on the database schema.
 */

export interface Database {
  public: {
    Tables: {
      agents: {
        Row: {
          id: string;
          name: string;
          description: string | null;
          retell_llm_id: string | null;
          retell_agent_id: string | null;
          general_prompt: string;
          begin_message: string | null;
          voice_id: string;
          voice_model: string | null;
          voice_temperature: number;
          voice_speed: number;
          enable_backchannel: boolean;
          backchannel_frequency: number;
          backchannel_words: string[];
          interruption_sensitivity: number;
          responsiveness: number;
          scenario_type: string;
          is_active: boolean;
          created_at: string;
          updated_at: string;
          created_by: string | null;
        };
        Insert: {
          id?: string;
          name: string;
          description?: string | null;
          retell_llm_id?: string | null;
          retell_agent_id?: string | null;
          general_prompt: string;
          begin_message?: string | null;
          voice_id: string;
          voice_model?: string | null;
          voice_temperature?: number;
          voice_speed?: number;
          enable_backchannel?: boolean;
          backchannel_frequency?: number;
          backchannel_words?: string[];
          interruption_sensitivity?: number;
          responsiveness?: number;
          scenario_type: string;
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
          created_by?: string | null;
        };
        Update: {
          id?: string;
          name?: string;
          description?: string | null;
          retell_llm_id?: string | null;
          retell_agent_id?: string | null;
          general_prompt?: string;
          begin_message?: string | null;
          voice_id?: string;
          voice_model?: string | null;
          voice_temperature?: number;
          voice_speed?: number;
          enable_backchannel?: boolean;
          backchannel_frequency?: number;
          backchannel_words?: string[];
          interruption_sensitivity?: number;
          responsiveness?: number;
          scenario_type?: string;
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
          created_by?: string | null;
        };
      };
      calls: {
        Row: {
          id: string;
          retell_call_id: string | null;
          retell_access_token: string | null;
          agent_id: string | null;
          agent_version: number;
          driver_name: string | null;
          driver_phone: string | null;
          load_number: string | null;
          call_status: string;
          start_timestamp: string | null;
          end_timestamp: string | null;
          duration_ms: number | null;
          transcript: string | null;
          transcript_object: any | null;
          recording_url: string | null;
          public_log_url: string | null;
          disconnection_reason: string | null;
          call_analysis: any | null;
          retell_llm_dynamic_variables: any | null;
          collected_dynamic_variables: any | null;
          metadata: any | null;
          created_at: string;
          updated_at: string;
          created_by: string | null;
        };
        Insert: {
          id?: string;
          retell_call_id?: string | null;
          retell_access_token?: string | null;
          agent_id?: string | null;
          agent_version?: number;
          driver_name?: string | null;
          driver_phone?: string | null;
          load_number?: string | null;
          call_status?: string;
          start_timestamp?: string | null;
          end_timestamp?: string | null;
          duration_ms?: number | null;
          transcript?: string | null;
          transcript_object?: any | null;
          recording_url?: string | null;
          public_log_url?: string | null;
          disconnection_reason?: string | null;
          call_analysis?: any | null;
          retell_llm_dynamic_variables?: any | null;
          collected_dynamic_variables?: any | null;
          metadata?: any | null;
          created_at?: string;
          updated_at?: string;
          created_by?: string | null;
        };
        Update: {
          id?: string;
          retell_call_id?: string | null;
          retell_access_token?: string | null;
          agent_id?: string | null;
          agent_version?: number;
          driver_name?: string | null;
          driver_phone?: string | null;
          load_number?: string | null;
          call_status?: string;
          start_timestamp?: string | null;
          end_timestamp?: string | null;
          duration_ms?: number | null;
          transcript?: string | null;
          transcript_object?: any | null;
          recording_url?: string | null;
          public_log_url?: string | null;
          disconnection_reason?: string | null;
          call_analysis?: any | null;
          retell_llm_dynamic_variables?: any | null;
          collected_dynamic_variables?: any | null;
          metadata?: any | null;
          created_at?: string;
          updated_at?: string;
          created_by?: string | null;
        };
      };
      call_results: {
        Row: {
          id: string;
          call_id: string;
          call_outcome: string | null;
          driver_status: string | null;
          current_location: string | null;
          eta: string | null;
          delay_reason: string | null;
          unloading_status: string | null;
          pod_reminder_acknowledged: boolean | null;
          emergency_type: string | null;
          safety_status: string | null;
          injury_status: string | null;
          emergency_location: string | null;
          load_secure: boolean | null;
          escalation_status: string | null;
          custom_analysis_data: any | null;
          confidence_score: number | null;
          extracted_at: string;
          extraction_method: string;
        };
        Insert: {
          id?: string;
          call_id: string;
          call_outcome?: string | null;
          driver_status?: string | null;
          current_location?: string | null;
          eta?: string | null;
          delay_reason?: string | null;
          unloading_status?: string | null;
          pod_reminder_acknowledged?: boolean | null;
          emergency_type?: string | null;
          safety_status?: string | null;
          injury_status?: string | null;
          emergency_location?: string | null;
          load_secure?: boolean | null;
          escalation_status?: string | null;
          custom_analysis_data?: any | null;
          confidence_score?: number | null;
          extracted_at?: string;
          extraction_method?: string;
        };
        Update: {
          id?: string;
          call_id?: string;
          call_outcome?: string | null;
          driver_status?: string | null;
          current_location?: string | null;
          eta?: string | null;
          delay_reason?: string | null;
          unloading_status?: string | null;
          pod_reminder_acknowledged?: boolean | null;
          emergency_type?: string | null;
          safety_status?: string | null;
          injury_status?: string | null;
          emergency_location?: string | null;
          load_secure?: boolean | null;
          escalation_status?: string | null;
          custom_analysis_data?: any | null;
          confidence_score?: number | null;
          extracted_at?: string;
          extraction_method?: string;
        };
      };
      loads: {
        Row: {
          id: string;
          load_number: string;
          origin_location: string | null;
          destination_location: string | null;
          pickup_date: string | null;
          delivery_date: string | null;
          assigned_driver_name: string | null;
          assigned_driver_phone: string | null;
          current_status: string;
          last_updated: string;
          created_at: string;
          created_by: string | null;
        };
        Insert: {
          id?: string;
          load_number: string;
          origin_location?: string | null;
          destination_location?: string | null;
          pickup_date?: string | null;
          delivery_date?: string | null;
          assigned_driver_name?: string | null;
          assigned_driver_phone?: string | null;
          current_status?: string;
          last_updated?: string;
          created_at?: string;
          created_by?: string | null;
        };
        Update: {
          id?: string;
          load_number?: string;
          origin_location?: string | null;
          destination_location?: string | null;
          pickup_date?: string | null;
          delivery_date?: string | null;
          assigned_driver_name?: string | null;
          assigned_driver_phone?: string | null;
          current_status?: string;
          last_updated?: string;
          created_at?: string;
          created_by?: string | null;
        };
      };
      agent_states: {
        Row: {
          id: string;
          agent_id: string;
          name: string;
          state_prompt: string;
          is_starting_state: boolean;
          created_at: string;
        };
        Insert: {
          id?: string;
          agent_id: string;
          name: string;
          state_prompt: string;
          is_starting_state?: boolean;
          created_at?: string;
        };
        Update: {
          id?: string;
          agent_id?: string;
          name?: string;
          state_prompt?: string;
          is_starting_state?: boolean;
          created_at?: string;
        };
      };
      agent_tools: {
        Row: {
          id: string;
          agent_id: string;
          state_id: string | null;
          tool_type: string;
          tool_name: string;
          tool_description: string;
          tool_config: any;
          created_at: string;
        };
        Insert: {
          id?: string;
          agent_id: string;
          state_id?: string | null;
          tool_type: string;
          tool_name: string;
          tool_description: string;
          tool_config?: any;
          created_at?: string;
        };
        Update: {
          id?: string;
          agent_id?: string;
          state_id?: string | null;
          tool_type?: string;
          tool_name?: string;
          tool_description?: string;
          tool_config?: any;
          created_at?: string;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      call_status: 'registered' | 'ongoing' | 'ended' | 'error';
      call_outcome: 'in_transit_update' | 'arrival_confirmation' | 'emergency_escalation';
      driver_status: 'driving' | 'delayed' | 'arrived' | 'unloading';
      emergency_type: 'accident' | 'breakdown' | 'medical' | 'other';
    };
  };
}