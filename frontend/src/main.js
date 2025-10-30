import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import api from '@/api/api'
import { useUserStore } from '@/stores/user'

import '@/assets/styles/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

async function initAuth() {
  try {
    // 请求后端设置 csrftoken cookie（后端 GetCSRFTokenView）
    await api.get('/accounts/csrf/')
  } catch (e) {
    console.warn('csrf fetch failed', e)
  }

  // ⭐⭐⭐ 关键修改：只在有 session cookie 时才尝试恢复用户信息 ⭐⭐⭐
  const hasSession = document.cookie.includes('sessionid=')
  
  if (hasSession) {
    try {
      const user = useUserStore()
      await user.fetchUser()
    } catch (e) {
      // 会话无效或过期，静默处理
      if (e.response?.status === 401 || e.response?.status === 403) {
        console.warn('Session invalid, cleared auth state')
        const user = useUserStore()
        user.clearAuth()
      } else {
        console.warn('fetchUser failed while initializing auth', e)
      }
    }
  }
}

initAuth().finally(() => {
  app.mount('#app')
})