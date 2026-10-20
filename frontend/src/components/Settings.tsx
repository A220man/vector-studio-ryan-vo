import { useAuth } from '../hooks/useAuth'

export function Settings() {
  const { user } = useAuth()

  return (
    <div className="settings">
      <h2>Settings</h2>
      
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3>Profile</h3>
        <div style={{ display: 'grid', gap: '1rem', maxWidth: '400px' }}>
          <div className="form-group">
            <label>Username</label>
            <input type="text" value={user?.username || ''} readOnly />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={user?.email || ''} readOnly />
          </div>
          <div className="form-group">
            <label>Roles</label>
            <input type="text" value={user?.roles.join(', ') || ''} readOnly />
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3>LLM Configuration</h3>
        <div style={{ display: 'grid', gap: '1rem', maxWidth: '500px' }}>
          <div className="form-group">
            <label>Provider</label>
            <select defaultValue="openai-compatible">
              <option value="openai-compatible">OpenAI Compatible</option>
              <option value="anthropic">Anthropic</option>
              <option value="gemini">Gemini</option>
              <option value="ollama">Ollama</option>
            </select>
          </div>
          <div className="form-group">
            <label>Model</label>
            <input type="text" defaultValue="gpt-4o-mini" placeholder="Model name" />
          </div>
          <div className="form-group">
            <label>Base URL (optional)</label>
            <input type="text" placeholder="https://api.openai.com/v1" />
          </div>
          <div className="form-group">
            <label>API Key</label>
            <input type="password" placeholder="••••••••" />
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Keycloak / OIDC</h3>
        <div style={{ display: 'grid', gap: '1rem', maxWidth: '500px' }}>
          <div className="form-group">
            <label>Issuer URL</label>
            <input type="text" defaultValue="http://localhost:8080/realms/vector-studio" readOnly />
          </div>
          <div className="form-group">
            <label>Client ID</label>
            <input type="text" defaultValue="vector-studio" readOnly />
          </div>
          <div className="form-group">
            <label>Redirect URI</label>
            <input type="text" defaultValue="http://localhost:5173/callback" readOnly />
          </div>
        </div>
      </div>
    </div>
  )
}