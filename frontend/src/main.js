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
    // 再尝试拉取当前用户信息（如果有 session 则会返回用户）
    const user = useUserStore()
    await user.fetchUser()
  }
  
  initAuth().finally(() => {
    app.mount('#app')
  })