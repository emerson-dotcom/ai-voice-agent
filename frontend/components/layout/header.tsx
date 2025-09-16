'use client'

import { useActiveCalls } from '@/hooks/use-calls'
import { useSocketEvent } from '@/hooks/use-socket'
import { Badge } from '@/components/ui/badge'
import { Bell, Phone, AlertTriangle } from 'lucide-react'
import { useState } from 'react'
import type { EmergencyAlert } from '@/types'
import toast from 'react-hot-toast'

export function Header() {
  const { data: activeCalls = [] } = useActiveCalls()
  const [emergencyAlerts, setEmergencyAlerts] = useState<EmergencyAlert[]>([])

  // Listen for emergency alerts
  useSocketEvent<EmergencyAlert>('emergency_detected', (alert) => {
    setEmergencyAlerts(prev => [alert, ...prev.slice(0, 4)]) // Keep last 5 alerts
    
    // Show urgent toast notification
    toast.error(
      `EMERGENCY: ${alert.driver_name} (Load ${alert.load_number})`,
      {
        duration: 10000,
        icon: '🚨',
      }
    )
  })

  const activeCallsCount = activeCalls.length
  const emergencyCount = emergencyAlerts.length

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Manage your AI voice agents and calls</p>
        </div>

        <div className="flex items-center space-x-4">
          {/* Active Calls Indicator */}
          <div className="flex items-center space-x-2">
            <Phone className="h-5 w-5 text-green-600" />
            <span className="text-sm text-gray-600">Active Calls:</span>
            <Badge variant={activeCallsCount > 0 ? "success" : "secondary"}>
              {activeCallsCount}
            </Badge>
          </div>

          {/* Emergency Alerts */}
          {emergencyCount > 0 && (
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span className="text-sm text-gray-600">Emergencies:</span>
              <Badge variant="destructive">
                {emergencyCount}
              </Badge>
            </div>
          )}

          {/* Notifications */}
          <div className="relative">
            <Bell className="h-6 w-6 text-gray-600 hover:text-gray-900 cursor-pointer" />
            {(activeCallsCount > 0 || emergencyCount > 0) && (
              <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full"></span>
            )}
          </div>
        </div>
      </div>

      {/* Emergency Alerts Bar */}
      {emergencyAlerts.length > 0 && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <span className="font-medium text-red-800">Recent Emergency Alerts:</span>
          </div>
          <div className="mt-2 space-y-1">
            {emergencyAlerts.slice(0, 3).map((alert, index) => (
              <div key={index} className="text-sm text-red-700">
                <strong>{alert.driver_name}</strong> (Load {alert.load_number}) - {alert.message.slice(0, 100)}...
              </div>
            ))}
          </div>
        </div>
      )}
    </header>
  )
}
