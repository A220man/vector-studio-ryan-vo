import { useAuth } from '../hooks/useAuth'
import { Link } from 'react-router-dom'

export function Dashboard() {
  const { user, logout } = useAuth()

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Dashboard</h2>
        <div className="user-info">
          <span>Welcome, {user?.username}</span>
          <button className="btn btn-secondary" onClick={logout}>Logout</button>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <h3>Agent Configurations</h3>
          <p className="empty">No configurations yet. Create your first agent configuration.</p>
          <Link to="/config/new" className="btn btn-primary" style={{ marginTop: '1rem' }}>
            Create Configuration
          </Link>
        </div>

        <div className="card">
          <h3>Hook Validation</h3>
          <p className="empty">Validate your agent hook schemas against Agent Plugins specification.</p>
          <button className="btn btn-secondary" style={{ marginTop: '1rem' }}>Validate Hooks</button>
        </div>

        <div className="card">
          <h3>Session Analysis</h3>
          <p className="empty">Analyze session transcripts for hook execution patterns.</p>
          <button className="btn btn-secondary" style={{ marginTop: '1rem' }}>Analyze Session</button>
        </div>
      </div>

      <div className="card" style={{ marginTop: '2rem' }}>
        <h3>Recent Activity</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Description</th>
                <th>Status</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><span className="badge badge-info">Config</span></td>
                <td>Created agent config "claude-code"</td>
                <td><span className="badge badge-success">Success</span></td>
                <td>2 hours ago</td>
              </tr>
              <tr>
                <td><span className="badge badge-warning">Validation</span></td>
                <td>Validated hook schema v2.1</td>
                <td><span className="badge badge-success">Passed</span></td>
                <td>5 hours ago</td>
              </tr>
              <tr>
                <td><span className="badge badge-error">Analysis</span></td>
                <td>Session transcript parse failed</td>
                <td><span className="badge badge-error">Failed</span></td>
                <td>1 day ago</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}