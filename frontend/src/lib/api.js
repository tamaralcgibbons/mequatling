// src/lib/api.ts
import axios from 'axios'

const apiBase =
  import.meta.env?.VITE_API_URL ||
  (location.protocol === 'https:' 
    ? `${location.origin}`              // same origin in prod if you proxy on server
    : (location.port === '5173'
        ? 'http://127.0.0.1:8001'       // dev backend
        : window.location.origin))

const api = axios.create({
  baseURL: apiBase,
  timeout: 15000,
  withCredentials: false,               // set true only if you use cookies
  headers: { 'Content-Type': 'application/json' },
})

// Helpful: normalize network errors
api.interceptors.response.use(
  (r) => r,
  (err) => {
    // Axios uses "Network Error" for CORS/connection issues
    if (!err.response) err.message = 'Network Error'
    return Promise.reject(err)
  }
)

export default api
