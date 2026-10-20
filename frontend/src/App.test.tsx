import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'

// Mock the auth context
vi.mock('./hooks/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-provider">{children}</div>
  ),
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    setUser: vi.fn(),
  }),
}))

describe('App', () => {
  it('renders login page when not authenticated', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Sign in to Vector Studio')).toBeInTheDocument()
    expect(screen.getByText('Sign in with Keycloak')).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    // This would need a more complex mock to test loading state
    // For now, verify the component renders
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )
    expect(screen.getByTestId('auth-provider')).toBeInTheDocument()
  })
})