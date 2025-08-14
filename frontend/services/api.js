import axios from 'axios'

/**
 * Central Axios instance.
 * Usage:
 *   import api from '@/services/api'
 *   const { data } = await api.get('/animals/')
 */

const baseURL =
  (import.meta.env && import.meta.env.VITE_API_URL) ||
  (location.port === '5173' ? 'http://127.0.0.1:8001' : window.location.origin)

const api = axios.create({
  baseURL,
  // You can set a timeout if you like:
  // timeout: 20000,
})

// Optional: attach interceptors for consistent error surfacing/logging
api.interceptors.response.use(
  (res) => res,
  (err) => {
    // You can centralize toast/notification here if your app uses one
    // For now, just rethrow so pages handle it.
    return Promise.reject(err)
  }
)

export default api
export { baseURL as apiBase }
