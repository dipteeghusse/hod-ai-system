import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('hod_token') : null
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('hod_token')
      localStorage.removeItem('hod_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ───────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', null, { params: { username: email, password } }),
  loginForm: (email: string, password: string) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  me: () => api.get('/auth/me'),
}

// ── Dashboard ──────────────────────────────────────────────────────────────────

export const dashboardApi = {
  stats: () => api.get('/dashboard/stats'),
}

// ── Tasks ──────────────────────────────────────────────────────────────────────

export const tasksApi = {
  list: (params?: { status?: string; priority?: string; assigned_to?: number }) =>
    api.get('/tasks', { params }),
  create: (data: any) => api.post('/tasks', data),
  update: (id: number, data: any) => api.patch(`/tasks/${id}`, data),
  delete: (id: number) => api.delete(`/tasks/${id}`),
}

// ── Meetings ───────────────────────────────────────────────────────────────────

export const meetingsApi = {
  list: () => api.get('/meetings'),
  create: (data: any) => api.post('/meetings', data),
  generateAgenda: (id: number) => api.post(`/meetings/${id}/generate-agenda`),
}

// ── Faculty ────────────────────────────────────────────────────────────────────

export const facultyApi = {
  list: () => api.get('/faculty'),
}

// ── AI Agent ───────────────────────────────────────────────────────────────────

export const agentApi = {
  chat: (query: string, agentType?: string, context?: any, sessionId?: string) =>
    api.post('/agent/chat', {
      query,
      agent_type: agentType || 'hod_assistant',
      context: context || {},
      session_id: sessionId,
    }),
  history: () => api.get('/agent/history'),
}

// ── Reports ────────────────────────────────────────────────────────────────────

export const reportsApi = {
  generate: (reportType: string, format?: string) =>
    api.post('/reports/generate', { report_type: reportType, format: format || 'text' }),
}
