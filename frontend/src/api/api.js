// axios wrapper that sends cookies and handles CSRF for Django session auth
import axios from 'axios'

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]+)'))
  return match ? decodeURIComponent(match[2]) : null
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/',
  timeout: 15000,
  withCredentials: true, // include session cookie
})

api.interceptors.request.use(config => {
  const method = (config.method || '').toUpperCase()
  if (!['GET','HEAD','OPTIONS','TRACE'].includes(method)) {
    const csrftoken = getCookie('csrftoken')
    if (csrftoken) {
      config.headers['X-CSRFToken'] = csrftoken
    }
  }
  return config
})

export default api