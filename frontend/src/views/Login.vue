<template>
  <div class="login-container">
    <div class="login-card">
      <h2>用户登录</h2>
      <form @submit.prevent="onLogin">
        <input v-model="username" placeholder="用户名" autocomplete="username" required />
        <input v-model="password" type="password" placeholder="密码" autocomplete="current-password" required />
        <button type="submit" :disabled="loading">{{ loading ? '登录中... / Logging in...' : '登录 / Login' }}</button>
        <div v-if="error" class="error-tip">{{ error }}</div>
      </form>
      <div class="register-link">
        还没有账号？<router-link to="/register">马上注册 / Register</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/api'
import { useUserStore } from '@/stores/user'

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const router = useRouter()
const user = useUserStore()

// helper 读取 cookie
function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return m ? decodeURIComponent(m.pop()) : ''
}

async function ensureCsrf() {
  // 如果没有 csrftoken，主动请求后端设置（后端 /accounts/csrf/）
  if (!getCookie('csrftoken')) {
    try {
      await api.get('/accounts/csrf/', { withCredentials: true })
    } catch (e) {
      // 忽略错误（后续登录会给出提示）
    }
  }
}

async function onLogin() {
  error.value = ''
  loading.value = true

  try {
    // 确保浏览器有 csrftoken cookie（若后端需要 CSRF）
    await ensureCsrf()

    // 调用 store.login 统一处理（store 会带凭证并读取 csrftoken）
    const ok = await user.login({ username: username.value, password: password.value })

    if (ok) {
      // 登录成功后跳回首页（或上一次页面）
      router.replace('/')
    } else {
      error.value = '用户名或密码错误 / Wrong username or password'
    }
  } catch (e) {
    // 更友好的错误提示
    error.value = e?.response?.data?.detail || '登录失败，请稍后重试 / Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(120deg, #f5f7fa 0%, #c3cfe2 100%);
}
.login-card {
  background: #fff;
  padding: 42px 32px 32px;
  border-radius: 14px;
  box-shadow: 0 4px 32px rgba(40, 60, 120, 0.15);
  width: 420px;
  max-width: 94vw;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 22px;
  font-size: 1.6rem;
  color: #3b4a7a;
}
.login-card input {
  display: block;
  width: 100%;
  margin-bottom: 18px;
  border: 1.5px solid #b6c2e3;
  border-radius: 7px;
  padding: 12px 14px;
  font-size: 1.08rem;
  outline: none;
  transition: border 0.2s, box-shadow 0.2s;
}
.login-card input:focus {
  border: 1.5px solid #6a85e6;
  box-shadow: 0 4px 18px rgba(106,133,230,0.08);
}
.login-card button {
  width: 100%;
  padding: 12px;
  background: linear-gradient(90deg, #6a85e6 0%, #43cea2 100%);
  color: #fff;
  font-size: 1.13rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  box-shadow: 0 6px 20px rgba(106,133,230,0.12);
  cursor: pointer;
  transition: transform 0.12s ease, opacity 0.12s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.login-card button:active:not(:disabled) {
  transform: translateY(1px);
}
.login-card button:disabled {
  background: #cfd8ec;
  cursor: not-allowed;
  opacity: 0.9;
}
.error-tip {
  color: #d32f2f;
  text-align: center;
  margin-top: 6px;
  font-size: 0.98rem;
  letter-spacing: 0.5px;
}
.register-link {
  text-align: center;
  margin-top: 6px;
  color: #3b4a7a;
  font-size: 0.98rem;
}
.register-link a {
  color: #6a85e6;
  text-decoration: underline;
  margin-left: 4px;
  transition: color 0.2s;
}
.register-link a:hover {
  color: #43cea2;
}

/* 手机端微调 */
@media (max-width: 480px) {
  .login-card { width: 92vw; padding: 28px 18px; }
  .login-card button { height: 46px; font-size: 1rem; }
}
</style>