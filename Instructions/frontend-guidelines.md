# AI Voice Agent - Frontend Guidelines

## Overview
This document outlines the frontend architecture, component structure, and development guidelines for the AI Voice Agent Tool built with Next.js 14+ using the App Router.

## Technology Stack

### Core Technologies
- **Next.js 14+** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Headless UI** for accessible components
- **Zustand** for state management
- **React Hook Form** for form handling
- **Zod** for schema validation

### Additional Libraries
- **@tanstack/react-query** for server state management
- **socket.io-client** for real-time updates
- **react-hot-toast** for notifications
- **lucide-react** for icons
- **date-fns** for date manipulation

## Project Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── globals.css            # Global styles
│   ├── layout.tsx             # Root layout
│   ├── page.tsx               # Home page
│   ├── loading.tsx            # Global loading UI
│   ├── error.tsx              # Global error UI
│   │
│   ├── (auth)/                # Auth route group
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   │
│   ├── dashboard/             # Main dashboard
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   ├── agents/            # Agent configuration
│   │   │   ├── page.tsx
│   │   │   ├── new/
│   │   │   │   └── page.tsx
│   │   │   └── [id]/
│   │   │       ├── page.tsx
│   │   │       └── edit/
│   │   │           └── page.tsx
│   │   ├── calls/             # Call management
│   │   │   ├── page.tsx
│   │   │   ├── new/
│   │   │   │   └── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   └── results/           # Call results
│   │       ├── page.tsx
│   │       └── [id]/
│   │           └── page.tsx
│   │
│   └── api/                   # API routes (if needed)
│       └── auth/
│           └── route.ts
│
├── components/                # Reusable components
│   ├── ui/                    # Base UI components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── modal.tsx
│   │   ├── card.tsx
│   │   └── index.ts
│   │
│   ├── layout/                # Layout components
│   │   ├── header.tsx
│   │   ├── sidebar.tsx
│   │   ├── navigation.tsx
│   │   └── dashboard-layout.tsx
│   │
│   ├── forms/                 # Form components
│   │   ├── agent-config-form.tsx
│   │   ├── call-initiation-form.tsx
│   │   └── voice-settings-form.tsx
│   │
│   ├── features/              # Feature-specific components
│   │   ├── agent-configuration/
│   │   │   ├── agent-list.tsx
│   │   │   ├── agent-card.tsx
│   │   │   ├── prompt-editor.tsx
│   │   │   └── voice-settings.tsx
│   │   ├── call-management/
│   │   │   ├── call-dashboard.tsx
│   │   │   ├── call-status.tsx
│   │   │   └── active-calls.tsx
│   │   └── results/
│   │       ├── structured-data-display.tsx
│   │       ├── transcript-viewer.tsx
│   │       └── call-summary.tsx
│   │
│   └── common/                # Common components
│       ├── loading-spinner.tsx
│       ├── error-boundary.tsx
│       ├── confirmation-dialog.tsx
│       └── real-time-status.tsx
│
├── lib/                       # Utility libraries
│   ├── api.ts                 # API client configuration
│   ├── auth.ts                # Authentication utilities
│   ├── socket.ts              # Socket.io client setup
│   ├── utils.ts               # General utilities
│   ├── validations.ts         # Zod schemas
│   └── constants.ts           # App constants
│
├── hooks/                     # Custom React hooks
│   ├── use-auth.ts
│   ├── use-socket.ts
│   ├── use-api.ts
│   └── use-call-status.ts
│
├── store/                     # Zustand stores
│   ├── auth-store.ts
│   ├── call-store.ts
│   └── ui-store.ts
│
├── types/                     # TypeScript type definitions
│   ├── api.ts
│   ├── agent.ts
│   ├── call.ts
│   └── user.ts
│
└── styles/                    # Additional styles
    ├── components.css
    └── utilities.css
```

## Component Architecture

### 1. Base UI Components (`components/ui/`)

#### Button Component
```typescript
// components/ui/button.tsx
import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

### 2. Layout Components

#### Dashboard Layout
```typescript
// components/layout/dashboard-layout.tsx
'use client'

import { ReactNode } from 'react'
import { Header } from './header'
import { Sidebar } from './sidebar'
import { useAuth } from '@/hooks/use-auth'
import { redirect } from 'next/navigation'

interface DashboardLayoutProps {
  children: ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
```

### 3. Feature Components

#### Agent Configuration Form
```typescript
// components/features/agent-configuration/agent-config-form.tsx
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { agentConfigSchema, type AgentConfigFormData } from '@/lib/validations'
import { VoiceSettings } from './voice-settings'
import { PromptEditor } from './prompt-editor'

interface AgentConfigFormProps {
  initialData?: Partial<AgentConfigFormData>
  onSubmit: (data: AgentConfigFormData) => Promise<void>
  isLoading?: boolean
}

export function AgentConfigForm({ initialData, onSubmit, isLoading }: AgentConfigFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<AgentConfigFormData>({
    resolver: zodResolver(agentConfigSchema),
    defaultValues: initialData,
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium mb-2">Configuration Name</label>
          <Input
            {...register('name')}
            placeholder="Enter configuration name"
            error={errors.name?.message}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Scenario Type</label>
          <select
            {...register('scenarioType')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="check_in">Driver Check-in</option>
            <option value="emergency">Emergency Protocol</option>
          </select>
        </div>
      </div>

      <PromptEditor control={control} />
      
      <VoiceSettings control={control} />

      <div className="flex justify-end space-x-4">
        <Button type="button" variant="outline">
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>
    </form>
  )
}
```

#### Call Status Component
```typescript
// components/features/call-management/call-status.tsx
'use client'

import { useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { useSocket } from '@/hooks/use-socket'
import { useCallStore } from '@/store/call-store'
import { CallStatus as CallStatusType } from '@/types/call'

interface CallStatusProps {
  callId: string
}

export function CallStatus({ callId }: CallStatusProps) {
  const socket = useSocket()
  const { calls, updateCallStatus } = useCallStore()
  const call = calls.find(c => c.id === callId)

  useEffect(() => {
    if (socket) {
      socket.on(`call-${callId}-status`, (status: CallStatusType) => {
        updateCallStatus(callId, status)
      })

      return () => {
        socket.off(`call-${callId}-status`)
      }
    }
  }, [socket, callId, updateCallStatus])

  if (!call) return null

  const getStatusColor = (status: CallStatusType) => {
    switch (status) {
      case 'initiated': return 'blue'
      case 'in_progress': return 'yellow'
      case 'completed': return 'green'
      case 'failed': return 'red'
      default: return 'gray'
    }
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Call Status</h3>
        <Badge variant={getStatusColor(call.status)}>
          {call.status.replace('_', ' ').toUpperCase()}
        </Badge>
      </div>
      
      <div className="space-y-2 text-sm">
        <div><strong>Driver:</strong> {call.driverName}</div>
        <div><strong>Phone:</strong> {call.phoneNumber}</div>
        <div><strong>Load:</strong> {call.loadNumber}</div>
        {call.duration && (
          <div><strong>Duration:</strong> {Math.floor(call.duration / 60)}m {call.duration % 60}s</div>
        )}
      </div>
    </Card>
  )
}
```

## State Management

### Zustand Store Example
```typescript
// store/call-store.ts
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { Call, CallStatus } from '@/types/call'

interface CallStore {
  calls: Call[]
  activeCalls: Call[]
  isLoading: boolean
  error: string | null
  
  // Actions
  setCalls: (calls: Call[]) => void
  addCall: (call: Call) => void
  updateCallStatus: (callId: string, status: CallStatus) => void
  removeCall: (callId: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useCallStore = create<CallStore>()(
  devtools(
    (set, get) => ({
      calls: [],
      activeCalls: [],
      isLoading: false,
      error: null,

      setCalls: (calls) => set({ calls }),
      
      addCall: (call) => set((state) => ({ 
        calls: [...state.calls, call],
        activeCalls: call.status === 'in_progress' 
          ? [...state.activeCalls, call] 
          : state.activeCalls
      })),

      updateCallStatus: (callId, status) => set((state) => ({
        calls: state.calls.map(call => 
          call.id === callId ? { ...call, status } : call
        ),
        activeCalls: status === 'in_progress'
          ? state.activeCalls.map(call => 
              call.id === callId ? { ...call, status } : call
            )
          : state.activeCalls.filter(call => call.id !== callId)
      })),

      removeCall: (callId) => set((state) => ({
        calls: state.calls.filter(call => call.id !== callId),
        activeCalls: state.activeCalls.filter(call => call.id !== callId)
      })),

      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error })
    }),
    { name: 'call-store' }
  )
)
```

## Custom Hooks

### API Hook
```typescript
// hooks/use-api.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { AgentConfig, Call } from '@/types'

export function useAgentConfigs() {
  return useQuery({
    queryKey: ['agent-configs'],
    queryFn: () => api.get('/agents'),
  })
}

export function useCreateAgentConfig() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: Partial<AgentConfig>) => api.post('/agents', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-configs'] })
    },
  })
}

export function useInitiateCall() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: { driverName: string; phoneNumber: string; loadNumber: string; agentConfigId: string }) => 
      api.post('/calls/initiate', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calls'] })
    },
  })
}
```

### Socket Hook
```typescript
// hooks/use-socket.ts
import { useEffect, useState } from 'react'
import { io, Socket } from 'socket.io-client'
import { useAuth } from './use-auth'

export function useSocket() {
  const [socket, setSocket] = useState<Socket | null>(null)
  const { user } = useAuth()

  useEffect(() => {
    if (user) {
      const socketInstance = io(process.env.NEXT_PUBLIC_SOCKET_URL!, {
        auth: {
          token: user.token,
        },
      })

      setSocket(socketInstance)

      return () => {
        socketInstance.close()
      }
    }
  }, [user])

  return socket
}
```

## Validation Schemas

```typescript
// lib/validations.ts
import { z } from 'zod'

export const agentConfigSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  scenarioType: z.enum(['check_in', 'emergency']),
  prompts: z.object({
    opening: z.string().min(1, 'Opening prompt is required'),
    followUp: z.string().min(1, 'Follow-up prompt is required'),
    closing: z.string().min(1, 'Closing prompt is required'),
  }),
  voiceSettings: z.object({
    backchanneling: z.boolean(),
    fillerWords: z.boolean(),
    interruptionSensitivity: z.number().min(0).max(1),
    speed: z.number().min(0.5).max(2),
  }),
})

export const callInitiationSchema = z.object({
  driverName: z.string().min(1, 'Driver name is required'),
  phoneNumber: z.string().regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number'),
  loadNumber: z.string().min(1, 'Load number is required'),
  agentConfigId: z.string().min(1, 'Agent configuration is required'),
})

export type AgentConfigFormData = z.infer<typeof agentConfigSchema>
export type CallInitiationFormData = z.infer<typeof callInitiationSchema>
```

## Styling Guidelines

### Tailwind CSS Configuration
```javascript
// tailwind.config.js
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          600: '#d97706',
        },
        danger: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

### Component Styling Patterns
```typescript
// Use consistent spacing and sizing
const containerClasses = "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
const cardClasses = "bg-white rounded-lg shadow-sm border border-gray-200 p-6"
const buttonClasses = "inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md"

// Use semantic color classes
const statusColors = {
  success: "text-green-800 bg-green-100",
  warning: "text-yellow-800 bg-yellow-100", 
  error: "text-red-800 bg-red-100",
  info: "text-blue-800 bg-blue-100",
}
```

## Performance Guidelines

### Code Splitting
```typescript
// Lazy load heavy components
import { lazy, Suspense } from 'react'

const TranscriptViewer = lazy(() => import('./transcript-viewer'))

function CallResults() {
  return (
    <Suspense fallback={<div>Loading transcript...</div>}>
      <TranscriptViewer />
    </Suspense>
  )
}
```

### Memoization
```typescript
// Memoize expensive calculations
import { useMemo } from 'react'

function CallAnalytics({ calls }) {
  const analytics = useMemo(() => {
    return calculateAnalytics(calls)
  }, [calls])

  return <div>{analytics}</div>
}
```

## Accessibility Guidelines

### ARIA Labels and Roles
```typescript
<button
  aria-label="Start voice call"
  aria-describedby="call-help-text"
  disabled={isLoading}
>
  {isLoading ? 'Starting...' : 'Start Call'}
</button>

<div id="call-help-text" className="sr-only">
  This will initiate a voice call to the specified driver
</div>
```

### Keyboard Navigation
```typescript
// Ensure all interactive elements are keyboard accessible
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick()
    }
  }}
  onClick={handleClick}
>
  Interactive Element
</div>
```

## Testing Guidelines

### Component Testing
```typescript
// __tests__/components/call-status.test.tsx
import { render, screen } from '@testing-library/react'
import { CallStatus } from '@/components/features/call-management/call-status'

describe('CallStatus', () => {
  it('displays call information correctly', () => {
    render(<CallStatus callId="123" />)
    
    expect(screen.getByText('Call Status')).toBeInTheDocument()
    expect(screen.getByText('IN PROGRESS')).toBeInTheDocument()
  })

  it('updates status in real-time', async () => {
    // Test real-time updates
  })
})
```

### Integration Testing
```typescript
// Test complete user flows
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CallInitiationForm } from '@/components/forms/call-initiation-form'

describe('Call Initiation Flow', () => {
  it('successfully initiates a call', async () => {
    render(<CallInitiationForm />)
    
    fireEvent.change(screen.getByLabelText('Driver Name'), {
      target: { value: 'John Doe' }
    })
    
    fireEvent.click(screen.getByText('Start Call'))
    
    await waitFor(() => {
      expect(screen.getByText('Call initiated successfully')).toBeInTheDocument()
    })
  })
})
```

## Build and Deployment

### Next.js Configuration
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_SOCKET_URL: process.env.NEXT_PUBLIC_SOCKET_URL,
  },
  images: {
    domains: ['example.com'],
  },
}

module.exports = nextConfig
```

### Environment Variables
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOCKET_URL=http://localhost:8000
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=http://localhost:3000
```
