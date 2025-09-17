'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Phone, 
  Copy, 
  ExternalLink,
  AlertCircle,
  CheckCircle,
  Info
} from 'lucide-react'
import toast from 'react-hot-toast'

interface FallbackWebCallProps {
  token: string
}

export default function FallbackWebCall({ token }: FallbackWebCallProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      toast.success('Access token copied to clipboard!')
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      toast.error('Failed to copy to clipboard')
    }
  }

  const openRetellDemo = () => {
    // Open the Retell demo page with the access token
    const demoUrl = `https://demo.retellai.com/?access_token=${token}`
    window.open(demoUrl, '_blank')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Phone className="h-5 w-5 mr-2" />
            Web Call Ready
          </CardTitle>
          <CardDescription>
            Your webcall access token is ready. Use one of the options below to start the call.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Access Token Display */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Access Token:</label>
            <div className="flex items-center space-x-2">
              <code className="flex-1 p-2 bg-gray-100 rounded text-xs break-all">
                {token}
              </code>
              <Button
                size="sm"
                variant="outline"
                onClick={() => copyToClipboard(token)}
                className="shrink-0"
              >
                {copied ? <CheckCircle className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          {/* Call Options */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Info className="h-4 w-4" />
              <span>Choose how to start your call:</span>
            </div>

            {/* Option 1: Retell Demo */}
            <Button
              onClick={openRetellDemo}
              className="w-full"
              variant="default"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Open in Retell Demo
            </Button>

            {/* Option 2: Copy Token */}
            <Button
              onClick={() => copyToClipboard(token)}
              variant="outline"
              className="w-full"
            >
              <Copy className="h-4 w-4 mr-2" />
              Copy Access Token
            </Button>
          </div>

          {/* Instructions */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">How to use:</h4>
            <ol className="text-sm text-blue-800 space-y-1">
              <li>1. Click "Open in Retell Demo" to test the call</li>
              <li>2. Or copy the access token to use in your own implementation</li>
              <li>3. The token is valid for 30 seconds after generation</li>
            </ol>
          </div>

          {/* Back Button */}
          <Button 
            onClick={() => window.location.href = '/dashboard/calls'} 
            variant="outline"
            className="w-full"
          >
            Back to Calls
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
