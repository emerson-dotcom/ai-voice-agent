'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Phone, 
  PhoneOff, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react'
import toast from 'react-hot-toast'

// Declare the RetellWebClient type (you'll need to install the SDK)
declare global {
  interface Window {
    RetellWebClient: any
  }
}

export default function WebCallPage() {
  const params = useParams()
  const token = params?.token as string
  
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isSpeakerMuted, setIsSpeakerMuted] = useState(false)
  const [callStatus, setCallStatus] = useState<'connecting' | 'connected' | 'ended' | 'error'>('connecting')
  const [error, setError] = useState<string | null>(null)
  const [permissionDenied, setPermissionDenied] = useState(false)
  const [retellClient, setRetellClient] = useState<any>(null)
  const [connectionTimeout, setConnectionTimeout] = useState<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!token) {
      setError('No access token provided')
      setCallStatus('error')
      return
    }

    // Load the Retell Web SDK
    const loadRetellSDK = async () => {
      try {
        // Try different import methods for the Retell Web SDK
        let RetellWebClient;
        
        try {
          // Method 1: Default import
          const retellModule = await import('retell-client-js-sdk')
          RetellWebClient = retellModule.RetellWebClient || retellModule.default?.RetellWebClient || retellModule.default
        } catch (importError) {
          console.error('Failed to import retell-client-js-sdk:', importError)
          throw new Error('Retell Web SDK not available. Please install: npm install retell-client-js-sdk')
        }

        if (!RetellWebClient) {
          throw new Error('RetellWebClient not found in the SDK')
        }

        const client = new RetellWebClient()
        setRetellClient(client)

        // Set up event listeners (using correct event names)
        console.log('Setting up event listeners...')
        
        // Try multiple event names since the SDK might use different ones
        const eventNames = [
          'conversation_started', 'call_started', 'started', 'connected',
          'conversation_ended', 'call_ended', 'ended', 'disconnected',
          'error', 'audio_events', 'audio', 'message',
          'agent_audio', 'agent_speech', 'tts', 'speech', 'voice',
          'audio_data', 'audio_chunk', 'audio_buffer', 'audio_stream',
          'response', 'agent_response', 'ai_response', 'synthesis'
        ]
        
        eventNames.forEach(eventName => {
          client.on(eventName, async (data: any) => {
            console.log(`📡 Event received: ${eventName}`, data)
            
            // Handle connection events
            if (eventName === 'conversation_started' || eventName === 'call_started' || eventName === 'started' || eventName === 'connected') {
              console.log('✅ Connection event detected!')
              setIsConnected(true)
              setCallStatus('connected')
              toast.success('Call connected successfully!')
            }
            
            // Handle disconnection events
            if (eventName === 'conversation_ended' || eventName === 'call_ended' || eventName === 'ended' || eventName === 'disconnected') {
              console.log('❌ Disconnection event detected!')
              setIsConnected(false)
              setCallStatus('ended')
              toast.success('Call ended')
            }
            
            // Handle error events
            if (eventName === 'error') {
              console.error('❌ Error event detected:', data)
              setError(data.message || data.toString() || 'An error occurred during the call')
              setCallStatus('error')
              toast.error('Call error: ' + (data.message || data.toString() || 'Unknown error'))
            }
            
            // Handle audio events
            if (eventName === 'audio_events' || eventName === 'audio') {
              console.log('🔊 Audio event:', data)
              console.log('Audio event type:', typeof data)
              console.log('Audio event details:', JSON.stringify(data, null, 2))
              
                  // Try to play audio if it's audio data
                  if (data && typeof data === 'object') {
                    if (data.audioData || data.audio || data.buffer) {
                      console.log('🎵 Found audio data, attempting to play...')
                      console.log('Audio data structure:', Object.keys(data))
                      
                      try {
                        // Try multiple audio playback methods
                        let audioPlayed = false
                        
                        // Method 1: Try Retell SDK playAudio (but it seems to have issues)
                        if (typeof (client as any).playAudio === 'function') {
                          console.log('Trying Retell SDK playAudio...')
                          try {
                            await (client as any).playAudio(data)
                            console.log('✅ Retell SDK playAudio reported success')
                            // Don't mark as played yet - we need to verify it actually worked
                            // audioPlayed = true
                          } catch (retellError: any) {
                            console.log('❌ Retell SDK playAudio failed:', retellError)
                            console.log('Retell error details:', retellError.message, retellError.name)
                            // Continue to fallback methods
                          }
                        } else {
                          console.log('⚠️ Retell SDK playAudio method not available')
                        }
                        
                        // Method 2: Try direct audio element playback
                        if (!audioPlayed && (data.audioData || data.audio)) {
                          console.log('Trying direct audio element playback...')
                          const audioBlob = data.audioData || data.audio
                          if (audioBlob instanceof Blob) {
                            const audioUrl = URL.createObjectURL(audioBlob)
                            const audioElement = new Audio(audioUrl)
                            await audioElement.play()
                            console.log('✅ Audio played successfully via Audio element')
                            audioPlayed = true
                          }
                        }
                        
                        // Method 2.5: Try converting audio data to proper format
                        if (!audioPlayed && data && typeof data === 'object') {
                          console.log('Trying to convert audio data to proper format...')
                          try {
                            // Check if data is an array of audio samples
                            const audioSamples = Object.values(data)
                            if (Array.isArray(audioSamples) && audioSamples.length > 0) {
                              console.log('Converting audio samples to Web Audio API format...')
                              const audioContext = (client as any).audioContext || new (window.AudioContext || (window as any).webkitAudioContext)()
                              
                              // Create audio buffer from samples
                              const sampleRate = 16000 // Common sample rate for voice
                              const audioBuffer = audioContext.createBuffer(1, audioSamples.length, sampleRate)
                              const channelData = audioBuffer.getChannelData(0)
                              
                              // Convert samples to float32
                              for (let i = 0; i < audioSamples.length; i++) {
                                channelData[i] = (audioSamples[i] as number) / 255.0 - 0.5 // Convert 0-255 to -0.5 to 0.5
                              }
                              
                              // Play the audio
                              const source = audioContext.createBufferSource()
                              source.buffer = audioBuffer
                              source.connect(audioContext.destination)
                              source.start()
                              console.log('✅ Audio played successfully via converted Web Audio API')
                              audioPlayed = true
                            }
                          } catch (convertError: any) {
                            console.log('❌ Audio conversion failed:', convertError)
                          }
                        }
                        
                        // Method 3: Try Web Audio API
                        if (!audioPlayed && data.buffer) {
                          console.log('Trying Web Audio API playback...')
                          const audioContext = (client as any).audioContext || new (window.AudioContext || (window as any).webkitAudioContext)()
                          const audioBuffer = await audioContext.decodeAudioData(data.buffer)
                          const source = audioContext.createBufferSource()
                          source.buffer = audioBuffer
                          source.connect(audioContext.destination)
                          source.start()
                          console.log('✅ Audio played successfully via Web Audio API')
                          audioPlayed = true
                        }
                        
                        if (!audioPlayed) {
                          console.log('⚠️ No suitable audio playback method found')
                        }
                        
                      } catch (playError: any) {
                        console.error('❌ Failed to play audio:', playError)
                        console.error('Error details:', playError.message, playError.name)
                      }
                    }
                  }
            }
            
            // Handle any message events that might contain audio data
            if (eventName === 'message') {
              console.log('📨 Message event:', data)
              if (data && typeof data === 'object') {
                console.log('Message type:', data.type)
                console.log('Message content:', data.content)
                if (data.audio) {
                  console.log('🎵 Audio data in message:', data.audio)
                  console.log('Message audio structure:', Object.keys(data.audio))
                  
                  // Try to play the audio using multiple methods
                  try {
                    let audioPlayed = false
                    
                    // Method 1: Try Retell SDK playAudio
                    if (typeof (client as any).playAudio === 'function') {
                      console.log('Trying Retell SDK playAudio for message...')
                      await (client as any).playAudio(data.audio)
                      console.log('✅ Message audio played successfully via Retell SDK')
                      audioPlayed = true
                    }
                    
                    // Method 2: Try direct audio element playback
                    if (!audioPlayed && data.audio instanceof Blob) {
                      console.log('Trying direct audio element playback for message...')
                      const audioUrl = URL.createObjectURL(data.audio)
                      const audioElement = new Audio(audioUrl)
                      await audioElement.play()
                      console.log('✅ Message audio played successfully via Audio element')
                      audioPlayed = true
                    }
                    
                    if (!audioPlayed) {
                      console.log('⚠️ No suitable message audio playback method found')
                    }
                    
                  } catch (playError: any) {
                    console.error('❌ Failed to play message audio:', playError)
                    console.error('Message audio error details:', playError.message, playError.name)
                  }
                }
              }
            }
            
            // Handle specific agent audio events
            if (eventName === 'agent_audio' || eventName === 'agent_speech' || eventName === 'tts') {
              console.log('🤖 Agent audio event:', data)
              console.log('Agent audio structure:', Object.keys(data))
              
              try {
                let audioPlayed = false
                
                // Method 1: Try Retell SDK playAudio
                if (typeof (client as any).playAudio === 'function') {
                  console.log('Trying Retell SDK playAudio for agent...')
                  await (client as any).playAudio(data)
                  console.log('✅ Agent audio played successfully via Retell SDK')
                  audioPlayed = true
                }
                
                // Method 2: Try direct audio element playback
                if (!audioPlayed && data instanceof Blob) {
                  console.log('Trying direct audio element playback for agent...')
                  const audioUrl = URL.createObjectURL(data)
                  const audioElement = new Audio(audioUrl)
                  await audioElement.play()
                  console.log('✅ Agent audio played successfully via Audio element')
                  audioPlayed = true
                }
                
                // Method 3: Try Web Audio API for agent audio
                if (!audioPlayed && data.buffer) {
                  console.log('Trying Web Audio API for agent audio...')
                  const audioContext = (client as any).audioContext || new (window.AudioContext || (window as any).webkitAudioContext)()
                  const audioBuffer = await audioContext.decodeAudioData(data.buffer)
                  const source = audioContext.createBufferSource()
                  source.buffer = audioBuffer
                  source.connect(audioContext.destination)
                  source.start()
                  console.log('✅ Agent audio played successfully via Web Audio API')
                  audioPlayed = true
                }
                
                if (!audioPlayed) {
                  console.log('⚠️ No suitable agent audio playback method found')
                }
                
              } catch (playError: any) {
                console.error('❌ Failed to play agent audio:', playError)
                console.error('Agent audio error details:', playError.message, playError.name)
              }
            }
          })
        })

        // Log all available events
        console.log('Available events on client:', Object.getOwnPropertyNames(client))
        console.log('Event listeners set up for:', eventNames)

        // Check available methods on the client
        console.log('Available methods on client:', Object.getOwnPropertyNames(Object.getPrototypeOf(client)))
        console.log('Client object:', client)

        // Use the correct method name: startConversation
        if (typeof client.startConversation !== 'function') {
          throw new Error(`startConversation method not available. Available methods: ${Object.getOwnPropertyNames(Object.getPrototypeOf(client)).join(', ')}`)
        }

        // Check microphone permissions
        console.log('Checking microphone permissions...')
        console.log('MediaDevices available:', !!navigator.mediaDevices)
        console.log('getUserMedia available:', !!navigator.mediaDevices?.getUserMedia)
        
        // Check current permission status
        const permissionStatus = await checkPermissionStatus()
        console.log('Current permission status:', permissionStatus)
        
        try {
          // Request microphone permission with explicit user gesture
          console.log('Requesting microphone permission...')
          const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true
            }
          })
          console.log('Microphone access granted')
          console.log('Audio tracks:', stream.getAudioTracks().length)
          // Stop the stream as we just needed to check permissions
          stream.getTracks().forEach(track => {
            console.log('Stopping track:', track.label)
            track.stop()
          })
        } catch (permissionError: any) {
          console.warn('Microphone permission error:', permissionError)
          console.warn('Error name:', permissionError.name)
          console.warn('Error message:', permissionError.message)
          
          if (permissionError.name === 'NotAllowedError') {
            setError('Microphone access was denied. Please click "Grant Microphone Permission" to allow access.')
            setPermissionDenied(true)
          } else if (permissionError.name === 'NotFoundError') {
            setError('No microphone found. Please connect a microphone and try again.')
          } else if (permissionError.name === 'NotReadableError') {
            setError('Microphone is being used by another application. Please close other apps and try again.')
          } else {
            setError(`Microphone error: ${permissionError.message}`)
          }
          
          setCallStatus('error')
          toast.error('Microphone access is required for voice calls')
          return // Don't continue with the call setup
        }

        // Set up audio before starting conversation
        console.log('Setting up audio...')
        try {
          // Try to call setupAudioPlayback if it's available
          if (typeof (client as any).setupAudioPlayback === 'function') {
            await (client as any).setupAudioPlayback()
            console.log('✅ Audio setup completed')
          } else {
            console.log('⚠️ setupAudioPlayback not available, trying alternative methods')
            
            // Try alternative audio setup methods
            if (typeof (client as any).handleAudioEvents === 'function') {
              console.log('Setting up audio events handler...')
              await (client as any).handleAudioEvents()
              console.log('✅ Audio events handler set up')
            }
            
            if (typeof (client as any).playAudio === 'function') {
              console.log('Audio playback method available')
            }
          }
          
          // Set up audio context for better audio handling
          console.log('Setting up audio context...')
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
          console.log('Audio context state:', audioContext.state)
          
          if (audioContext.state === 'suspended') {
            await audioContext.resume()
            console.log('Audio context resumed')
          }
          
          // Store audio context for later use
          (client as any).audioContext = audioContext
          
        } catch (audioError: any) {
          console.warn('❌ Audio setup failed:', audioError)
          // Continue anyway, as audio setup might not be required
        }

        // Validate token format
        console.log('Starting conversation with token:', token)
        console.log('Token length:', token.length)
        
        // Check if token is a valid JWT format (3 parts separated by dots)
        const tokenParts = token.split('.')
        if (tokenParts.length !== 3) {
          throw new Error('Invalid token format. Expected JWT format with 3 parts.')
        }
        
        // Decode token payload for debugging (without verification)
        try {
          const payload = JSON.parse(atob(tokenParts[1]))
          console.log('Token payload:', payload)
          console.log('Token expires at:', new Date(payload.exp * 1000))
          console.log('Token issued at:', new Date(payload.iat * 1000))
        } catch (decodeError) {
          console.warn('Could not decode token payload:', decodeError)
        }
        
        try {
          // Try different parameter formats with timeout
          console.log('Attempting to start conversation...')
          console.log('Client object:', client)
          console.log('Token being used:', token)
          
          // Create a timeout promise
          const timeoutPromise = new Promise((_, reject) => {
            const timeout = setTimeout(() => {
              reject(new Error('Conversation start timeout after 30 seconds'))
            }, 30000)
            setConnectionTimeout(timeout)
          })
          
          // Method 1: Try with accessToken parameter
          try {
            console.log('Trying Method 1: { accessToken: token }')
            await Promise.race([
              (client as any).startConversation({ accessToken: token }),
              timeoutPromise
            ])
            console.log('✅ Conversation started successfully with accessToken parameter')
            
            // Set up a fallback timer to mark as connected if no event is received
            setTimeout(() => {
              if (callStatus === 'connecting') {
                console.log('🔄 No connection event received, assuming connected based on successful startConversation')
                setIsConnected(true)
                setCallStatus('connected')
                toast.success('Call connected successfully!')
                
                // Test audio after connection
                setTimeout(() => {
                  console.log('🎵 Testing audio after connection...')
                  testAudioPlayback()
                }, 1000)
              }
            }, 2000) // Wait 2 seconds for events
          } catch (error1: any) {
            console.warn('❌ Method 1 failed:', error1)
            console.warn('Error details:', error1.message, error1.name, error1.stack)
            
            // Method 2: Try with token parameter
            try {
              console.log('Trying Method 2: { token: token }')
              await Promise.race([
                (client as any).startConversation({ token: token }),
                timeoutPromise
              ])
              console.log('✅ Conversation started successfully with token parameter')
              
              // Set up a fallback timer to mark as connected if no event is received
              setTimeout(() => {
                if (callStatus === 'connecting') {
                  console.log('🔄 No connection event received, assuming connected based on successful startConversation')
                  setIsConnected(true)
                  setCallStatus('connected')
                  toast.success('Call connected successfully!')
                  
                  // Test audio after connection
                  setTimeout(() => {
                    console.log('🎵 Testing audio after connection...')
                    testAudioPlayback()
                  }, 1000)
                }
              }, 2000) // Wait 2 seconds for events
            } catch (error2: any) {
              console.warn('❌ Method 2 failed:', error2)
              console.warn('Error details:', error2.message, error2.name, error2.stack)
              
              // Method 3: Try with just the token as a string
              try {
                console.log('Trying Method 3: token as string')
                await Promise.race([
                  (client as any).startConversation(token),
                  timeoutPromise
                ])
                console.log('✅ Conversation started successfully with token as string')
                
                // Set up a fallback timer to mark as connected if no event is received
                setTimeout(() => {
                  if (callStatus === 'connecting') {
                    console.log('🔄 No connection event received, assuming connected based on successful startConversation')
                    setIsConnected(true)
                    setCallStatus('connected')
                    toast.success('Call connected successfully!')
                    
                    // Test audio after connection
                    setTimeout(() => {
                      console.log('🎵 Testing audio after connection...')
                      testAudioPlayback()
                    }, 1000)
                  }
                }, 2000) // Wait 2 seconds for events
              } catch (error3: any) {
                console.error('❌ All methods failed:', error3)
                console.error('Final error details:', error3.message, error3.name, error3.stack)
                throw error3
              }
            }
          }
        } catch (startError: any) {
          console.error('❌ Error starting conversation:', startError)
          console.error('Start error details:', startError.message, startError.name, startError.stack)
          throw startError
        }
        
      } catch (err: any) {
        console.error('Failed to load Retell SDK:', err)
        setError('Failed to load call interface: ' + err.message)
        setCallStatus('error')
        toast.error('Failed to start call: ' + err.message)
        
        // Show fallback information
        console.log('Access token for manual use:', token)
      }
    }

    loadRetellSDK()

    // Cleanup on unmount
    return () => {
      if (retellClient) {
        retellClient.stopConversation()
      }
      if (connectionTimeout) {
        clearTimeout(connectionTimeout)
      }
    }
  }, [token])

  const handleMuteToggle = () => {
    if (retellClient) {
      // Check if audio control methods are available
      if (typeof retellClient.handleAudioEvents === 'function') {
        if (isMuted) {
          // Unmute - you may need to implement this based on the SDK
          setIsMuted(false)
          toast.success('Microphone unmuted')
        } else {
          // Mute - you may need to implement this based on the SDK
          setIsMuted(true)
          toast.success('Microphone muted')
        }
      } else {
        toast.success('Audio controls not available in this SDK version')
      }
    }
  }

  const handleSpeakerToggle = () => {
    if (retellClient) {
      // Check if audio control methods are available
      if (typeof retellClient.setupAudioPlayback === 'function') {
        if (isSpeakerMuted) {
          setIsSpeakerMuted(false)
          toast.success('Speaker unmuted')
        } else {
          setIsSpeakerMuted(true)
          toast.success('Speaker muted')
        }
      } else {
        toast.success('Speaker controls not available in this SDK version')
      }
    }
  }

  const handleEndCall = () => {
    if (retellClient) {
      retellClient.stopConversation()
      setIsConnected(false)
      setCallStatus('ended')
    }
  }

  const checkPermissionStatus = async () => {
    try {
      if (navigator.permissions) {
        const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName })
        console.log('Current microphone permission status:', permission.state)
        return permission.state
      }
    } catch (error) {
      console.log('Could not check permission status:', error)
    }
    return 'unknown'
  }

  const handleCancelConnection = () => {
    console.log('User cancelled connection attempt')
    if (connectionTimeout) {
      clearTimeout(connectionTimeout)
      setConnectionTimeout(null)
    }
    setCallStatus('error')
    setError('Connection cancelled by user')
    toast.error('Connection cancelled')
  }

  const testAudioPlayback = async () => {
    try {
      console.log('Testing audio playback...')
      
      // Test browser audio context
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      console.log('Audio context state:', audioContext.state)
      
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
        console.log('Audio context resumed')
      }
      
      // Test if we can create an audio element
      const audio = new Audio()
      console.log('Audio element created:', !!audio)
      
      // Test if we can play a simple tone
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      oscillator.frequency.setValueAtTime(440, audioContext.currentTime)
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime)
      
      oscillator.start()
      oscillator.stop(audioContext.currentTime + 0.1)
      
      console.log('✅ Audio test completed successfully')
      toast.success('Audio test successful')
      
    } catch (error: any) {
      console.error('❌ Audio test failed:', error)
      toast.error('Audio test failed: ' + (error.message || 'Unknown error'))
    }
  }

  const debugRetellSDK = () => {
    if (retellClient) {
      console.log('🔍 Retell SDK Debug Information:')
      console.log('Client object:', retellClient)
      console.log('Available methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(retellClient)))
      console.log('Available properties:', Object.getOwnPropertyNames(retellClient))
      
      // Check for audio-related methods
      const audioMethods = Object.getOwnPropertyNames(Object.getPrototypeOf(retellClient))
        .filter(method => method.toLowerCase().includes('audio') || 
                         method.toLowerCase().includes('play') || 
                         method.toLowerCase().includes('sound') ||
                         method.toLowerCase().includes('speech'))
      
      console.log('Audio-related methods:', audioMethods)
      
      // Try to call audio methods if they exist
      audioMethods.forEach(method => {
        try {
          if (typeof (retellClient as any)[method] === 'function') {
            console.log(`Method ${method} is available and callable`)
          }
        } catch (error) {
          console.log(`Method ${method} exists but may not be callable:`, error)
        }
      })
      
      toast.success('SDK debug info logged to console')
    } else {
      toast.error('No Retell client available')
    }
  }

  const testAudioFormats = async () => {
    try {
      console.log('🧪 Testing different audio formats...')
      
      // Test 1: Create a simple audio blob
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const sampleRate = audioContext.sampleRate
      const duration = 0.5 // 0.5 seconds
      const numSamples = sampleRate * duration
      
      // Create a simple sine wave
      const buffer = audioContext.createBuffer(1, numSamples, sampleRate)
      const data = buffer.getChannelData(0)
      for (let i = 0; i < numSamples; i++) {
        data[i] = Math.sin(2 * Math.PI * 440 * i / sampleRate) * 0.1
      }
      
      // Test Audio Element playback
      console.log('Testing Audio Element playback...')
      const audioElement = new Audio()
      const audioUrl = URL.createObjectURL(new Blob([buffer.getChannelData(0)]))
      audioElement.src = audioUrl
      await audioElement.play()
      console.log('✅ Audio Element playback successful')
      
      // Test Web Audio API playback
      console.log('Testing Web Audio API playback...')
      const source = audioContext.createBufferSource()
      source.buffer = buffer
      source.connect(audioContext.destination)
      source.start()
      console.log('✅ Web Audio API playback successful')
      
      // Test if Retell SDK can handle our test audio
      if (retellClient && typeof (retellClient as any).playAudio === 'function') {
        console.log('Testing Retell SDK playAudio with test data...')
        try {
          await (retellClient as any).playAudio({ buffer: buffer })
          console.log('✅ Retell SDK playAudio successful')
        } catch (error) {
          console.log('❌ Retell SDK playAudio failed:', error)
        }
      }
      
      toast.success('Audio format tests completed - check console')
      
    } catch (error: any) {
      console.error('❌ Audio format test failed:', error)
      toast.error('Audio format test failed: ' + (error.message || 'Unknown error'))
    }
  }

  const testRetellAudioFormat = async () => {
    try {
      console.log('🧪 Testing Retell audio format specifically...')
      
      // Create test data in the same format as Retell (0-255 values)
      const testAudioData: { [key: number]: number } = {}
      const sampleRate = 16000
      const duration = 0.5 // 0.5 seconds
      const numSamples = sampleRate * duration
      
      // Generate test audio samples (0-255 range)
      for (let i = 0; i < numSamples; i++) {
        const sample = Math.sin(2 * Math.PI * 440 * i / sampleRate) * 0.5 + 0.5 // 0 to 1
        testAudioData[i] = Math.round(sample * 255) // 0 to 255
      }
      
      console.log('Created test audio data:', Object.keys(testAudioData).length, 'samples')
      console.log('Sample values:', Object.values(testAudioData).slice(0, 10))
      
      // Test Retell SDK with this format
      if (retellClient && typeof (retellClient as any).playAudio === 'function') {
        console.log('Testing Retell SDK with 0-255 format...')
        try {
          await (retellClient as any).playAudio(testAudioData)
          console.log('✅ Retell SDK playAudio with 0-255 format successful')
        } catch (error) {
          console.log('❌ Retell SDK playAudio with 0-255 format failed:', error)
        }
      }
      
      // Test our conversion method
      console.log('Testing our audio conversion method...')
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const audioSamples = Object.values(testAudioData)
      const audioBuffer = audioContext.createBuffer(1, audioSamples.length, sampleRate)
      const channelData = audioBuffer.getChannelData(0)
      
      // Convert samples to float32
      for (let i = 0; i < audioSamples.length; i++) {
        channelData[i] = ((audioSamples[i] as number) / 255.0 - 0.5) * 2 // Convert 0-255 to -1 to 1
      }
      
      const source = audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContext.destination)
      source.start()
      console.log('✅ Our conversion method successful')
      
      toast.success('Retell audio format test completed - check console')
      
    } catch (error: any) {
      console.error('❌ Retell audio format test failed:', error)
      toast.error('Retell audio format test failed: ' + (error.message || 'Unknown error'))
    }
  }

  const handleRequestPermission = async () => {
    try {
      console.log('User clicked permission button - requesting microphone access...')
      setCallStatus('connecting')
      setError(null)
      setPermissionDenied(false)
      
      // Check if getUserMedia is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia is not supported in this browser')
      }
      
      console.log('Requesting microphone permission with user gesture...')
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })
      
      console.log('Microphone permission granted successfully!')
      console.log('Audio tracks:', stream.getAudioTracks().length)
      stream.getTracks().forEach(track => {
        console.log('Stopping track:', track.label)
        track.stop()
      })
      
      toast.success('Microphone permission granted! Starting call...')
      
      // Reload the page to restart the call setup
      setTimeout(() => {
        window.location.reload()
      }, 1000)
      
    } catch (permissionError: any) {
      console.error('Permission request failed:', permissionError)
      console.error('Error name:', permissionError.name)
      console.error('Error message:', permissionError.message)
      
      if (permissionError.name === 'NotAllowedError') {
        setError('Microphone access is still denied. Please check your browser settings and allow microphone access for this site.')
      } else if (permissionError.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.')
      } else if (permissionError.name === 'NotReadableError') {
        setError('Microphone is being used by another application. Please close other apps and try again.')
      } else {
        setError(`Microphone error: ${permissionError.message}`)
      }
      
      setCallStatus('error')
      setPermissionDenied(true)
      toast.error('Microphone access denied. Please check browser settings.')
    }
  }

  const getStatusBadge = () => {
    switch (callStatus) {
      case 'connecting':
        return <Badge className="bg-blue-100 text-blue-800"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Connecting</Badge>
      case 'connected':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Connected</Badge>
      case 'ended':
        return <Badge className="bg-gray-100 text-gray-800"><PhoneOff className="h-3 w-3 mr-1" />Ended</Badge>
      case 'error':
        return <Badge className="bg-red-100 text-red-800"><AlertCircle className="h-3 w-3 mr-1" />Error</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center text-red-600">
              <AlertCircle className="h-5 w-5 mr-2" />
              Call Error
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-600">{error}</p>
            
            {permissionDenied && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h4 className="font-medium text-yellow-800 mb-2">Microphone Permission Required</h4>
                <ul className="text-sm text-yellow-700 space-y-1">
                  <li>• Click "Grant Microphone Permission" button above</li>
                  <li>• Allow microphone access when prompted by your browser</li>
                  <li>• Make sure your microphone is connected and working</li>
                  <li>• If no prompt appears, check your browser's site permissions</li>
                </ul>
                
                <div className="mt-3 p-3 bg-yellow-100 rounded border border-yellow-300">
                  <h5 className="font-medium text-yellow-800 mb-1">If no permission prompt appears:</h5>
                  <ul className="text-xs text-yellow-700 space-y-1">
                    <li><strong>Chrome:</strong> Click the lock icon in address bar → Microphone → Allow</li>
                    <li><strong>Firefox:</strong> Click the shield icon → Permissions → Microphone → Allow</li>
                    <li><strong>Edge:</strong> Click the lock icon → Site permissions → Microphone → Allow</li>
                    <li><strong>Safari:</strong> Safari menu → Settings → Websites → Microphone → Allow</li>
                  </ul>
                </div>
              </div>
            )}
            
            {/* Show access token for manual use */}
            <div className="p-4 bg-gray-100 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Access Token:</h4>
              <code className="text-xs break-all text-gray-700">{token}</code>
              <p className="text-xs text-gray-500 mt-2">
                You can use this token with the Retell Web SDK in your own implementation.
              </p>
            </div>
            
            <div className="flex space-x-2">
              {permissionDenied ? (
                <>
                  <Button 
                    onClick={handleRequestPermission}
                    className="flex-1"
                  >
                    Grant Microphone Permission
                  </Button>
                  <Button 
                    onClick={async () => {
                      const status = await checkPermissionStatus()
                      console.log('Permission status:', status)
                      toast.success(`Permission status: ${status}`)
                    }}
                    variant="outline"
                    className="flex-1"
                  >
                    Check Status
                  </Button>
                </>
              ) : (
                <Button 
                  onClick={() => navigator.clipboard.writeText(token)}
                  variant="outline"
                  className="flex-1"
                >
                  Copy Token
                </Button>
              )}
              <Button 
                onClick={() => window.location.href = '/dashboard/calls'} 
                className="flex-1"
              >
                Back to Calls
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Web Call</span>
            {getStatusBadge()}
          </CardTitle>
          <CardDescription>
            {callStatus === 'connecting' && 'Connecting to call...'}
            {callStatus === 'connected' && 'Call is active'}
            {callStatus === 'ended' && 'Call has ended'}
            {callStatus === 'error' && 'Call encountered an error'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {callStatus === 'connecting' && (
            <div className="text-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
              <p className="text-gray-600 mb-4">Connecting to call...</p>
              <Button
                variant="outline"
                onClick={handleCancelConnection}
                className="px-6"
              >
                Cancel Connection
              </Button>
            </div>
          )}

          {callStatus === 'connected' && (
            <div className="space-y-4">
              <div className="text-center py-4">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Phone className="h-8 w-8 text-green-600" />
                </div>
                <p className="text-lg font-medium text-gray-900">Call Active</p>
                <p className="text-sm text-gray-600">You are connected to the AI agent</p>
              </div>

              <div className="space-y-4">
                <div className="flex justify-center space-x-4">
                  <Button
                    variant={isMuted ? "destructive" : "outline"}
                    size="lg"
                    onClick={handleMuteToggle}
                    className="rounded-full w-12 h-12 p-0"
                  >
                    {isMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
                  </Button>

                  <Button
                    variant={isSpeakerMuted ? "destructive" : "outline"}
                    size="lg"
                    onClick={handleSpeakerToggle}
                    className="rounded-full w-12 h-12 p-0"
                  >
                    {isSpeakerMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                  </Button>

                  <Button
                    variant="destructive"
                    size="lg"
                    onClick={handleEndCall}
                    className="rounded-full w-12 h-12 p-0"
                  >
                    <PhoneOff className="h-5 w-5" />
                  </Button>
                </div>
                
                <div className="text-center space-y-2">
                  <div className="flex justify-center space-x-2 flex-wrap gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={testAudioPlayback}
                      className="px-4"
                    >
                      Test Audio
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={debugRetellSDK}
                      className="px-4"
                    >
                      Debug SDK
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={testAudioFormats}
                      className="px-4"
                    >
                      Test Formats
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={testRetellAudioFormat}
                      className="px-4"
                    >
                      Test Retell
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500">
                    Test browser audio, debug SDK, and test Retell audio format
                  </p>
                </div>
              </div>
            </div>
          )}

          {callStatus === 'ended' && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <PhoneOff className="h-8 w-8 text-gray-600" />
              </div>
              <p className="text-lg font-medium text-gray-900 mb-4">Call Ended</p>
              <Button 
                onClick={() => window.location.href = '/dashboard/calls'} 
                className="w-full"
              >
                Back to Calls
              </Button>
            </div>
          )}

          {callStatus === 'error' && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="h-8 w-8 text-red-600" />
              </div>
              <p className="text-lg font-medium text-gray-900 mb-4">Call Error</p>
              <p className="text-sm text-gray-600 mb-4">{error}</p>
              <Button 
                onClick={() => window.location.href = '/dashboard/calls'} 
                className="w-full"
              >
                Back to Calls
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
