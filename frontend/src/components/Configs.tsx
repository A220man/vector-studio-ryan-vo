import { useState, useEffect } from 'react'
import { configApi, AgentConfig } from '../api/client'
export function Configs() {
  const [configs, setConfigs] = useState<AgentConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingConfig, setEditingConfig] = useState<AgentConfig | null>(null)
  const [formData, setFormData] = useState({ name: '', description: '', config_data: '' })
  const [search, setSearch] = useState('')

  const fetchConfigs = async () => {
    try {
      setLoading(true)
      const params = search ? { search } : {}
      const response = await configApi.list(params)
      setConfigs(response.items)
      setError(null)
    } catch (err) {
      setError('Failed to load configurations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfigs()
  }, [search])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingConfig) {
        await configApi.update(editingConfig.id, formData)
      } else {
        await configApi.create(formData)
      }
      setShowForm(false)
      setEditingConfig(null)
      setFormData({ name: '', description: '', config_data: '' })
      fetchConfigs()
    } catch (err) {
      setError('Failed to save configuration')
    }
  }

  const handleEdit = (config: AgentConfig) => {
    setEditingConfig(config)
    setFormData({ name: config.name, description: config.description, config_data: config.config_data })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this configuration?')) return
    try {
      await configApi.delete(id)
      fetchConfigs()
    } catch (err) {
      setError('Failed to delete configuration')
    }
  }

  const handleNew = () => {
    setEditingConfig(null)
    setFormData({ name: '', description: '', config_data: '{}' })
    setShowForm(true)
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingConfig(null)
    setFormData({ name: '', description: '', config_data: '' })
  }

  if (loading) return <div className="loading">Loading configurations...</div>

  return (
    <div className="configs-page">
      <div className="page-header">
        <h2>Agent Configurations</h2>
        <button className="btn btn-primary" onClick={handleNew}>New Configuration</button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="search-bar" style={{ marginBottom: '1rem' }}>
        <input
          type="text"
          placeholder="Search configurations..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="form-input"
          style={{ maxWidth: '300px' }}
        />
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h3>{editingConfig ? 'Edit' : 'Create'} Configuration</h3>
          <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem', maxWidth: '600px' }}>
            <div className="form-group">
              <label>Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Configuration (JSON)</label>
              <textarea
                value={formData.config_data}
                onChange={(e) => setFormData({ ...formData, config_data: e.target.value })}
                rows={10}
                className="form-input"
                style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
                required
              />
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button type="submit" className="btn btn-primary">{editingConfig ? 'Update' : 'Create'}</button>
              <button type="button" className="btn btn-secondary" onClick={handleCancel}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {configs.length === 0 ? (
          <div className="empty" style={{ padding: '2rem', textAlign: 'center' }}>
            No configurations yet. Click "New Configuration" to create one.
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Created</th>
                  <th>Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {configs.map((config) => (
                  <tr key={config.id}>
                    <td style={{ fontWeight: 500 }}>{config.name}</td>
                    <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {config.description || '-'}
                    </td>
                    <td>{new Date(config.created_at).toLocaleDateString()}</td>
                    <td>{new Date(config.updated_at).toLocaleDateString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }} onClick={() => handleEdit(config)}>Edit</button>
                        <button className="btn btn-danger" style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }} onClick={() => handleDelete(config.id)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}