import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, Phone, BarChart3, Users } from 'lucide-react'
import Link from 'next/link'
import { AuthGuard } from '@/components/AuthGuard'
import { Header } from '@/components/Header'

export default function HomePage() {
  return (
    <AuthGuard>
      <Header />
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">
            AI Voice Agent
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Configure, test, and review calls made by adaptive AI voice agents for logistics operations
          </p>
        </div>

        {/* Main Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {/* Configure Agents */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Configure Agents
              </CardTitle>
              <CardDescription>
                Set up voice agents with custom prompts, voice settings, and conversation logic
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild className="w-full shadow-md hover:shadow-lg" size="lg">
                <Link href="/agents">
                  Manage Agents
                </Link>
              </Button>
            </CardContent>
          </Card>

          {/* Start Calls */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Phone className="h-5 w-5" />
                Start Test Calls
              </CardTitle>
              <CardDescription>
                Trigger calls to drivers with specific load information and monitor real-time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild className="w-full shadow-md hover:shadow-lg" size="lg" variant="success">
                <Link href="/calls">
                  Start Call
                </Link>
              </Button>
            </CardContent>
          </Card>

          {/* View Results */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Call Results
              </CardTitle>
              <CardDescription>
                Review call transcripts, structured data extraction, and performance analytics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild className="w-full shadow-md hover:shadow-lg" size="lg" variant="outline">
                <Link href="/results">
                  View Results
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Features Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Logistics Scenarios */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Logistics Scenarios
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-l-4 border-blue-500 pl-4">
                <h3 className="font-semibold">Driver Check-in Agent</h3>
                <p className="text-sm text-muted-foreground">
                  Handles end-to-end driver check-in conversations with dynamic flow based on driver status
                </p>
                <div className="text-xs text-muted-foreground mt-1">
                  Extracts: driver status, location, ETA, delays, unloading status
                </div>
              </div>

              <div className="border-l-4 border-red-500 pl-4">
                <h3 className="font-semibold">Emergency Protocol Agent</h3>
                <p className="text-sm text-muted-foreground">
                  Detects emergencies during routine calls and immediately escalates to human dispatcher
                </p>
                <div className="text-xs text-muted-foreground mt-1">
                  Extracts: emergency type, safety status, location, escalation details
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Advanced Features */}
          <Card>
            <CardHeader>
              <CardTitle>Advanced Voice Features</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                <div>
                  <h4 className="font-medium text-sm">Backchannel Responses</h4>
                  <p className="text-xs text-muted-foreground">
                    Natural "uh-huh", "yeah" responses during conversation
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                <div>
                  <h4 className="font-medium text-sm">Interruption Sensitivity</h4>
                  <p className="text-xs text-muted-foreground">
                    Configurable sensitivity to user interruptions
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                <div>
                  <h4 className="font-medium text-sm">Human-like Flow</h4>
                  <p className="text-xs text-muted-foreground">
                    Filler words and natural conversation patterns
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                <div>
                  <h4 className="font-medium text-sm">Emergency Detection</h4>
                  <p className="text-xs text-muted-foreground">
                    Automatic pivot to emergency protocol when needed
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        </div>
      </div>
    </AuthGuard>
  )
}
