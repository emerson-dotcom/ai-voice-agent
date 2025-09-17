import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/lib/api'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  
  // Actions
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
  setToken: (token: string) => void
  clearAuth: () => void
  initializeAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: true, // Start with loading true to check stored auth
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const response = await api.login(email, password)
          const token = response.access_token
          
          // The API client automatically sets the token, but we also store it in state
          set({
            token,
            isAuthenticated: true,
            isLoading: false
          })
          
          // Note: In a real app, you'd decode the JWT to get user info
          // For now, we'll set a basic user object
          set({
            user: {
              id: 1,
              email,
              is_active: true,
              is_admin: true,
              created_at: new Date().toISOString()
            }
          })
          
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      register: async (email: string, password: string, fullName?: string) => {
        set({ isLoading: true })
        try {
          const user = await api.register(email, password, fullName)
          set({
            user,
            isLoading: false
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: () => {
        api.clearToken()
        set({
          user: null,
          token: null,
          isAuthenticated: false
        })
      },

      setUser: (user: User) => {
        set({ user })
      },

      setToken: (token: string) => {
        api.setToken(token)
        set({ token, isAuthenticated: true })
      },

      clearAuth: () => {
        api.clearToken()
        set({
          user: null,
          token: null,
          isAuthenticated: false
        })
      },

      // Initialize auth state from persisted data
      initializeAuth: () => {
        const { token } = get()
        if (token) {
          // Check if token is expired before using it
          try {
            const parts = token.split('.')
            if (parts.length !== 3) {
              throw new Error('Invalid token format')
            }
            
            const payload = JSON.parse(atob(parts[1]))
            const isExpired = payload.exp * 1000 < Date.now()
            
            if (isExpired) {
              console.log('Token expired, clearing auth state')
              set({ 
                user: null,
                token: null,
                isAuthenticated: false,
                isLoading: false 
              })
              api.clearToken()
            } else {
              api.setToken(token)
              set({ isAuthenticated: true, isLoading: false })
            }
          } catch (error) {
            console.error('Error parsing token:', error)
            set({ 
              user: null,
              token: null,
              isAuthenticated: false,
              isLoading: false 
            })
            api.clearToken()
          }
        } else {
          set({ isLoading: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        // Initialize auth state after rehydration
        if (state) {
          state.initializeAuth()
        }
      },
    }
  )
)

// Hook for easy use in components
export function useAuth() {
  const {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    setUser,
    setToken,
    clearAuth,
    initializeAuth,
  } = useAuthStore()

  return {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    setUser,
    setToken,
    clearAuth,
    initializeAuth,
  }
}
