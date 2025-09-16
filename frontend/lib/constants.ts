export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
export const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:8000'

export const CALL_STATUSES = {
  INITIATED: 'initiated',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const

export const CALL_OUTCOMES = {
  IN_TRANSIT_UPDATE: 'In-Transit Update',
  ARRIVAL_CONFIRMATION: 'Arrival Confirmation',
  EMERGENCY_ESCALATION: 'Emergency Escalation',
} as const

export const DRIVER_STATUSES = {
  DRIVING: 'Driving',
  DELAYED: 'Delayed',
  ARRIVED: 'Arrived',
  UNLOADING: 'Unloading',
} as const

export const EMERGENCY_TYPES = {
  ACCIDENT: 'Accident',
  BREAKDOWN: 'Breakdown',
  MEDICAL: 'Medical',
  OTHER: 'Other',
} as const

export const SCENARIO_TYPES = {
  CHECK_IN: 'check_in',
  EMERGENCY: 'emergency',
} as const

export const DEFAULT_VOICE_SETTINGS = {
  backchanneling: true,
  filler_words: true,
  interruption_sensitivity: 0.5,
  voice_speed: 1.0,
  voice_temperature: 0.7,
  responsiveness: 1.0,
}

export const DEFAULT_CONVERSATION_FLOW = {
  max_turns: 20,
  timeout_seconds: 120,
  retry_attempts: 3,
  emergency_keywords: [
    'emergency',
    'accident',
    'blowout',
    'medical',
    'breakdown',
    'crash',
    'injured'
  ],
  data_extraction_points: [],
}

export const NAVIGATION_ITEMS = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: 'LayoutDashboard',
  },
  {
    name: 'Agent Configuration',
    href: '/dashboard/agents',
    icon: 'Settings',
  },
  {
    name: 'Call Management',
    href: '/dashboard/calls',
    icon: 'Phone',
  },
  {
    name: 'Results & Analytics',
    href: '/dashboard/results',
    icon: 'BarChart3',
  },
]
