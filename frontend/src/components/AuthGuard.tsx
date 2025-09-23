'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface AuthGuardProps {
  children: React.ReactNode
  requiredRole?: 'admin' | 'dispatcher' | 'user'
}

export function AuthGuard({ children, requiredRole }: AuthGuardProps) {
  const { isAuthenticated, loading, user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    console.log('AuthGuard - loading:', loading, 'isAuthenticated:', isAuthenticated, 'user:', !!user)

    if (!loading && !isAuthenticated) {
      console.log('AuthGuard - Redirecting to login...')
      router.push('/login')
    }
  }, [isAuthenticated, loading, router, user])

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return null
  }

  // Check role requirements
  if (requiredRole) {
    const userRole = user?.user_metadata?.role || 'user'

    // Role hierarchy check
    const roleHierarchy = {
      'admin': 3,
      'dispatcher': 2,
      'user': 1
    }

    const userLevel = roleHierarchy[userRole as keyof typeof roleHierarchy] || 0
    const requiredLevel = roleHierarchy[requiredRole] || 0

    if (userLevel < requiredLevel) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center max-w-md">
            <div className="text-6xl mb-4">🔒</div>
            <h1 className="text-2xl font-bold mb-2">Access Denied</h1>
            <p className="text-muted-foreground mb-4">
              You don't have permission to access this page.
              {requiredRole === 'admin' && ' Admin access is required.'}
            </p>
            <button
              onClick={() => router.push('/')}
              className="text-blue-600 hover:underline"
            >
              Go back to home
            </button>
          </div>
        </div>
      )
    }
  }

  return <>{children}</>
}