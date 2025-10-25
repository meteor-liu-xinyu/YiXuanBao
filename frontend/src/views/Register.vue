<template>
  <div class="login-container">
    <div class="login-card">
      <h2>用户注册 / Register</h2>

      <form @submit.prevent="onRegister">
        <div style="position:relative;">
          <input
            v-model="username"
            placeholder="用户名 / Username"
            autocomplete="username"
            required
            @blur="onUsernameBlur"
          />
          <span v-if="checkingUsername" class="username-status checking">检测中...</span>
          <span v-else-if="usernameAvailable === true" class="username-status available">可用 ✓</span>
          <span v-else-if="usernameAvailable === false" class="username-status taken">已被占用 ✕</span>
        </div>

        <input v-model="password" type="password" placeholder="密码 / Password" autocomplete="new-password" required />
        <input v-model="confirm" type="password" placeholder="确认密码 / Confirm password" autocomplete="new-password" required />

        <button type="submit" :disabled="loading || usernameAvailable === false">
          {{ loading ? '注册中... / Registering...' : '注册 / Register' }}
        </button>

        <div v-if="error" class="error-tip">{{ error }}</div>
        <div v-if="success" class="success-tip">{{ success }}</div>
      </form>

      <div class="register-link">
        已有账号？<router-link to="/login">去登录 / Login</router-link>
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
const confirm = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const router = useRouter()
const user = useUserStore()

// username availability state:
// null = not checked yet, true = available, false = taken
const usernameAvailable = ref(null)
const checkingUsername = ref(false)

function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return m ? decodeURIComponent(m.pop()) : ''
}

async function ensureCsrf() {
  if (!getCookie('csrftoken')) {
    try {
      await api.get('/accounts/csrf/', { withCredentials: true })
    } catch (e) {
      // ignore — we'll surface errors on register
    }
  }
}

/**
 * Check username availability by calling backend.
 * Expected backend endpoint: GET /accounts/check-username/?username=xxx
 * Response handling tolerant:
 *   - if response.data.exists === true -> username taken
 *   - if response.data.exists === false -> available
 *   - if response.data.available present -> use it (boolean)
 * If the endpoint is not available or request fails, we set usernameAvailable = null (unknown).
 */
async function checkUsernameAvailability(name) {
  if (!name || String(name).trim().length === 0) {
    usernameAvailable.value = null
    return null
  }

  checkingUsername.value = true
  usernameAvailable.value = null
  try {
    const res = await api.get('/accounts/check-username/', {
      params: { username: name },
      withCredentials: true
    })
    const data = res && res.data ? res.data : {}
    // Prefer explicit boolean fields
    if (typeof data.exists === 'boolean') {
      usernameAvailable.value = !data.exists
    } else if (typeof data.available === 'boolean') {
      usernameAvailable.value = !!data.available
    } else if (typeof data.is_taken === 'boolean') {
      usernameAvailable.value = !data.is_taken
    } else {
      // fallback: if server returned 200 and no clear field, assume available
      usernameAvailable.value = true
    }
    return usernameAvailable.value
  } catch (e) {
    // network error or endpoint missing -> do not block registration, but leave as unknown
    usernameAvailable.value = null
    // Optionally, you could set error.value here, but better to surface on submit if needed
    return null
  } finally {
    checkingUsername.value = false
  }
}

async function onUsernameBlur() {
  // perform availability check on blur; ignore empty usernames
  if (!username.value || String(username.value).trim().length === 0) {
    usernameAvailable.value = null
    return
  }
  // we don't await multiple concurrent checks — ensure serial by awaiting
  await checkUsernameAvailability(username.value.trim())
}

async function onRegister() {
  error.value = ''
  success.value = ''

  if (password.value !== confirm.value) {
    error.value = '两次密码不一致 / Passwords do not match'
    return
  }

  // If availability already known and username is taken, block immediately
  if (usernameAvailable.value === false) {
    error.value = '用户名已被占用 / Username already taken'
    return
  }

  // If availability unknown, perform a synchronous check (best-effort)
  if (usernameAvailable.value === null) {
    const avail = await checkUsernameAvailability(username.value.trim())
    if (avail === false) {
      error.value = '用户名已被占用 / Username already taken'
      return
    }
  }

  loading.value = true

  try {
    await ensureCsrf()

    // Prefer using store.register if available so store can centralize behavior.
    // If your store.register returns the axios response, handle it; otherwise fallback to api call.
    let res
    if (typeof user.register === 'function') {
      res = await user.register({ username: username.value.trim(), password: password.value })
    } else {
      res = await api.post('/accounts/register/', {
        username: username.value.trim(),
        password: password.value
      }, { withCredentials: true })
    }

    // Treat 2xx as success
    if (res && (res.status === 200 || res.status === 201 || res.status === 204)) {
      success.value = '注册成功 / Register successful'
      // mark username as taken now that it's registered
      usernameAvailable.value = false
      setTimeout(() => router.replace('/login'), 1000)
    } else {
      error.value = '注册失败，请稍后重试 / Register failed'
    }
  } catch (e) {
    // Prefer backend message if present
    error.value =
      e?.response?.data?.detail ||
      (e?.response?.data && typeof e.response.data === 'string' ? e.response.data : '') ||
      '注册失败 / Register failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 与登录页样式保持一致，视觉统一 */
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

.username-status {
  position: absolute;
  right: 10px;
  top: 10px;
  font-size: 0.9rem;
  padding: 4px 8px;
  border-radius: 6px;
}
.username-status.checking { color:#666; background:#fffbea; border:1px solid #f0e6b8; }
.username-status.available { color:#155724; background:#e6f4ea; border:1px solid #c7ebd1; }
.username-status.taken { color:#7a1c1c; background:#fdecea; border:1px solid #f5c6cb; }

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
.success-tip {
  color: #388e3c;
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