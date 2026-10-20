import { useAuth } from '../hooks/useAuth'

export function Login() {
  const { login, loading } = useAuth()

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="login-page">
      <div className="card" style={{ maxWidth: '400px', margin: '4rem auto' }}>
        <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Sign in to Vector Studio</h2>
        <p style={{ textAlign: 'center', color: 'var(--color-fg-muted)', marginBottom: '2rem' }}>
          AI Agent Configuration Manager
        </p>
        <button
          className="btn btn-primary"
          style={{ width: '100%' }}
          onClick={login}
          disabled={loading}
        >
          Sign in with Keycloak
        </button>
        <p style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--color-fg-muted)' }}>
          Redirects to Keycloak for authentication
        </p>
      </div>
    </div>
  )
}