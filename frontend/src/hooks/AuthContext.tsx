import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export interface User {
  id: string
  username: string
  email: string
  roles: string[]
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  login: () => void
  logout: () => void
  setUser: (user: User | null) => void
  exchangeCodeForToken: (code: string) => Promise<User | null>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function getEnv(key: string, fallback: string): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (import.meta as any).env?.[key] ?? fallback
}

const API_BASE = getEnv('VITE_API_BASE', '')

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = sessionStorage.getItem('user')
    if (stored) {
      setUser(JSON.parse(stored))
    }
    setLoading(false)
  }, [])

  const login = () => {
    const params = new URLSearchParams({
      client_id: getEnv('VITE_OIDC_CLIENT_ID', 'vector-studio'),
      redirect_uri: getEnv('VITE_OIDC_REDIRECT_URI', 'http://localhost:5173/callback'),
      response_type: 'code',
      scope: 'openid profile email',
      state: crypto.randomUUID(),
      nonce: crypto.randomUUID(),
    })
    const issuer = getEnv('VITE_OIDC_ISSUER_URL', 'http://localhost:8080/realms/vector-studio')
    window.location.href = `${issuer}/protocol/openid-connect/auth?${params.toString()}`
  }

  const logout = async () => {
    setUser(null)
    sessionStorage.removeItem('user')
    const issuer = getEnv('VITE_OIDC_ISSUER_URL', 'http://localhost:8080/realms/vector-studio')
    const redirectUri = getEnv('VITE_OIDC_LOGOUT_URI', 'http://localhost:5173')
    window.location.href = `${issuer}/protocol/openid-connect/logout?post_logout_redirect_uri=${encodeURIComponent(redirectUri)}`
  }

  const exchangeCodeForToken = async (code: string): Promise<User | null> => {
    const redirectUri = getEnv('VITE_OIDC_REDIRECT_URI', 'http://localhost:5173/callback')
    try {
      const response = await fetch(`${API_BASE}/auth/callback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, redirect_uri: redirectUri }),
      })
      if (!response.ok) {
        throw new Error('Token exchange failed')
      }
      const data = await response.json()
      const userData: User = {
        id: String(data.user.id),
        username: data.user.username,
        email: data.user.email,
        roles: data.user.roles,
      }
      sessionStorage.setItem('user', JSON.stringify(userData))
      sessionStorage.setItem('access_token', data.access_token)
      return userData
    } catch (error) {
      console.error('Token exchange error:', error)
      return null
    }
  }

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    logout,
    setUser,
    exchangeCodeForToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}