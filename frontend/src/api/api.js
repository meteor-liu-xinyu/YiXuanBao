import axios from 'axios'

// 读取 cookie helper
function getCookie(name) {
  const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return v ? v.pop() : ''
}

// 基础 axios 实例：确保 withCredentials 为 true（跨端口时发送 cookie）
const api = axios.create({
  baseURL: '/api', // 根据项目后端前缀调整，比如 '/api' 或 '/'
  withCredentials: true, // 关键：允许发送并接收跨域 cookie（需要后端 CORS_ALLOW_CREDENTIALS=true）
  headers: {
    Accept: 'application/json',
  },
})

// 在请求拦截器中，为 unsafe 方法添加 X-CSRFToken
api.interceptors.request.use(config => {
  const method = (config.method || '').toLowerCase()
  if (['post', 'put', 'patch', 'delete'].includes(method)) {
    const csrftoken = getCookie('csrftoken') || getCookie('csrf') // 依据后端 Cookie 名
    if (csrftoken) {
      config.headers['X-CSRFToken'] = csrftoken
    }
  }
  return config
}, error => Promise.reject(error))

export default api