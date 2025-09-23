'use client'

import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { User, LogOut, Settings, Shield, Phone, BarChart3, ChevronDown } from 'lucide-react'
import Link from 'next/link'

export function Header() {
  const { user, signOut, isAdmin } = useAuth()

  if (!user) return null

  const userRole = user.user_metadata?.role || 'user'
  const displayName = user.user_metadata?.full_name || user.email

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'dispatcher':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <header className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/" className="font-bold text-xl">
            AI Voice Agent
          </Link>
          <nav className="hidden md:flex space-x-6">
            <Link href="/agents" className="text-sm font-medium hover:text-primary">
              Agents
            </Link>
            <Link href="/calls" className="text-sm font-medium hover:text-primary">
              Calls
            </Link>
            <Link href="/results" className="text-sm font-medium hover:text-primary">
              Results
            </Link>
          </nav>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-2">
            <span className="text-sm font-medium">{displayName}</span>
            <Badge className={getRoleBadgeColor(userRole)} variant="secondary">
              {userRole}
            </Badge>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="flex items-center space-x-2 h-10 px-3 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-blue-600 flex items-center justify-center text-white text-sm font-medium">
                  {displayName.charAt(0).toUpperCase()}
                </div>
                <ChevronDown className="h-4 w-4 text-slate-500" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-64 mt-2 bg-white border border-slate-200 rounded-xl shadow-lg" align="end">
              <div className="px-4 py-3 bg-slate-50 rounded-t-xl border-b border-slate-200">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold">
                    {displayName.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-slate-900">{displayName}</p>
                    <p className="text-xs text-slate-600 truncate">{user.email}</p>
                    <Badge className={`${getRoleBadgeColor(userRole)} mt-1 text-xs px-2 py-0.5`} variant="secondary">
                      {userRole.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </div>

              <div className="md:hidden py-2">
                <DropdownMenuItem asChild>
                  <Link href="/agents" className="flex items-center px-4 py-3 hover:bg-slate-50 transition-colors">
                    <Settings className="mr-3 h-4 w-4 text-slate-600" />
                    <span className="text-sm font-medium">Configure Agents</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/calls" className="flex items-center px-4 py-3 hover:bg-slate-50 transition-colors">
                    <Phone className="mr-3 h-4 w-4 text-slate-600" />
                    <span className="text-sm font-medium">Start Calls</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/results" className="flex items-center px-4 py-3 hover:bg-slate-50 transition-colors">
                    <BarChart3 className="mr-3 h-4 w-4 text-slate-600" />
                    <span className="text-sm font-medium">Call Results</span>
                  </Link>
                </DropdownMenuItem>
                <div className="border-t border-slate-200 my-2"></div>
              </div>

              {isAdmin && (
                <div className="py-2">
                  <DropdownMenuItem asChild>
                    <Link href="/admin" className="flex items-center px-4 py-3 hover:bg-slate-50 transition-colors">
                      <Shield className="mr-3 h-4 w-4 text-amber-600" />
                      <span className="text-sm font-medium">Admin Panel</span>
                    </Link>
                  </DropdownMenuItem>
                  <div className="border-t border-slate-200 my-2"></div>
                </div>
              )}

              <div className="py-2">
                <DropdownMenuItem
                  onClick={() => signOut()}
                  className="flex items-center px-4 py-3 text-red-600 hover:text-red-700 hover:bg-red-50 transition-colors cursor-pointer"
                >
                  <LogOut className="mr-3 h-4 w-4" />
                  <span className="text-sm font-medium">Sign Out</span>
                </DropdownMenuItem>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}