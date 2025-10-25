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

  // 无条件尝试拉取当前用户信息（如果存在会话/凭证应该返回用户）
  // 使用 try/catch 包裹以防止未捕获的 promise 或阻塞 mount 流程
  try {
    const user = useUserStore()
    await user.fetchUser()
  } catch (e) {
    // 如果拉取失败（401/403/网络错误等），记录但不要中止应用挂载
    console.warn('fetchUser failed while initializing auth', e)
  }
}

initAuth().finally(() => {
  app.mount('#app')
})