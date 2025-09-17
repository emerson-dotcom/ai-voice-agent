import { API_BASE_URL } from './constants'

class ApiClient {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL: string) {
    this.baseURL = baseURL
    
    // Get token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token')
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    // Handle 204 No Content responses (like DELETE operations)
    if (response.status === 204) {
      return undefined as T
    }

    // For responses with content, parse as JSON
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return response.json()
    }

    // If no JSON content, return undefined
    return undefined as T
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  // Authentication endpoints
  async login(email: string, password: string) {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)

    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || 'Login failed')
    }

    const data = await response.json()
    this.setToken(data.access_token)
    return data
  }

  async register(email: string, password: string, fullName?: string) {
    return this.post<import('@/types').User>('/api/v1/auth/register', {
      email,
      password,
      full_name: fullName,
    })
  }

  // Agent configuration endpoints
  async getAgentConfigs(params?: {
    page?: number
    per_page?: number
    scenario_type?: string
    is_active?: boolean
  }) {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const endpoint = `/api/v1/agents${searchParams.toString() ? `?${searchParams.toString()}` : ''}`
    return this.get<import('@/types').AgentConfigList>(endpoint)
  }

  async createAgentConfig(data: unknown) {
    return this.post<import('@/types').AgentConfiguration>('/api/v1/agents', data)
  }

  async getAgentConfig(id: number) {
    return this.get<import('@/types').AgentConfiguration>(`/api/v1/agents/${id}`)
  }

  async updateAgentConfig(id: number, data: unknown) {
    return this.put<import('@/types').AgentConfiguration>(`/api/v1/agents/${id}`, data)
  }

  async deleteAgentConfig(id: number) {
    return this.delete(`/api/v1/agents/${id}`)
  }

  async deployAgentConfig(id: number, deploy: boolean = true) {
    return this.post<import('@/types').AgentConfiguration>(`/api/v1/agents/${id}/deploy?deploy=${deploy}`)
  }

  async testAgentConfig(id: number, testPhone: string) {
    return this.post(`/api/v1/agents/${id}/test?test_phone=${encodeURIComponent(testPhone)}`)
  }

  // Call management endpoints
  async initializeCall(data: {
    driver_name: string
    phone_number?: string
    load_number: string
    agent_config_id: number
    call_type?: 'phone_call' | 'web_call'
  }) {
    return this.post<import('@/types').Call>('/api/v1/calls/initiate', data)
  }

  async getCalls(params?: {
    page?: number
    per_page?: number
    status_filter?: string
    driver_name?: string
    load_number?: string
  }) {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const endpoint = `/api/v1/calls${searchParams.toString() ? `?${searchParams.toString()}` : ''}`
    return this.get<import('@/types').CallList>(endpoint)
  }

  async getActiveCalls() {
    return this.get<import('@/types').Call[]>('/api/v1/calls/active')
  }

  async getCallDetails(id: number) {
    return this.get<import('@/types').CallDetail>(`/api/v1/calls/${id}`)
  }

  async getCallTranscript(id: number) {
    return this.get<import('@/types').Transcript>(`/api/v1/calls/${id}/transcript`)
  }

  async cancelCall(id: number) {
    return this.post<import('@/types').Call>(`/api/v1/calls/${id}/cancel`)
  }

  async retryCall(id: number) {
    return this.post<import('@/types').Call>(`/api/v1/calls/${id}/retry`)
  }

  async getCallStatus(id: number) {
    return this.get(`/api/v1/calls/${id}/status`)
  }

  async getAnalytics(days: number = 7) {
    return this.get<import('@/types').CallAnalytics>(`/api/v1/calls/analytics/summary?days=${days}`)
  }
}

export const api = new ApiClient(API_BASE_URL)
