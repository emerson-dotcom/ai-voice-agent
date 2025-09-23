'use client'

import { useState, useEffect } from 'react'
import CallForm from '@/components/call-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Phone, Settings } from 'lucide-react'
import { Agent } from '@/types'
import { AuthGuard } from '@/components/AuthGuard'
import { Header } from '@/components/Header'
import { agentApi } from '@/lib/api'

export default function CallsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  // Fetch agents on component mount
  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    try {
      const agentsData = await agentApi.list()
      setAgents(agentsData.filter((agent: Agent) => agent.is_active))
    } catch (error) {
      console.error('Error fetching agents:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthGuard>
      <Header />
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">
            Start Call
          </h1>
          <p className="text-xl text-slate-600">
            Configure and start calls with AI voice agents for logistics testing
          </p>
        </div>

        {/* Single Column - Call Configuration */}
        <div className="max-w-2xl mx-auto">
          <CallForm
            agents={agents}
            loads={[]}
            isLoading={loading}
          />
        </div>
      </div>
    </div>
    </AuthGuard>
  )
}