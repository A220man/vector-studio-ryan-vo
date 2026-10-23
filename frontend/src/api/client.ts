function getEnv(key: string, fallback: string): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (import.meta as any).env?.[key] ?? fallback
}

const API_BASE = getEnv('VITE_API_BASE', '')

function getAccessToken(): string | null {
  return sessionStorage.getItem('access_token')
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    if (response.status === 401) {
      sessionStorage.removeItem('user')
      sessionStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    throw new Error(`API error: ${response.status}`)
  }

  return response.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body: unknown) => request<T>(path, {
    method: 'POST',
    body: JSON.stringify(body),
  }),
  put: <T>(path: string, body: unknown) => request<T>(path, {
    method: 'PUT',
    body: JSON.stringify(body),
  }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

// Auth endpoints
export const authApi = {
  me: () => api.get<{ id: string; username: string; email: string; roles: string[] }>('/auth/me'),
  logout: () => api.post('/auth/logout', {}),
}

// Agent config endpoints
export interface AgentConfig {
  id: number
  name: string
  description: string
  config_data: string
  created_at: string
  updated_at: string
}

export const configApi = {
  list: (params?: { page?: number; limit?: number; search?: string }) => {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', String(params.page))
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.search) query.set('search', params.search)
    return api.get<{ items: AgentConfig[]; total: number; page: number; limit: number }>(
      `/configs?${query.toString()}`
    )
  },
  get: (id: number) => api.get<AgentConfig>(`/configs/${id}`),
  create: (data: { name: string; description: string; config_data: string }) =>
    api.post<AgentConfig>('/configs', data),
  update: (id: number, data: Partial<AgentConfig>) =>
    api.put<AgentConfig>(`/configs/${id}`, data),
  delete: (id: number) => api.delete(`/configs/${id}`),
}