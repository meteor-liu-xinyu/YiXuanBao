import axios from 'axios'

// 读取 cookie helper（改为 decodeURIComponent，返回空字符串而不是 undefined）
function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return m ? decodeURIComponent(m.pop()) : ''
}

// 基础 axios 实例：确保 withCredentials 为 true（跨端口时发送 cookie）
const api = axios.create({
  baseURL: '/api', // 前端调用时使用 /api/...，Vite proxy 转发到后端
  withCredentials: true, // 关键：允许发送并接收跨域 cookie（需要后端 CORS_ALLOW_CREDENTIALS=true）
  headers: {
    Accept: 'application/json',
    'X-Requested-With': 'XMLHttpRequest' // 加上这个有助于后端识别 XHR 请求
  },
})

// 在请求拦截器中，为 unsafe 方法添加 X-CSRFToken
api.interceptors.request.use(config => {
  const method = (config.method || '').toLowerCase()
  if (['post', 'put', 'patch', 'delete'].includes(method)) {
    const csrftoken = getCookie('csrftoken') || getCookie('csrf') // 依据后端 Cookie 名
    if (csrftoken) {
      config.headers['X-CSRFToken'] = csrftoken
    } else {
      // 调试信息：如果没有 csrftoken，可能是在登录/注册后没有成功设置 cookie
      // console.debug('No csrftoken cookie found for request', config.url)
    }
  }
  return config
}, error => Promise.reject(error))

export default api