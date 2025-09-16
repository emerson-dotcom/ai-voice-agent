import { useEffect, useState } from 'react'
import { socketManager } from '@/lib/socket'
import type { Socket } from 'socket.io-client'

export function useSocket(token?: string) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    if (token) {
      const socketInstance = socketManager.connect(token)
      setSocket(socketInstance)

      const handleConnect = () => setIsConnected(true)
      const handleDisconnect = () => setIsConnected(false)

      socketInstance.on('connect', handleConnect)
      socketInstance.on('disconnect', handleDisconnect)

      // Set initial state
      setIsConnected(socketInstance.connected)

      return () => {
        socketInstance.off('connect', handleConnect)
        socketInstance.off('disconnect', handleDisconnect)
      }
    }
  }, [token])

  return {
    socket,
    isConnected,
    joinCallRoom: (callId: number) => socketManager.joinCallRoom(callId),
    leaveCallRoom: (callId: number) => socketManager.leaveCallRoom(callId),
  }
}

export function useSocketEvent<T = any>(
  eventName: string,
  handler: (data: T) => void,
  deps: any[] = []
) {
  useEffect(() => {
    socketManager.on(eventName, handler)

    return () => {
      socketManager.off(eventName, handler)
    }
  }, deps)
}
