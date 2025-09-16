import { io, Socket } from 'socket.io-client'
import { SOCKET_URL } from './constants'
import type { CallStatusUpdate, ConversationUpdate, EmergencyAlert } from '@/types'

class SocketManager {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(token: string): Socket {
    if (this.socket?.connected) {
      return this.socket
    }

    this.socket = io(SOCKET_URL, {
      auth: {
        token: token
      },
      transports: ['websocket', 'polling'],
      timeout: 10000,
      forceNew: true
    })

    this.setupEventHandlers()
    return this.socket
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  private setupEventHandlers(): void {
    if (!this.socket) return

    this.socket.on('connect', () => {
      console.log('Connected to server')
      this.reconnectAttempts = 0
    })

    this.socket.on('disconnect', (reason) => {
      console.log('Disconnected from server:', reason)
      this.handleReconnect()
    })

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error)
      this.handleReconnect()
    })

    // Application-specific events
    this.socket.on('call_initiated', (data) => {
      console.log('Call initiated:', data)
      this.emit('call_initiated', data)
    })

    this.socket.on('call_status_update', (data: CallStatusUpdate) => {
      console.log('Call status update:', data)
      this.emit('call_status_update', data)
    })

    this.socket.on('conversation_update', (data: ConversationUpdate) => {
      console.log('Conversation update:', data)
      this.emit('conversation_update', data)
    })

    this.socket.on('call_completed', (data) => {
      console.log('Call completed:', data)
      this.emit('call_completed', data)
    })

    this.socket.on('emergency_detected', (data: EmergencyAlert) => {
      console.log('Emergency detected:', data)
      this.emit('emergency_detected', data)
    })

    this.socket.on('emergency_protocol_activated', (data) => {
      console.log('Emergency protocol activated:', data)
      this.emit('emergency_protocol_activated', data)
    })
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
        this.socket?.connect()
      }, delay)
    }
  }

  // Event emitter for React components
  private eventHandlers: Record<string, Function[]> = {}

  on(event: string, handler: Function): void {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = []
    }
    this.eventHandlers[event].push(handler)
  }

  off(event: string, handler: Function): void {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler)
    }
  }

  private emit(event: string, data: any): void {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => handler(data))
    }
  }

  // Room management
  joinCallRoom(callId: number): void {
    this.socket?.emit('join_call_room', { call_id: callId })
  }

  leaveCallRoom(callId: number): void {
    this.socket?.emit('leave_call_room', { call_id: callId })
  }

  // Get socket instance for direct use
  getSocket(): Socket | null {
    return this.socket
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }
}

export const socketManager = new SocketManager()
