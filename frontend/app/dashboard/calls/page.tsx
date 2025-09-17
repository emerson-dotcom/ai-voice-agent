'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { useCalls, useActiveCalls, useInitiateCall, useCancelCall } from '@/hooks/use-calls'
import { useAgentConfigs } from '@/hooks/use-agents'
import type { Call, AgentConfiguration, CallList, AgentConfigList } from '@/types'
import { format } from 'date-fns'
import { 
  Phone, 
  Plus, 
  Search, 
  PhoneCall,
  PhoneOff,
  Clock,
  CheckCircle,
  XCircle,
  Eye,
  PlayCircle,
  StopCircle,
  User,
  Truck,
  Globe
} from 'lucide-react'

export default function CallManagementPage() {
  const { data: callHistoryData, isLoading: historyLoading } = useCalls()
  const { data: activeCallsData, isLoading: activeLoading } = useActiveCalls()
  const { data: agentData } = useAgentConfigs()
  
  // Extract the actual arrays from the API response
  const callHistory: Call[] = (callHistoryData as CallList)?.calls || []
  const activeCalls: Call[] = (activeCallsData as Call[]) || []
  const agentConfigs: AgentConfiguration[] = (agentData as AgentConfigList)?.configs || []
  const cancelCall = useCancelCall()
  
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showNewCallForm, setShowNewCallForm] = useState(false)

  const filteredCalls = callHistory.filter(call => {
    const matchesSearch = !searchTerm || 
      call.driver_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      call.phone_number.includes(searchTerm) ||
      call.load_number.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = statusFilter === 'all' || call.status === statusFilter
    
    return matchesSearch && matchesStatus
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'initiated':
        return <Badge className="bg-blue-100 text-blue-800"><Clock className="h-3 w-3 mr-1" />Initiated</Badge>
      case 'in_progress':
        return <Badge className="bg-yellow-100 text-yellow-800"><PhoneCall className="h-3 w-3 mr-1" />In Progress</Badge>
      case 'completed':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Completed</Badge>
      case 'failed':
        return <Badge className="bg-red-100 text-red-800"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>
      case 'cancelled':
        return <Badge className="bg-gray-100 text-gray-800"><PhoneOff className="h-3 w-3 mr-1" />Cancelled</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const handleCancelCall = async (callId: number) => {
    if (confirm('Are you sure you want to cancel this call?')) {
      await cancelCall.mutateAsync(callId)
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (historyLoading || activeLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Call Management</h1>
            <p className="text-gray-600">Monitor and manage voice calls to drivers</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Call Management</h1>
          <p className="text-gray-600">Monitor and manage voice calls to drivers</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/calls/new">
            <Plus className="h-4 w-4 mr-2" />
            Start New Call
          </Link>
        </Button>
      </div>

      {/* Active Calls */}
      {activeCalls.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <PhoneCall className="h-5 w-5 mr-2 text-green-500" />
              Active Calls ({activeCalls.length})
            </CardTitle>
            <CardDescription>
              Calls currently in progress
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {activeCalls.map((call) => (
                <div key={call.id} className="flex items-center justify-between p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    </div>
                    <div>
                      <div className="font-medium">{call.driver_name}</div>
                      <div className="text-sm text-gray-600">{call.phone_number} • Load #{call.load_number}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    {call.duration && (
                      <div className="text-sm font-mono text-gray-600">
                        {formatDuration(call.duration)}
                      </div>
                    )}
                    {getStatusBadge(call.status)}
                    <div className="flex space-x-2">
                      {call.conversation_metadata?.web_call_url && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => window.open(call.conversation_metadata?.web_call_url, '_blank')}
                          title="Open web call"
                        >
                          <Globe className="h-4 w-4" />
                        </Button>
                      )}
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/dashboard/calls/${call.id}`}>
                          <Eye className="h-4 w-4" />
                        </Link>
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleCancelCall(call.id)}
                        disabled={cancelCall.isPending}
                      >
                        <StopCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* New Call Form */}
      {showNewCallForm && (
        <Card>
          <CardHeader>
            <CardTitle>Start New Call</CardTitle>
            <CardDescription>
              Enter driver details to initiate a voice call
            </CardDescription>
          </CardHeader>
          <CardContent>
            <NewCallForm 
              agentConfigs={agentConfigs}
              onClose={() => setShowNewCallForm(false)}
            />
          </CardContent>
        </Card>
      )}

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by driver name, phone, or load number..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex space-x-2">
              <Button
                variant={statusFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('all')}
              >
                All
              </Button>
              <Button
                variant={statusFilter === 'completed' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('completed')}
              >
                Completed
              </Button>
              <Button
                variant={statusFilter === 'failed' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('failed')}
              >
                Failed
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Call History */}
      <Card>
        <CardHeader>
          <CardTitle>Call History</CardTitle>
          <CardDescription>
            Recent voice calls and their outcomes
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredCalls.length === 0 ? (
            <div className="text-center py-12">
              <Phone className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Calls Found</h3>
              <p className="text-gray-600 mb-4">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filters.'
                  : 'Start your first call to see it here.'}
              </p>
              {!searchTerm && statusFilter === 'all' && (
                <Button onClick={() => setShowNewCallForm(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Start First Call
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredCalls.map((call) => (
                <div key={call.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {call.status === 'completed' ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : call.status === 'failed' ? (
                        <XCircle className="h-5 w-5 text-red-500" />
                      ) : (
                        <Clock className="h-5 w-5 text-yellow-500" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div>
                          <div className="font-medium flex items-center">
                            <User className="h-4 w-4 mr-1" />
                            {call.driver_name}
                          </div>
                          <div className="text-sm text-gray-600 flex items-center space-x-4">
                            <span className="flex items-center">
                              <Phone className="h-3 w-3 mr-1" />
                              {call.phone_number}
                            </span>
                            <span className="flex items-center">
                              <Truck className="h-3 w-3 mr-1" />
                              Load #{call.load_number}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-sm text-gray-600">
                        {format(new Date(call.created_at), 'MMM d, HH:mm')}
                      </div>
                      {call.duration && (
                        <div className="text-sm font-mono text-gray-500">
                          {formatDuration(call.duration)}
                        </div>
                      )}
                    </div>
                    {getStatusBadge(call.status)}
                    <div className="flex space-x-2">
                      {call.conversation_metadata?.web_call_url && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => window.open(call.conversation_metadata?.web_call_url, '_blank')}
                          title="Open web call"
                        >
                          <Globe className="h-4 w-4" />
                        </Button>
                      )}
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/dashboard/calls/${call.id}`}>
                          <Eye className="h-4 w-4" />
                        </Link>
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// New Call Form Component
function NewCallForm({ agentConfigs, onClose }: { agentConfigs: AgentConfiguration[], onClose: () => void }) {
  const [formData, setFormData] = useState({
    driverName: '',
    phoneNumber: '',
    loadNumber: '',
    agentConfigId: '',
    callType: 'phone_call'
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  
  const initiateCall = useInitiateCall()

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    
    if (!formData.driverName.trim()) {
      newErrors.driverName = 'Driver name is required'
    }
    
    if (!formData.phoneNumber.trim()) {
      newErrors.phoneNumber = 'Phone number is required'
    } else if (!/^\+?[1-9]\d{1,14}$/.test(formData.phoneNumber.replace(/[\s-()]/g, ''))) {
      newErrors.phoneNumber = 'Invalid phone number format'
    }
    
    if (!formData.loadNumber.trim()) {
      newErrors.loadNumber = 'Load number is required'
    }
    
    if (!formData.agentConfigId) {
      newErrors.agentConfigId = 'Agent configuration is required'
    }
    
    if (!formData.callType) {
      newErrors.callType = 'Call type is required'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return

    try {
      await initiateCall.mutateAsync({
        driver_name: formData.driverName,
        phone_number: formData.phoneNumber,
        load_number: formData.loadNumber,
        agent_config_id: parseInt(formData.agentConfigId),
        call_type: formData.callType
      })
      onClose()
    } catch (error) {
      console.error('Failed to initiate call:', error)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Driver Name</label>
          <Input
            value={formData.driverName}
            onChange={(e) => setFormData(prev => ({ ...prev, driverName: e.target.value }))}
            placeholder="Enter driver's full name"
            className={errors.driverName ? 'border-red-500' : ''}
          />
          {errors.driverName && <p className="text-sm text-red-600 mt-1">{errors.driverName}</p>}
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">Phone Number</label>
          <Input
            value={formData.phoneNumber}
            onChange={(e) => setFormData(prev => ({ ...prev, phoneNumber: e.target.value }))}
            placeholder="+1 (555) 123-4567"
            className={errors.phoneNumber ? 'border-red-500' : ''}
          />
          {errors.phoneNumber && <p className="text-sm text-red-600 mt-1">{errors.phoneNumber}</p>}
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">Load Number</label>
          <Input
            value={formData.loadNumber}
            onChange={(e) => setFormData(prev => ({ ...prev, loadNumber: e.target.value }))}
            placeholder="7891-B"
            className={errors.loadNumber ? 'border-red-500' : ''}
          />
          {errors.loadNumber && <p className="text-sm text-red-600 mt-1">{errors.loadNumber}</p>}
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">Agent Configuration</label>
          <select
            value={formData.agentConfigId}
            onChange={(e) => setFormData(prev => ({ ...prev, agentConfigId: e.target.value }))}
            className={`w-full px-3 py-2 border rounded-md ${errors.agentConfigId ? 'border-red-500' : 'border-gray-300'}`}
          >
            <option value="">Select an agent configuration...</option>
            {agentConfigs.filter(config => config.is_active).map((config) => (
              <option key={config.id} value={config.id}>
                {config.name} ({config.scenario_type.replace('_', ' ')})
              </option>
            ))}
          </select>
          {errors.agentConfigId && <p className="text-sm text-red-600 mt-1">{errors.agentConfigId}</p>}
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">Call Type</label>
          <select
            value={formData.callType}
            onChange={(e) => setFormData(prev => ({ ...prev, callType: e.target.value }))}
            className={`w-full px-3 py-2 border rounded-md ${errors.callType ? 'border-red-500' : 'border-gray-300'}`}
          >
            <option value="phone_call">📞 Phone Call (Direct)</option>
            <option value="web_call">🌐 Web Call (Browser-based)</option>
          </select>
          {errors.callType && <p className="text-sm text-red-600 mt-1">{errors.callType}</p>}
          <p className="text-xs text-gray-500 mt-1">
            {formData.callType === 'web_call' 
              ? 'Creates a web-based call that opens in browser' 
              : 'Creates a direct phone call to the driver\'s number'}
          </p>
        </div>
      </div>
      
      <div className="flex justify-end space-x-4 pt-4">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" disabled={initiateCall.isPending}>
          {initiateCall.isPending ? (
            <>
              <Clock className="h-4 w-4 mr-2 animate-spin" />
              Starting Call...
            </>
          ) : (
            <>
              <PlayCircle className="h-4 w-4 mr-2" />
              Start Call
            </>
          )}
        </Button>
      </div>
    </form>
  )
}
