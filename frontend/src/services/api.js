import axios from 'axios'
import { useAuthStore } from '../store/authStore'

// On Render: VITE_API_URL = https://your-backend.onrender.com
// Locally:   falls back to /api (proxied by nginx/vite)
const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}`
  : '/api'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach access token from store
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes('/auth/login') &&
      !original.url?.includes('/auth/refresh')
    ) {
      original._retry = true
      const { refreshToken, setTokens, logout } = useAuthStore.getState()
      if (refreshToken) {
        try {
          const res = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token } = res.data
          setTokens(access_token, refresh_token)
          original.headers.Authorization = `Bearer ${access_token}`
          return api(original)
        } catch {
          logout()
        }
      } else {
        logout()
      }
    }
    return Promise.reject(error)
  }
)

// Auth
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  verifyEmail: (token) => api.post('/auth/verify-email', { token }),
  resendVerification: (email) => api.post('/auth/resend-verification', { email }),
  refresh: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  me: (accessToken) =>
    api.get('/auth/me', {
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
    }),
  logout: () => api.post('/auth/logout'),
}

// Papers
export const papersApi = {
  upload: (formData) =>
    api.post('/papers/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: (params) => api.get('/papers', { params }),
  get: (id) => api.get(`/papers/${id}`),
  delete: (id) => api.delete(`/papers/${id}`),
}

// Questions
export const questionsApi = {
  getByPaper: (paperId) => api.get(`/questions/paper/${paperId}`),
}

// Answers
export const answersApi = {
  submit: (data) => api.post('/answers/submit', data),
  chat: (data) => api.post('/answers/chat', data),
  get: (questionId) => api.get(`/answers/question/${questionId}`),
  uploadImage: (questionId, formData) =>
    api.post(`/answers/upload-image/${questionId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

export default api
